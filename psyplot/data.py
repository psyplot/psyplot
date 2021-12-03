"""Data management core routines of psyplot."""

# Disclaimer
# ----------
#
# Copyright (C) 2021 Helmholtz-Zentrum Hereon
# Copyright (C) 2020-2021 Helmholtz-Zentrum Geesthacht
# Copyright (C) 2016-2021 University of Lausanne
#
# This file is part of psyplot and is released under the GNU LGPL-3.O license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3.0 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU LGPL-3.0 license for more details.
#
# You should have received a copy of the GNU LGPL-3.0 license
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import division
import os
import os.path as osp
import inspect
from threading import Thread
from functools import partial
from glob import glob
from importlib import import_module
import re
import six
from collections import defaultdict
from itertools import chain, product, repeat, starmap, count, cycle, islice
import xarray as xr
from xarray.core.utils import NDArrayMixin
from xarray.core.formatting import first_n_items, format_item

import xarray.backends.api as xarray_api
from pandas import to_datetime
import numpy as np
import datetime as dt
import logging
from psyplot.config.rcsetup import rcParams, safe_list
from psyplot.docstring import dedent, docstrings
from psyplot.compat.pycompat import (
    zip, map, isstring, OrderedDict, filter, range, getcwd,
    Queue)
from psyplot.warning import PsyPlotRuntimeWarning
from warnings import warn
import psyplot.utils as utils

try:
    import dask
    with_dask = True
except ImportError:
    with_dask = False

try:
    import xarray.backends.plugins as xr_plugins
except ImportError:
    xr_plugins = None  # type: ignore


# No data variable. This is used for filtering if an attribute could not have
# been accessed
_NODATA = object


VARIABLELABEL = 'variable'


logger = logging.getLogger(__name__)


_ds_counter = count(1)

xr_version = tuple(map(int, xr.__version__.split('.')[:2]))


def _no_auto_update_getter(self):
    """:class:`bool`. Boolean controlling whether the :meth:`start_update`
    method is automatically called by the :meth:`update` method


    Examples
    --------
    You can disable the automatic update via

        >>> with data.no_auto_update:
        ...     data.update(time=1)
        ...     data.start_update()

    To permanently disable the automatic update, simply set

        >>> data.no_auto_update = True
        >>> data.update(time=1)
        >>> data.no_auto_update = False  # reenable automatical update"""
    if getattr(self, '_no_auto_update', None) is not None:
        return self._no_auto_update
    else:
        self._no_auto_update = utils._TempBool()
    return self._no_auto_update


def _infer_interval_breaks(coord):
    """
    >>> _infer_interval_breaks(np.arange(5))
    array([-0.5,  0.5,  1.5,  2.5,  3.5,  4.5])

    Taken from xarray.plotting.plot module
    """
    coord = np.asarray(coord)
    deltas = 0.5 * (coord[1:] - coord[:-1])
    first = coord[0] - deltas[0]
    last = coord[-1] + deltas[-1]
    return np.r_[[first], coord[:-1] + deltas, [last]]


def _get_variable_names(arr):
    """Return the variable names of an array"""
    if VARIABLELABEL in arr.dims:
        return arr.coords[VARIABLELABEL].tolist()
    else:
        return arr.name


def _get_dims(arr):
    """Return all dimensions but the :attr:`VARIABLELABEL`"""
    return tuple(filter(lambda d: d != VARIABLELABEL, arr.dims))


def _open_store(store_mod, store_cls, fname):
    try:
        return getattr(import_module(store_mod), store_cls).open(fname)
    except AttributeError:
        return getattr(import_module(store_mod), store_cls)(fname)


def _fix_times(dims):
    # xarray 0.16 fails with pandas 1.1.0 for datetime, see
    # https://github.com/pydata/xarray/issues/4283
    for key, val in dims.items():
        if np.issubdtype(np.asarray(val).dtype, np.datetime64):
            dims[key] = to_datetime([val])[0]


@docstrings.get_sections(base='setup_coords')
@dedent
def setup_coords(arr_names=None, sort=[], dims={}, **kwargs):
    """
    Sets up the arr_names dictionary for the plot

    Parameters
    ----------
    arr_names: string, list of strings or dictionary
        Set the unique array names of the resulting arrays and (optionally)
        dimensions.

        - if string: same as list of strings (see below). Strings may
          include {0} which will be replaced by a counter.
        - list of strings: those will be used for the array names. The final
          number of dictionaries in the return depend in this case on the
          `dims` and ``**furtherdims``
        - dictionary:
          Then nothing happens and an :class:`OrderedDict` version of
          `arr_names` is returned.
    sort: list of strings
        This parameter defines how the dictionaries are ordered. It has no
        effect if `arr_names` is a dictionary (use a
        :class:`~collections.OrderedDict` for that). It can be a list of
        dimension strings matching to the dimensions in `dims` for the
        variable.
    dims: dict
        Keys must be variable names of dimensions (e.g. time, level, lat or
        lon) or 'name' for the variable name you want to choose.
        Values must be values of that dimension or iterables of the values
        (e.g. lists). Note that strings will be put into a list.
        For example dims = {'name': 't2m', 'time': 0} will result in one plot
        for the first time step, whereas dims = {'name': 't2m', 'time': [0, 1]}
        will result in two plots, one for the first (time == 0) and one for the
        second (time == 1) time step.
    ``**kwargs``
        The same as `dims` (those will update what is specified in `dims`)

    Returns
    -------
    ~collections.OrderedDict
        A mapping from the keys in `arr_names` and to dictionaries. Each
        dictionary corresponds defines the coordinates of one data array to
        load"""
    try:
        return OrderedDict(arr_names)
    except (ValueError, TypeError):
        # ValueError for cyordereddict, TypeError for collections.OrderedDict
        pass
    if arr_names is None:
        arr_names = repeat('arr{0}')
    elif isstring(arr_names):
        arr_names = repeat(arr_names)
    dims = OrderedDict(dims)
    for key, val in six.iteritems(kwargs):
        dims.setdefault(key, val)
    sorted_dims = OrderedDict()
    if sort:
        for key in sort:
            sorted_dims[key] = dims.pop(key)
        for key, val in six.iteritems(dims):
            sorted_dims[key] = val
    else:
        # make sure, it is first sorted for the variable names
        if 'name' in dims:
            sorted_dims['name'] = None
        for key, val in sorted(dims.items()):
            sorted_dims[key] = val
        for key, val in six.iteritems(kwargs):
            sorted_dims.setdefault(key, val)
    for key, val in six.iteritems(sorted_dims):
        sorted_dims[key] = iter(safe_list(val))
    return OrderedDict([
        (arr_name.format(i), dict(zip(sorted_dims.keys(), dim_tuple)))
        for i, (arr_name, dim_tuple) in enumerate(zip(
            arr_names, product(
                *map(list, sorted_dims.values()))))])


def to_slice(arr):
    """Test whether `arr` is an integer array that can be replaced by a slice

    Parameters
    ----------
    arr: numpy.array
        Numpy integer array

    Returns
    -------
    slice or None
        If `arr` could be converted to an array, this is returned, otherwise
        `None` is returned

    See Also
    --------
    get_index_from_coord"""
    if isinstance(arr, slice):
        return arr
    if len(arr) == 1:
        return slice(arr[0], arr[0] + 1)
    step = np.unique(arr[1:] - arr[:-1])
    if len(step) == 1:
        return slice(arr[0], arr[-1] + step[0], step[0])


def get_index_from_coord(coord, base_index):
    """Function to return the coordinate as integer, integer array or slice

    If `coord` is zero-dimensional, the corresponding integer in `base_index`
    will be supplied. Otherwise it is first tried to return a slice, if that
    does not work an integer array with the corresponding indices is returned.

    Parameters
    ----------
    coord: xarray.Coordinate or xarray.Variable
        Coordinate to convert
    base_index: pandas.Index
        The base index from which the `coord` was extracted

    Returns
    -------
    int, array of ints or slice
        The indexer that can be used to access the `coord` in the
        `base_index`
    """
    try:
        values = coord.values
    except AttributeError:
        values = coord
    if values.ndim == 0:
        return base_index.get_loc(values[()])
    if len(values) == len(base_index) and (values == base_index).all():
        return slice(None)
    values = np.array(list(map(lambda i: base_index.get_loc(i), values)))
    return to_slice(values) or values


#: mapping that translates datetime format strings to regex patterns
t_patterns = {
        '%Y': '[0-9]{4}',
        '%m': '[0-9]{1,2}',
        '%d': '[0-9]{1,2}',
        '%H': '[0-9]{1,2}',
        '%M': '[0-9]{1,2}',
        '%S': '[0-9]{1,2}',
    }


@docstrings.get_sections(base='get_tdata')
@dedent
def get_tdata(t_format, files):
    """
    Get the time information from file names

    Parameters
    ----------
    t_format: str
        The string that can be used to get the time information in the files.
        Any numeric datetime format string (e.g. %Y, %m, %H) can be used, but
        not non-numeric strings like %b, etc. See [1]_ for the datetime format
        strings
    files: list of str
        The that contain the time informations

    Returns
    -------
    pandas.Index
        The time coordinate
    list of str
        The file names as they are sorten in the returned index

    References
    ----------
    .. [1] https://docs.python.org/2/library/datetime.html"""
    def median(arr):
        return arr.min() + (arr.max() - arr.min())/2
    import re
    from pandas import Index
    t_pattern = t_format
    for fmt, patt in t_patterns.items():
        t_pattern = t_pattern.replace(fmt, patt)
    t_pattern = re.compile(t_pattern)
    time = list(range(len(files)))
    for i, f in enumerate(files):
        time[i] = median(np.array(list(map(
            lambda s: np.datetime64(dt.datetime.strptime(s, t_format)),
            t_pattern.findall(f)))))
    ind = np.argsort(time)  # sort according to time
    files = np.array(files)[ind]
    time = np.array(time)[ind]
    return to_datetime(Index(time, name='time')), files


docstrings.get_sections(xr.Dataset.to_netcdf.__doc__,
                        'xarray.Dataset.to_netcdf')


@docstrings.dedent
def to_netcdf(ds, *args, **kwargs):
    """
    Store the given dataset as a netCDF file

    This functions works essentially the same as the usual
    :meth:`xarray.Dataset.to_netcdf` method but can also encode absolute time
    units

    Parameters
    ----------
    ds: xarray.Dataset
        The dataset to store
    %(xarray.Dataset.to_netcdf.parameters)s
    """
    to_update = {}
    for v, obj in six.iteritems(ds.variables):
        units = obj.attrs.get('units', obj.encoding.get('units', None))
        if units == 'day as %Y%m%d.%f' and np.issubdtype(
                obj.dtype, np.datetime64):
            to_update[v] = xr.Variable(
                obj.dims, AbsoluteTimeEncoder(obj), attrs=obj.attrs.copy(),
                encoding=obj.encoding)
            to_update[v].attrs['units'] = units
    if to_update:
        ds = ds.copy()
        ds.update(to_update)
    return xarray_api.to_netcdf(ds, *args, **kwargs)


def _get_fname_netCDF4(store):
    """Try to get the file name from the NetCDF4DataStore store"""
    return getattr(store, '_filename', None)


def _get_fname_scipy(store):
    """Try to get the file name from the ScipyDataStore store"""
    try:
        return store.ds.filename
    except AttributeError:
        return None


def _get_fname_nio(store):
    """Try to get the file name from the NioDataStore store"""
    try:
        f = store.ds.file
    except AttributeError:
        return None
    try:
        return f.path
    except AttributeError:
        return None


class Signal(object):
    """Signal to connect functions to a specific event

    This class behaves almost similar to PyQt's
    :class:`PyQt4.QtCore.pyqtBoundSignal`
    """

    instance = None
    owner = None

    def __init__(self, name=None, cls_signal=False):
        self.name = name
        self.cls_signal = cls_signal
        self._connections = []

    def connect(self, func):
        if func not in self._connections:
            self._connections.append(func)

    def emit(self, *args, **kwargs):
        if (not getattr(self.owner, 'block_signals', False) and
                not getattr(self.instance, 'block_signals', False)):
            logger.debug('Emitting signal %s', self.name)
            for func in self._connections[:]:
                logger.debug('Calling %s', func)
                func(*args, **kwargs)

    def disconnect(self, func=None):
        """Disconnect a function call to the signal. If None, all connections
        are disconnected"""
        if func is None:
            self._connections = []
        else:
            self._connections.remove(func)

    def __get__(self, instance, owner):
        self.owner = owner
        if instance is None or self.cls_signal:
            return self
        ret = getattr(instance, self.name, None)
        if ret is None:
            setattr(instance, self.name, Signal(self.name))
            ret = getattr(instance, self.name, None)
            ret.instance = instance
        return ret


#: functions to use to extract the file name from a data store
get_fname_funcs = [_get_fname_netCDF4, _get_fname_scipy, _get_fname_nio]


@docstrings.get_sections(base='get_filename_ds')
@docstrings.dedent
def get_filename_ds(ds, dump=True, paths=None, **kwargs):
    """
    Return the filename of the corresponding to a dataset

    This method returns the path to the `ds` or saves the dataset
    if there exists no filename

    Parameters
    ----------
    ds: xarray.Dataset
        The dataset you want the path information for
    dump: bool
        If True and the dataset has not been dumped so far, it is dumped to a
        temporary file or the one generated by `paths` is used
    paths: iterable or True
        An iterator over filenames to use if a dataset has no filename.
        If paths is ``True``, an iterator over temporary files will be
        created without raising a warning

    Other Parameters
    ----------------
    ``**kwargs``
        Any other keyword for the :func:`to_netcdf` function
    %(xarray.Dataset.to_netcdf.parameters)s

    Returns
    -------
    str or None
        None, if the dataset has not yet been dumped to the harddisk and
        `dump` is False, otherwise the complete the path to the input
        file
    str
        The module of the :class:`xarray.backends.common.AbstractDataStore`
        instance that is used to hold the data
    str
        The class name of the
        :class:`xarray.backends.common.AbstractDataStore` instance that is
        used to open the data
    """
    from tempfile import NamedTemporaryFile

    # if already specified, return that filename
    if ds.psy._filename is not None:
        return tuple([ds.psy._filename] + list(ds.psy.data_store))

    def dump_nc():
        # make sure that the data store is not closed by providing a
        # write argument
        if xr_version < (0, 11):
            kwargs.setdefault('writer', xarray_api.ArrayWriter())
            store = to_netcdf(ds, fname, **kwargs)
        else:
            # `writer` parameter was removed by
            # https://github.com/pydata/xarray/pull/2261
            kwargs.setdefault('multifile', True)
            store = to_netcdf(ds, fname, **kwargs)[1]
        store_mod = store.__module__
        store_cls = store.__class__.__name__
        ds._file_obj = store
        return store_mod, store_cls

    def tmp_it():
        while True:
            yield NamedTemporaryFile(suffix='.nc').name

    def _legacy_get_filename_ds(ds):
        # try to get the filename from the data store of the obj
        #
        # Outdated possibility since the backend plugin methodology of
        # xarray 0.18
        if store_mod is not None:
            store = ds._file_obj
            # try several engines
            if hasattr(store, 'file_objs'):
                fname = []
                store_mod = []
                store_cls = []
                for obj in store.file_objs:  # mfdataset
                    _fname = None
                    for func in get_fname_funcs:
                        if _fname is None:
                            _fname = func(obj)
                            if _fname is not None:
                                fname.append(_fname)
                                store_mod.append(obj.__module__)
                                store_cls.append(obj.__class__.__name__)
                fname = tuple(fname)
                store_mod = tuple(store_mod)
                store_cls = tuple(store_cls)
            else:
                for func in get_fname_funcs:
                    fname = func(store)
                    if fname is not None:
                        break

        return fname, store_mod, store_cls

    fname = None
    if paths is True or (dump and paths is None):
        paths = tmp_it()
    elif paths is not None:
        if isstring(paths):
            paths = iter([paths])
        else:
            paths = iter(paths)
    store_mod, store_cls = ds.psy.data_store
    if xr_plugins is None:
        fname, store_mod, store_cls = _legacy_get_filename_ds(ds)
    elif "source" in ds.encoding:
        fname = ds.encoding["source"]
        store_mod = None
        store_cls = None


    # check if paths is provided and if yes, save the file
    if fname is None and paths is not None:
        fname = next(paths, None)
        if dump and fname is not None:
            store_mod, store_cls = dump_nc()

    ds.psy.filename = fname
    ds.psy.data_store = (store_mod, store_cls)

    return fname, store_mod, store_cls


class CFDecoder(object):
    """
    Class that interpretes the coordinates and attributes accordings to
    cf-conventions"""

    _registry = []

    @property
    def logger(self):
        """:class:`logging.Logger` of this instance"""
        try:
            return self._logger
        except AttributeError:
            name = '%s.%s' % (self.__module__, self.__class__.__name__)
            self._logger = logging.getLogger(name)
            self.logger.debug('Initializing...')
            return self._logger

    @logger.setter
    def logger(self, value):
        self._logger = value

    def __init__(self, ds=None, x=None, y=None, z=None, t=None):
        self.ds = ds
        self.x = rcParams['decoder.x'].copy() if x is None else set(x)
        self.y = rcParams['decoder.y'].copy() if y is None else set(y)
        self.z = rcParams['decoder.z'].copy() if z is None else set(z)
        self.t = rcParams['decoder.t'].copy() if t is None else set(t)

    @staticmethod
    def register_decoder(decoder_class, pos=0):
        """Register a new decoder

        This function registeres a decoder class to use

        Parameters
        ----------
        decoder_class: type
            The class inherited from the :class:`CFDecoder`
        pos: int
            The position where to register the decoder (by default: the first
            position"""
        CFDecoder._registry.insert(pos, decoder_class)

    @classmethod
    @docstrings.get_sections(base='CFDecoder.can_decode', sections=['Parameters',
                                                                'Returns'])
    def can_decode(cls, ds, var):
        """
        Class method to determine whether the object can be decoded by this
        decoder class.

        Parameters
        ----------
        ds: xarray.Dataset
            The dataset that contains the given `var`
        var: xarray.Variable or xarray.DataArray
            The array to decode

        Returns
        -------
        bool
            True if the decoder can decode the given array `var`. Otherwise
            False

        Notes
        -----
        The default implementation returns True for any argument. Subclass this
        method to be specific on what type of data your decoder can decode
        """
        return True

    @classmethod
    @docstrings.dedent
    def get_decoder(cls, ds, var, *args, **kwargs):
        """
        Class method to get the right decoder class that can decode the
        given dataset and variable

        Parameters
        ----------
        %(CFDecoder.can_decode.parameters)s

        Returns
        -------
        CFDecoder
            The decoder for the given dataset that can decode the variable
            `var`"""
        for decoder_cls in cls._registry:
            if decoder_cls.can_decode(ds, var):
                return decoder_cls(ds, *args, **kwargs)
        return CFDecoder(ds, *args, **kwargs)

    @staticmethod
    @docstrings.get_sections(base='CFDecoder.decode_coords', sections=[
        'Parameters', 'Returns'])
    def decode_coords(ds, gridfile=None):
        """
        Sets the coordinates and bounds in a dataset

        This static method sets those coordinates and bounds that are marked
        marked in the netCDF attributes as coordinates in :attr:`ds` (without
        deleting them from the variable attributes because this information is
        necessary for visualizing the data correctly)

        Parameters
        ----------
        ds: xarray.Dataset
            The dataset to decode
        gridfile: str
            The path to a separate grid file or a xarray.Dataset instance which
            may store the coordinates used in `ds`

        Returns
        -------
        xarray.Dataset
            `ds` with additional coordinates"""
        def add_attrs(obj):
            if 'coordinates' in obj.attrs:
                extra_coords.update(obj.attrs['coordinates'].split())
                obj.encoding['coordinates'] = obj.attrs.pop('coordinates')
            if 'grid_mapping' in obj.attrs:
                extra_coords.add(obj.attrs['grid_mapping'])
            if 'bounds' in obj.attrs:
                extra_coords.add(obj.attrs['bounds'])
        if gridfile is not None and not isinstance(gridfile, xr.Dataset):
            gridfile = open_dataset(gridfile)
        extra_coords = set(ds.coords)
        for k, v in six.iteritems(ds.variables):
            add_attrs(v)
        add_attrs(ds)
        if gridfile is not None:
            ds.update({k: v for k, v in six.iteritems(gridfile.variables)
                       if k in extra_coords})
        if xr_version < (0, 11):
            ds.set_coords(extra_coords.intersection(ds.variables),
                          inplace=True)
        else:
            ds._coord_names.update(extra_coords.intersection(ds.variables))
        return ds

    @docstrings.get_sections(base='CFDecoder.is_unstructured', sections=[
        'Parameters', 'Returns'])

    @docstrings.get_sections(base=
        'CFDecoder.get_cell_node_coord',
        sections=['Parameters', 'Returns'])
    @dedent
    def get_cell_node_coord(self, var, coords=None, axis='x', nans=None):
        """
        Checks whether the bounds in the variable attribute are triangular

        Parameters
        ----------
        var: xarray.Variable or xarray.DataArray
            The variable to check
        coords: dict
            Coordinates to use. If None, the coordinates of the dataset in the
            :attr:`ds` attribute are used.
        axis: {'x', 'y'}
            The spatial axis to check
        nans: {None, 'skip', 'only'}
            Determines whether values with nan shall be left (None), skipped
            (``'skip'``) or shall be the only one returned (``'only'``)

        Returns
        -------
        xarray.DataArray or None
            the bounds corrdinate (if existent)"""
        if coords is None:
            coords = self.ds.coords
        axis = axis.lower()
        get_coord = self.get_x if axis == 'x' else self.get_y
        coord = get_coord(var, coords=coords)
        if coord is not None:
            bounds = self._get_coord_cell_node_coord(coord, coords, nans,
                                                     var=var)
            if bounds is None:
                bounds = self.get_plotbounds(coord)
                if bounds.ndim == 1:
                    dim0 = coord.dims[-1]
                    bounds = xr.DataArray(
                        np.dstack([bounds[:-1], bounds[1:]])[0],
                        dims=(dim0, '_bnds'),  attrs=coord.attrs.copy(),
                        name=coord.name + '_bnds')
                elif bounds.ndim == 2:
                    warn("2D bounds are not yet sufficiently tested!")
                    bounds = xr.DataArray(
                        np.dstack([bounds[1:, 1:].ravel(),
                                   bounds[1:, :-1].ravel(),
                                   bounds[:-1, :-1].ravel(),
                                   bounds[:-1, 1:].ravel()])[0],
                        dims=(''.join(var.dims[-2:]), '_bnds'),
                        attrs=coord.attrs.copy(),
                        name=coord.name + '_bnds')
                else:
                    raise NotImplementedError(
                        "More than 2D-bounds are not supported")
            if bounds is not None and bounds.shape[-1] == 2:
                # normal CF-Conventions for rectangular grids
                arr = bounds.values
                if axis == 'y':
                    stacked = np.c_[arr[..., :1], arr[..., :1],
                                    arr[..., 1:], arr[..., 1:]]
                    if bounds.ndim == 2:
                        stacked = np.repeat(
                            stacked.reshape((-1, 4)),
                            len(self.get_x(var, coords)), axis=0)
                    else:
                        stacked = stacked.reshape((-1, 4))
                else:
                    stacked = np.c_[arr, arr[..., ::-1]]
                    if bounds.ndim == 2:
                        stacked = np.tile(
                            stacked, (len(self.get_y(var, coords)), 1))
                    else:
                        stacked = stacked.reshape((-1, 4))
                bounds = xr.DataArray(
                    stacked,
                    dims=('cell', bounds.dims[1]), name=bounds.name,
                    attrs=bounds.attrs)

            return bounds
        return None

    docstrings.delete_params('CFDecoder.get_cell_node_coord.parameters',
                             'var', 'axis')

    @docstrings.dedent
    def _get_coord_cell_node_coord(self, coord, coords=None, nans=None,
                                   var=None):
        """
        Get the boundaries of an unstructed coordinate

        Parameters
        ----------
        coord: xr.Variable
            The coordinate whose bounds should be returned
        %(CFDecoder.get_cell_node_coord.parameters.no_var|axis)s

        Returns
        -------
        %(CFDecoder.get_cell_node_coord.returns)s
        """
        bounds = coord.attrs.get('bounds')
        if bounds is not None:
            bounds = self.ds.coords.get(bounds)
        if bounds is not None:
            if coords is not None:
                bounds = bounds.sel(**{
                    key: coords[key]
                    for key in set(coords).intersection(bounds.dims)})
            if nans is not None and var is None:
                raise ValueError("Need the variable to deal with NaN!")
            elif nans is None:
                pass
            elif nans == 'skip':
                dims = [dim for dim in set(var.dims) - set(bounds.dims)]
                mask = var.notnull().all(list(dims)) if dims else var.notnull()
                try:
                    bounds = bounds[mask.values]
                except IndexError:  # 3D bounds
                    bounds = bounds.where(mask)
            elif nans == 'only':
                dims = [dim for dim in set(var.dims) - set(bounds.dims)]
                mask = var.isnull().all(list(dims)) if dims else var.isnull()
                bounds = bounds[mask.values]
            else:
                raise ValueError(
                    "`nans` must be either None, 'skip', or 'only'! "
                    "Not {0}!".format(str(nans)))
            return bounds

    @docstrings.get_sections(base='CFDecoder._check_unstructured_bounds', sections=[
        'Parameters', 'Returns'])
    @docstrings.dedent
    def _check_unstructured_bounds(self, var, coords=None, axis='x', nans=None):
        """
        Checks whether the bounds in the variable attribute are triangular

        Parameters
        ----------
        %(CFDecoder.get_cell_node_coord.parameters)s

        Returns
        -------
        bool or None
            True, if unstructered, None if it could not be determined
        xarray.Coordinate or None
            the bounds corrdinate (if existent)"""
        # !!! WILL BE REMOVED IN THE NEAR FUTURE! !!!
        bounds = self.get_cell_node_coord(var, coords, axis=axis, nans=nans)
        if bounds is not None:
            return bounds.shape[-1] == 3, bounds
        else:
            return None, None

    @docstrings.dedent
    def is_unstructured(self, var):
        """
        Test if a variable is on an unstructered grid

        Parameters
        ----------
        %(CFDecoder.is_unstructured.parameters)s

        Returns
        -------
        %(CFDecoder.is_unstructured.returns)s

        Notes
        -----
        Currently this is the same as :meth:`is_unstructured` method, but may
        change in the future to support hexagonal grids"""
        if str(var.attrs.get('grid_type')) == 'unstructured':
            return True
        xcoord = self.get_x(var)
        if xcoord is not None:
            bounds = self._get_coord_cell_node_coord(xcoord)
            if bounds is not None and bounds.ndim == 2 and bounds.shape[-1] > 2:
                return True

    @docstrings.dedent
    def is_circumpolar(self, var):
        """
        Test if a variable is on a circumpolar grid

        Parameters
        ----------
        %(CFDecoder.is_unstructured.parameters)s

        Returns
        -------
        %(CFDecoder.is_unstructured.returns)s"""
        xcoord = self.get_x(var)
        return xcoord is not None and xcoord.ndim == 2

    def get_variable_by_axis(self, var, axis, coords=None):
        """Return the coordinate matching the specified axis

        This method uses to ``'axis'`` attribute in coordinates to return the
        corresponding coordinate of the given variable

        Possible types
        --------------
        var: xarray.Variable
            The variable to get the dimension for
        axis: {'x', 'y', 'z', 't'}
            The axis string that identifies the dimension
        coords: dict
            Coordinates to use. If None, the coordinates of the dataset in the
            :attr:`ds` attribute are used.

        Returns
        -------
        xarray.Coordinate or None
            The coordinate for `var` that matches the given `axis` or None if
            no coordinate with the right `axis` could be found.

        Notes
        -----
        This is a rather low-level function that only interpretes the
        CFConvention. It is used by the :meth:`get_x`,
        :meth:`get_y`, :meth:`get_z` and :meth:`get_t` methods

        Warning
        -------
        If None of the coordinates have an ``'axis'`` attribute, we use the
        ``'coordinate'`` attribute of `var` (if existent).
        Since however the CF Conventions do not determine the order on how
        the coordinates shall be saved, we try to use a pattern matching
        for latitude (``'lat'``) and longitude (``lon'``). If this patterns
        do not match, we interpret the  coordinates such that x: -1, y: -2,
        z: -3. This is all not very safe for awkward dimension names,
        but works for most cases. If you want to be a hundred percent sure,
        use the :attr:`x`, :attr:`y`, :attr:`z` and :attr:`t` attribute.

        See Also
        --------
        get_x, get_y, get_z, get_t"""

        def get_coord(cname, raise_error=True):
            try:
                return coords[cname]
            except KeyError:
                if cname not in self.ds.coords:
                    if raise_error:
                        raise
                    return None
                ret = self.ds.coords[cname]
                try:
                    idims = var.psy.idims
                except AttributeError:  # got xarray.Variable
                    idims = {}
                return ret.isel(**{d: sl for d, sl in idims.items()
                                   if d in ret.dims})

        axis = axis.lower()
        if axis not in list('xyzt'):
            raise ValueError("Axis must be one of X, Y, Z, T, not {0}".format(
                axis))
        # we first check for the dimensions and then for the coordinates
        # attribute
        coords = coords or self.ds.coords
        coord_names = var.attrs.get('coordinates', var.encoding.get(
            'coordinates', '')).split()
        if not coord_names:
            return
        ret = []
        matched = []
        for coord in map(lambda dim: coords[dim], filter(
                lambda dim: dim in coords, chain(
                    coord_names, var.dims))):
            # check for the axis attribute or whether the coordinate is in the
            # list of possible coordinate names
            if coord.name not in (c.name for c in ret):
                if coord.name in getattr(self, axis):
                    matched.append(coord)
                elif coord.attrs.get('axis', '').lower() == axis:
                    ret.append(coord)
        if matched:
            if len(set([c.name for c in matched])) > 1:
                warn("Found multiple matches for %s coordinate in the "
                     "coordinates: %s. I use %s" % (
                         axis, ', '.join([c.name for c in matched]),
                         matched[0].name),
                     PsyPlotRuntimeWarning)
            return matched[0]
        elif ret:
            return None if len(ret) > 1 else ret[0]
        # If the coordinates attribute is specified but the coordinate
        # variables themselves have no 'axis' attribute, we interpret the
        # coordinates such that x: -1, y: -2, z: -3
        # Since however the CF Conventions do not determine the order on how
        # the coordinates shall be saved, we try to use a pattern matching
        # for latitude and longitude. This is not very nice, hence it is
        # better to specify the :attr:`x` and :attr:`y` attribute
        tnames = self.t.intersection(coord_names)
        if axis == 'x':
            for cname in filter(lambda cname: re.search('lon', cname),
                                coord_names):
                return get_coord(cname)
            return get_coord(coord_names[-1], raise_error=False)
        elif axis == 'y' and len(coord_names) >= 2:
            for cname in filter(lambda cname: re.search('lat', cname),
                                coord_names):
                return get_coord(cname)
            return get_coord(coord_names[-2], raise_error=False)
        elif (axis == 'z' and len(coord_names) >= 3 and
              coord_names[-3] not in tnames):
            return get_coord(coord_names[-3], raise_error=False)
        elif axis == 't' and tnames:
            tname = next(iter(tnames))
            if len(tnames) > 1:
                warn("Found multiple matches for time coordinate in the "
                     "coordinates: %s. I use %s" % (', '.join(tnames), tname),
                     PsyPlotRuntimeWarning)
            return get_coord(tname, raise_error=False)

    @docstrings.get_sections(base="CFDecoder.get_x", sections=[
        'Parameters', 'Returns'])
    @dedent
    def get_x(self, var, coords=None):
        """
        Get the x-coordinate of a variable

        This method searches for the x-coordinate in the :attr:`ds`. It first
        checks whether there is one dimension that holds an ``'axis'``
        attribute with 'X', otherwise it looks whether there is an intersection
        between the :attr:`x` attribute and the variables dimensions, otherwise
        it returns the coordinate corresponding to the last dimension of `var`

        Possible types
        --------------
        var: xarray.Variable
            The variable to get the x-coordinate for
        coords: dict
            Coordinates to use. If None, the coordinates of the dataset in the
            :attr:`ds` attribute are used.

        Returns
        -------
        xarray.Coordinate or None
            The y-coordinate or None if it could be found"""
        coords = coords or self.ds.coords
        coord = self.get_variable_by_axis(var, 'x', coords)
        if coord is not None:
            return coord
        return coords.get(self.get_xname(var))

    def get_xname(self, var, coords=None):
        """Get the name of the x-dimension

        This method gives the name of the x-dimension (which is not necessarily
        the name of the coordinate if the variable has a coordinate attribute)

        Parameters
        ----------
        var: xarray.Variables
            The variable to get the dimension for
        coords: dict
            The coordinates to use for checking the axis attribute. If None,
            they are not used

        Returns
        -------
        str
            The coordinate name

        See Also
        --------
        get_x"""
        if coords is not None:
            coord = self.get_variable_by_axis(var, 'x', coords)
            if coord is not None and coord.name in var.dims:
                return coord.name
        dimlist = list(self.x.intersection(var.dims))
        if dimlist:
            if len(dimlist) > 1:
                warn("Found multiple matches for x coordinate in the variable:"
                     "%s. I use %s" % (', '.join(dimlist), dimlist[0]),
                     PsyPlotRuntimeWarning)
            return dimlist[0]
        # otherwise we return the coordinate in the last position
        if var.dims:
            return var.dims[-1]

    @docstrings.get_sections(base="CFDecoder.get_y", sections=[
        'Parameters', 'Returns'])
    @dedent
    def get_y(self, var, coords=None):
        """
        Get the y-coordinate of a variable

        This method searches for the y-coordinate in the :attr:`ds`. It first
        checks whether there is one dimension that holds an ``'axis'``
        attribute with 'Y', otherwise it looks whether there is an intersection
        between the :attr:`y` attribute and the variables dimensions, otherwise
        it returns the coordinate corresponding to the second last dimension of
        `var` (or the last if the dimension of var is one-dimensional)

        Possible types
        --------------
        var: xarray.Variable
            The variable to get the y-coordinate for
        coords: dict
            Coordinates to use. If None, the coordinates of the dataset in the
            :attr:`ds` attribute are used.

        Returns
        -------
        xarray.Coordinate or None
            The y-coordinate or None if it could be found"""
        coords = coords or self.ds.coords
        coord = self.get_variable_by_axis(var, 'y', coords)
        if coord is not None:
            return coord
        return coords.get(self.get_yname(var))

    def get_yname(self, var, coords=None):
        """Get the name of the y-dimension

        This method gives the name of the y-dimension (which is not necessarily
        the name of the coordinate if the variable has a coordinate attribute)

        Parameters
        ----------
        var: xarray.Variables
            The variable to get the dimension for
        coords: dict
            The coordinates to use for checking the axis attribute. If None,
            they are not used

        Returns
        -------
        str
            The coordinate name

        See Also
        --------
        get_y"""
        if coords is not None:
            coord = self.get_variable_by_axis(var, 'y', coords)
            if coord is not None and coord.name in var.dims:
                return coord.name
        dimlist = list(self.y.intersection(var.dims))
        if dimlist:
            if len(dimlist) > 1:
                warn("Found multiple matches for y coordinate in the variable:"
                     "%s. I use %s" % (', '.join(dimlist), dimlist[0]),
                     PsyPlotRuntimeWarning)
            return dimlist[0]
        # otherwise we return the coordinate in the last or second last
        # position
        if var.dims:
            if self.is_unstructured(var):
                return var.dims[-1]
            return var.dims[-2 if var.ndim > 1 else -1]

    @docstrings.get_sections(base="CFDecoder.get_z", sections=[
        'Parameters', 'Returns'])
    @dedent
    def get_z(self, var, coords=None):
        """
        Get the vertical (z-) coordinate of a variable

        This method searches for the z-coordinate in the :attr:`ds`. It first
        checks whether there is one dimension that holds an ``'axis'``
        attribute with 'Z', otherwise it looks whether there is an intersection
        between the :attr:`z` attribute and the variables dimensions, otherwise
        it returns the coordinate corresponding to the third last dimension of
        `var` (or the second last or last if var is two or one-dimensional)

        Possible types
        --------------
        var: xarray.Variable
            The variable to get the z-coordinate for
        coords: dict
            Coordinates to use. If None, the coordinates of the dataset in the
            :attr:`ds` attribute are used.

        Returns
        -------
        xarray.Coordinate or None
            The z-coordinate or None if no z coordinate could be found"""
        coords = coords or self.ds.coords
        coord = self.get_variable_by_axis(var, 'z', coords)
        if coord is not None:
            return coord
        zname = self.get_zname(var)
        if zname is not None:
            return coords.get(zname)
        return None

    def get_zname(self, var, coords=None):
        """Get the name of the z-dimension

        This method gives the name of the z-dimension (which is not necessarily
        the name of the coordinate if the variable has a coordinate attribute)

        Parameters
        ----------
        var: xarray.Variables
            The variable to get the dimension for
        coords: dict
            The coordinates to use for checking the axis attribute. If None,
            they are not used

        Returns
        -------
        str or None
            The coordinate name or None if no vertical coordinate could be
            found

        See Also
        --------
        get_z"""
        if coords is not None:
            coord = self.get_variable_by_axis(var, 'z', coords)
            if coord is not None and coord.name in var.dims:
                return coord.name
        dimlist = list(self.z.intersection(var.dims))
        if dimlist:
            if len(dimlist) > 1:
                warn("Found multiple matches for z coordinate in the variable:"
                     "%s. I use %s" % (', '.join(dimlist), dimlist[0]),
                     PsyPlotRuntimeWarning)
            return dimlist[0]
        # otherwise we return the coordinate in the third last position
        if var.dims:
            is_unstructured = self.is_unstructured(var)
            icheck = -2 if is_unstructured else -3
            min_dim = abs(icheck) if 'variable' not in var.dims else abs(icheck-1)
            if var.ndim >= min_dim and var.dims[icheck] != self.get_tname(
                    var, coords):
                return var.dims[icheck]
        return None

    @docstrings.get_sections(base="CFDecoder.get_t", sections=[
        'Parameters', 'Returns'])
    @dedent
    def get_t(self, var, coords=None):
        """
        Get the time coordinate of a variable

        This method searches for the time coordinate in the :attr:`ds`. It
        first checks whether there is one dimension that holds an ``'axis'``
        attribute with 'T', otherwise it looks whether there is an intersection
        between the :attr:`t` attribute and the variables dimensions, otherwise
        it returns the coordinate corresponding to the first dimension of `var`

        Possible types
        --------------
        var: xarray.Variable
            The variable to get the time coordinate for
        coords: dict
            Coordinates to use. If None, the coordinates of the dataset in the
            :attr:`ds` attribute are used.

        Returns
        -------
        xarray.Coordinate or None
            The time coordinate or None if no time coordinate could be found"""
        coords = coords or self.ds.coords
        coord = self.get_variable_by_axis(var, 't', coords)
        if coord is not None:
            return coord
        dimlist = list(self.t.intersection(var.dims).intersection(coords))
        if dimlist:
            if len(dimlist) > 1:
                warn("Found multiple matches for time coordinate in the "
                     "variable: %s. I use %s" % (
                         ', '.join(dimlist), dimlist[0]),
                     PsyPlotRuntimeWarning)
            return coords[dimlist[0]]
        tname = self.get_tname(var)
        if tname is not None:
            return coords.get(tname)
        return None

    def get_tname(self, var, coords=None):
        """Get the name of the t-dimension

        This method gives the name of the time dimension

        Parameters
        ----------
        var: xarray.Variables
            The variable to get the dimension for
        coords: dict
            The coordinates to use for checking the axis attribute. If None,
            they are not used

        Returns
        -------
        str or None
            The coordinate name or None if no time coordinate could be found

        See Also
        --------
        get_t"""
        if coords is not None:
            coord = self.get_variable_by_axis(var, 't', coords)
            if coord is not None and coord.name in var.dims:
                return coord.name
        dimlist = list(self.t.intersection(var.dims))
        if dimlist:
            if len(dimlist) > 1:
                warn("Found multiple matches for t coordinate in the variable:"
                     "%s. I use %s" % (', '.join(dimlist), dimlist[0]),
                     PsyPlotRuntimeWarning)
            return dimlist[0]
        # otherwise we return None
        return None

    def get_idims(self, arr, coords=None):
        """Get the coordinates in the :attr:`ds` dataset as int or slice

        This method returns a mapping from the coordinate names of the given
        `arr` to an integer, slice or an array of integer that represent the
        coordinates in the :attr:`ds` dataset and can be used to extract the
        given `arr` via the :meth:`xarray.Dataset.isel` method.

        Parameters
        ----------
        arr: xarray.DataArray
            The data array for which to get the dimensions as integers, slices
            or list of integers from the dataset in the :attr:`base` attribute
        coords: iterable
            The coordinates to use. If not given all coordinates in the
            ``arr.coords`` attribute are used

        Returns
        -------
        dict
            Mapping from coordinate name to integer, list of integer or slice

        See Also
        --------
        xarray.Dataset.isel, InteractiveArray.idims"""
        if coords is None:
            coords = arr.coords
        else:
            coords = {
                label: coord for label, coord in six.iteritems(arr.coords)
                if label in coords}
        ret = self.get_coord_idims(coords)
        # handle the coordinates that are not in the dataset
        missing = set(arr.dims).difference(ret)
        if missing:
            warn('Could not get slices for the following dimensions: %r' % (
                missing, ), PsyPlotRuntimeWarning)
        return ret

    def get_coord_idims(self, coords):
        """Get the slicers for the given coordinates from the base dataset

        This method converts `coords` to slicers (list of
        integers or ``slice`` objects)

        Parameters
        ----------
        coords: dict
            A subset of the ``ds.coords`` attribute of the base dataset
            :attr:`ds`

        Returns
        -------
        dict
            Mapping from coordinate name to integer, list of integer or slice
        """
        ret = dict(
            (label, get_index_from_coord(coord, self.ds.indexes[label]))
            for label, coord in six.iteritems(coords)
            if label in self.ds.indexes)
        return ret

    @docstrings.get_sections(base='CFDecoder.get_plotbounds', sections=[
        'Parameters', 'Returns'])
    @dedent
    def get_plotbounds(self, coord, kind=None, ignore_shape=False):
        """
        Get the bounds of a coordinate

        This method first checks the ``'bounds'`` attribute of the given
        `coord` and if it fails, it calculates them.

        Parameters
        ----------
        coord: xarray.Coordinate
            The coordinate to get the bounds for
        kind: str
            The interpolation method (see :func:`scipy.interpolate.interp1d`)
            that is used in case of a 2-dimensional coordinate
        ignore_shape: bool
            If True and the `coord` has a ``'bounds'`` attribute, this
            attribute is returned without further check. Otherwise it is tried
            to bring the ``'bounds'`` into a format suitable for (e.g.) the
            :func:`matplotlib.pyplot.pcolormesh` function.

        Returns
        -------
        bounds: np.ndarray
            The bounds with the same number of dimensions as `coord` but one
            additional array (i.e. if `coord` has shape (4, ), `bounds` will
            have shape (5, ) and if `coord` has shape (4, 5), `bounds` will
            have shape (5, 6)"""
        if 'bounds' in coord.attrs:
            bounds = self.ds.coords[coord.attrs['bounds']]
            if ignore_shape:
                return bounds.values.ravel()
            if not bounds.shape[:-1] == coord.shape:
                bounds = self.ds.isel(**self.get_idims(coord))
            try:
                return self._get_plotbounds_from_cf(coord, bounds)
            except ValueError as e:
                warn((e.message if six.PY2 else str(e)) +
                     " Bounds are calculated automatically!")
        return self._infer_interval_breaks(coord, kind=kind)

    @staticmethod
    @docstrings.dedent
    def _get_plotbounds_from_cf(coord, bounds):
        """
        Get plot bounds from the bounds stored as defined by CFConventions

        Parameters
        ----------
        coord: xarray.Coordinate
            The coordinate to get the bounds for
        bounds: xarray.DataArray
            The bounds as inferred from the attributes of the given `coord`

        Returns
        -------
        %(CFDecoder.get_plotbounds.returns)s

        Notes
        -----
        this currently only works for rectilinear grids"""

        if bounds.shape[:-1] != coord.shape or bounds.shape[-1] != 2:
            raise ValueError(
                "Cannot interprete bounds with shape {0} for {1} "
                "coordinate with shape {2}.".format(
                    bounds.shape, coord.name, coord.shape))
        ret = np.zeros(tuple(map(lambda i: i+1, coord.shape)))
        ret[tuple(map(slice, coord.shape))] = bounds[..., 0]
        last_slices = tuple(slice(-1, None) for _ in coord.shape)
        ret[last_slices] = bounds[tuple(chain(last_slices, [1]))]
        return ret

    docstrings.keep_params('CFDecoder._check_unstructured_bounds.parameters',
                           'nans')

    @docstrings.get_sections(base='CFDecoder.get_triangles', sections=[
        'Parameters', 'Returns'])
    @docstrings.dedent
    def get_triangles(self, var, coords=None, convert_radian=True,
                      copy=False, src_crs=None, target_crs=None,
                      nans=None, stacklevel=1):
        """
        Get the triangles for the variable

        Parameters
        ----------
        var: xarray.Variable or xarray.DataArray
            The variable to use
        coords: dict
            Alternative coordinates to use. If None, the coordinates of the
            :attr:`ds` dataset are used
        convert_radian: bool
            If True and the coordinate has units in 'radian', those are
            converted to degrees
        copy: bool
            If True, vertice arrays are copied
        src_crs: cartopy.crs.Crs
            The source projection of the data. If not None, a transformation
            to the given `target_crs` will be done
        target_crs: cartopy.crs.Crs
            The target projection for which the triangles shall be transformed.
            Must only be provided if the `src_crs` is not None.
        %(CFDecoder._check_unstructured_bounds.parameters.nans)s

        Returns
        -------
        matplotlib.tri.Triangulation
            The spatial triangles of the variable

        Raises
        ------
        ValueError
            If `src_crs` is not None and `target_crs` is None"""
        warn("The 'get_triangles' method is depreceated and will be removed "
             "soon! Use the 'get_cell_node_coord' method!",
             DeprecationWarning, stacklevel=stacklevel)
        from matplotlib.tri import Triangulation

        def get_vertices(axis):
            bounds = self._check_unstructured_bounds(var, coords=coords,
                                                   axis=axis, nans=nans)[1]
            if coords is not None:
                bounds = coords.get(bounds.name, bounds)
            vertices = bounds.values.ravel()
            if convert_radian:
                coord = getattr(self, 'get_' + axis)(var)
                if coord.attrs.get('units') == 'radian':
                    vertices = vertices * 180. / np.pi
            return vertices if not copy else vertices.copy()

        if coords is None:
            coords = self.ds.coords

        xvert = get_vertices('x')
        yvert = get_vertices('y')
        if src_crs is not None and src_crs != target_crs:
            if target_crs is None:
                raise ValueError(
                    "Found %s for the source crs but got None for the "
                    "target_crs!" % (src_crs, ))
            arr = target_crs.transform_points(src_crs, xvert, yvert)
            xvert = arr[:, 0]
            yvert = arr[:, 1]
        triangles = np.reshape(range(len(xvert)), (len(xvert) // 3, 3))
        return Triangulation(xvert, yvert, triangles)

    docstrings.delete_params(
        'CFDecoder.get_plotbounds.parameters', 'ignore_shape')

    @staticmethod
    def _infer_interval_breaks(coord, kind=None):
        """
        Interpolate the bounds from the data in coord

        Parameters
        ----------
        %(CFDecoder.get_plotbounds.parameters.no_ignore_shape)s

        Returns
        -------
        %(CFDecoder.get_plotbounds.returns)s

        Notes
        -----
        this currently only works for rectilinear grids"""
        if coord.ndim == 1:
            return _infer_interval_breaks(coord)
        elif coord.ndim == 2:
            from scipy.interpolate import interp2d
            kind = kind or rcParams['decoder.interp_kind']
            y, x = map(np.arange, coord.shape)
            new_x, new_y = map(_infer_interval_breaks, [x, y])
            coord = np.asarray(coord)
            return interp2d(x, y, coord, kind=kind, copy=False)(new_x, new_y)

    @classmethod
    @docstrings.get_sections(base='CFDecoder._decode_ds')
    @docstrings.dedent
    def _decode_ds(cls, ds, gridfile=None, decode_coords=True,
                   decode_times=True):
        """
        Static method to decode coordinates and time informations

        This method interpretes absolute time informations (stored with units
        ``'day as %Y%m%d.%f'``) and coordinates

        Parameters
        ----------
        %(CFDecoder.decode_coords.parameters)s
        decode_times : bool, optional
            If True, decode times encoded in the standard NetCDF datetime
            format into datetime objects. Otherwise, leave them encoded as
            numbers.
        decode_coords : bool, optional
            If True, decode the 'coordinates' attribute to identify coordinates
            in the resulting dataset."""
        if decode_coords:
            ds = cls.decode_coords(ds, gridfile=gridfile)
        if decode_times:
            for k, v in six.iteritems(ds.variables):
                # check for absolute time units and make sure the data is not
                # already decoded via dtype check
                if v.attrs.get('units', '') == 'day as %Y%m%d.%f' and (
                        np.issubdtype(v.dtype, np.float64)):
                    decoded = xr.Variable(
                        v.dims, AbsoluteTimeDecoder(v), attrs=v.attrs,
                        encoding=v.encoding)
                    ds.update({k: decoded})
        return ds

    @classmethod
    @docstrings.dedent
    def decode_ds(cls, ds, *args, **kwargs):
        """
        Static method to decode coordinates and time informations

        This method interpretes absolute time informations (stored with units
        ``'day as %Y%m%d.%f'``) and coordinates

        Parameters
        ----------
        %(CFDecoder._decode_ds.parameters)s

        Returns
        -------
        xarray.Dataset
            The decoded dataset"""
        for decoder_cls in cls._registry + [CFDecoder]:
            ds = decoder_cls._decode_ds(ds, *args, **kwargs)
        return ds

    def correct_dims(self, var, dims={}, remove=True):
        """Expands the dimensions to match the dims in the variable

        Parameters
        ----------
        var: xarray.Variable
            The variable to get the data for
        dims: dict
            a mapping from dimension to the slices
        remove: bool
            If True, dimensions in `dims` that are not in the dimensions of
            `var` are removed"""
        method_mapping = {'x': self.get_xname,
                          'z': self.get_zname, 't': self.get_tname}
        dims = dict(dims)
        if self.is_unstructured(var):  # we assume a one-dimensional grid
            method_mapping['y'] = self.get_xname
        else:
            method_mapping['y'] = self.get_yname
        for key in six.iterkeys(dims.copy()):
            if key in method_mapping and key not in var.dims:
                dim_name = method_mapping[key](var, self.ds.coords)
                if dim_name in dims:
                    dims.pop(key)
                else:
                    new_name = method_mapping[key](var)
                    if new_name is not None:
                        dims[new_name] = dims.pop(key)
        # now remove the unnecessary dimensions
        if remove:
            for key in set(dims).difference(var.dims):
                dims.pop(key)
                self.logger.debug(
                    "Could not find a dimensions matching %s in variable %s!",
                    key, var)
        return dims

    def standardize_dims(self, var, dims={}):
        """Replace the coordinate names through x, y, z and t

        Parameters
        ----------
        var: xarray.Variable
            The variable to use the dimensions of
        dims: dict
            The dictionary to use for replacing the original dimensions

        Returns
        -------
        dict
            The dictionary with replaced dimensions"""
        dims = dict(dims)
        name_map = {self.get_xname(var, self.ds.coords): 'x',
                    self.get_yname(var, self.ds.coords): 'y',
                    self.get_zname(var, self.ds.coords): 'z',
                    self.get_tname(var, self.ds.coords): 't'}
        dims = dict(dims)
        for dim in set(dims).intersection(name_map):
            dims[name_map[dim]] = dims.pop(dim)
        return dims


class UGridDecoder(CFDecoder):
    """
    Decoder for UGrid data sets

    Warnings
    --------
    Currently only triangles are supported."""

    def is_unstructured(self, *args, **kwargs):
        """Reimpletemented to return always True. Any ``*args`` and ``**kwargs``
        are ignored"""
        return True

    def get_mesh(self, var, coords=None):
        """Get the mesh variable for the given `var`

        Parameters
        ----------
        var: xarray.Variable
            The data source whith the ``'mesh'`` attribute
        coords: dict
            The coordinates to use. If None, the coordinates of the dataset of
            this decoder is used

        Returns
        -------
        xarray.Coordinate
            The mesh coordinate"""
        mesh = var.attrs.get('mesh')
        if mesh is None:
            return None
        if coords is None:
            coords = self.ds.coords
        return coords.get(mesh, self.ds.coords.get(mesh))

    @classmethod
    @docstrings.dedent
    def can_decode(cls, ds, var):
        """
        Check whether the given variable can be decoded.

        Returns True if a mesh coordinate could be found via the
        :meth:`get_mesh` method

        Parameters
        ----------
        %(CFDecoder.can_decode.parameters)s

        Returns
        -------
        %(CFDecoder.can_decode.returns)s"""
        return cls(ds).get_mesh(var) is not None

    @docstrings.dedent
    def get_triangles(self, var, coords=None, convert_radian=True, copy=False,
                      src_crs=None, target_crs=None, nans=None, stacklevel=1):
        """
        Get the of the given coordinate.

        Parameters
        ----------
        %(CFDecoder.get_triangles.parameters)s

        Returns
        -------
        %(CFDecoder.get_triangles.returns)s

        Notes
        -----
        If the ``'location'`` attribute is set to ``'node'``, a delaunay
        triangulation is performed using the
        :class:`matplotlib.tri.Triangulation` class.

        .. todo::
            Implement the visualization for UGrid data shown on the edge of the
            triangles"""
        warn("The 'get_triangles' method is depreceated and will be removed "
             "soon! Use the 'get_cell_node_coord' method!",
             DeprecationWarning, stacklevel=stacklevel)
        from matplotlib.tri import Triangulation

        if coords is None:
            coords = self.ds.coords

        def get_coord(coord):
            return coords.get(coord, self.ds.coords.get(coord))

        mesh = self.get_mesh(var, coords)
        nodes = self.get_nodes(mesh, coords)
        if any(n is None for n in nodes):
            raise ValueError("Could not find the nodes variables!")
        xvert, yvert = nodes
        xvert = xvert.values
        yvert = yvert.values
        loc = var.attrs.get('location', 'face')
        if loc == 'face':
            triangles = get_coord(
                mesh.attrs.get('face_node_connectivity', '')).values
            if triangles is None:
                raise ValueError(
                    "Could not find the connectivity information!")
        elif loc == 'node':
            triangles = None
        else:
            raise ValueError(
                "Could not interprete location attribute (%s) of mesh "
                "variable %s!" % (loc, mesh.name))

        if convert_radian:
            for coord in nodes:
                if coord.attrs.get('units') == 'radian':
                    coord = coord * 180. / np.pi
        if src_crs is not None and src_crs != target_crs:
            if target_crs is None:
                raise ValueError(
                    "Found %s for the source crs but got None for the "
                    "target_crs!" % (src_crs, ))
            xvert = xvert[triangles].ravel()
            yvert = yvert[triangles].ravel()
            arr = target_crs.transform_points(src_crs, xvert, yvert)
            xvert = arr[:, 0]
            yvert = arr[:, 1]
            if loc == 'face':
                triangles = np.reshape(range(len(xvert)), (len(xvert) // 3,
                                                           3))

        return Triangulation(xvert, yvert, triangles)

    @docstrings.dedent
    def get_cell_node_coord(self, var, coords=None, axis='x', nans=None):
        """
        Checks whether the bounds in the variable attribute are triangular

        Parameters
        ----------
        %(CFDecoder.get_cell_node_coord.parameters)s

        Returns
        -------
        %(CFDecoder.get_cell_node_coord.returns)s"""
        if coords is None:
            coords = self.ds.coords

        idims = self.get_coord_idims(coords)

        def get_coord(coord):
            coord = coords.get(coord, self.ds.coords.get(coord))
            return coord.isel(**{d: sl for d, sl in idims.items()
                                 if d in coord.dims})

        mesh = self.get_mesh(var, coords)
        if mesh is None:
            return
        nodes = self.get_nodes(mesh, coords)
        if not len(nodes):
            raise ValueError("Could not find the nodes variables for the %s "
                             "coordinate!" % axis)
        vert = nodes[0 if axis == 'x' else 1]
        if vert is None:
            raise ValueError("Could not find the nodes variables for the %s "
                             "coordinate!" % axis)
        loc = var.attrs.get('location', 'face')
        if loc == 'node':
            # we assume a triangular grid and use matplotlibs triangulation
            from matplotlib.tri import Triangulation
            xvert, yvert = nodes
            triangles = Triangulation(xvert, yvert)
            if axis == 'x':
                bounds = triangles.x[triangles.triangles]
            else:
                bounds = triangles.y[triangles.triangles]
        elif loc in ['edge', 'face']:
            connectivity = get_coord(
                mesh.attrs.get('%s_node_connectivity' % loc, ''))
            if connectivity is None:
                raise ValueError(
                    "Could not find the connectivity information!")
            connectivity = connectivity.values
            bounds = vert.values[
                np.where(np.isnan(connectivity), connectivity[:, :1],
                         connectivity).astype(int)]
        else:
            raise ValueError(
                "Could not interprete location attribute (%s) of mesh "
                "variable %s!" % (loc, mesh.name))
        dim0 = '__face' if loc == 'node' else var.dims[-1]
        return xr.DataArray(
            bounds,
            coords={key: val for key, val in coords.items()
                    if (dim0, ) == val.dims},
            dims=(dim0, '__bnds', ),
            name=vert.name + '_bnds',  attrs=vert.attrs.copy())

    @staticmethod
    @docstrings.dedent
    def decode_coords(ds, gridfile=None):
        """
        Reimplemented to set the mesh variables as coordinates

        Parameters
        ----------
        %(CFDecoder.decode_coords.parameters)s

        Returns
        -------
        %(CFDecoder.decode_coords.returns)s"""
        extra_coords = set(ds.coords)
        for var in six.itervalues(ds.variables):
            if 'mesh' in var.attrs:
                mesh = var.attrs['mesh']
                if mesh not in extra_coords:
                    extra_coords.add(mesh)
                    try:
                        mesh_var = ds.variables[mesh]
                    except KeyError:
                        warn('Could not find mesh variable %s' % mesh)
                        continue
                    if 'node_coordinates' in mesh_var.attrs:
                        extra_coords.update(
                            mesh_var.attrs['node_coordinates'].split())
                    if 'face_node_connectivity' in mesh_var.attrs:
                        extra_coords.add(
                            mesh_var.attrs['face_node_connectivity'])
        if gridfile is not None and not isinstance(gridfile, xr.Dataset):
            gridfile = open_dataset(gridfile)
            ds.update({k: v for k, v in six.iteritems(gridfile.variables)
                       if k in extra_coords})
        if xr_version < (0, 11):
            ds.set_coords(extra_coords.intersection(ds.variables),
                          inplace=True)
        else:
            ds._coord_names.update(extra_coords.intersection(ds.variables))
        return ds

    def get_nodes(self, coord, coords):
        """Get the variables containing the definition of the nodes

        Parameters
        ----------
        coord: xarray.Coordinate
            The mesh variable
        coords: dict
            The coordinates to use to get node coordinates"""
        def get_coord(coord):
            return coords.get(coord, self.ds.coords.get(coord))
        return list(map(get_coord,
                        coord.attrs.get('node_coordinates', '').split()[:2]))

    @docstrings.dedent
    def get_x(self, var, coords=None):
        """
        Get the centers of the triangles in the x-dimension

        Parameters
        ----------
        %(CFDecoder.get_y.parameters)s

        Returns
        -------
        %(CFDecoder.get_y.returns)s"""
        if coords is None:
            coords = self.ds.coords
        # first we try the super class
        ret = super(UGridDecoder, self).get_x(var, coords)
        # but if that doesn't work because we get the variable name in the
        # dimension of `var`, we use the means of the triangles
        if ret is None or ret.name in var.dims or (hasattr(var, 'mesh') and
                                                   ret.name == var.mesh):
            bounds = self.get_cell_node_coord(var, axis='x', coords=coords)
            if bounds is not None:
                centers = bounds.mean(axis=-1)
                x = self.get_nodes(self.get_mesh(var, coords), coords)[0]
                try:
                    cls = xr.IndexVariable
                except AttributeError:  # xarray < 0.9
                    cls = xr.Coordinate
                return cls(x.name, centers, attrs=x.attrs.copy())
        else:
            return ret

    @docstrings.dedent
    def get_y(self, var, coords=None):
        """
        Get the centers of the triangles in the y-dimension

        Parameters
        ----------
        %(CFDecoder.get_y.parameters)s

        Returns
        -------
        %(CFDecoder.get_y.returns)s"""
        if coords is None:
            coords = self.ds.coords
        # first we try the super class
        ret = super(UGridDecoder, self).get_y(var, coords)
        # but if that doesn't work because we get the variable name in the
        # dimension of `var`, we use the means of the triangles
        if ret is None or ret.name in var.dims or (hasattr(var, 'mesh') and
                                                   ret.name == var.mesh):
            bounds = self.get_cell_node_coord(var, axis='y', coords=coords)
            if bounds is not None:
                centers = bounds.mean(axis=-1)
                y = self.get_nodes(self.get_mesh(var, coords), coords)[1]
                try:
                    cls = xr.IndexVariable
                except AttributeError:  # xarray < 0.9
                    cls = xr.Coordinate
                return cls(y.name, centers, attrs=y.attrs.copy())
        else:
            return ret


# register the UGridDecoder
CFDecoder.register_decoder(UGridDecoder)

docstrings.keep_params('CFDecoder.decode_coords.parameters', 'gridfile')
docstrings.get_sections(inspect.cleandoc(
    xr.open_dataset.__doc__.split('\n', 1)[1]),
    'xarray.open_dataset')
docstrings.delete_params('xarray.open_dataset.parameters', 'engine')


@docstrings.get_sections(base='open_dataset')
@docstrings.dedent
def open_dataset(filename_or_obj, decode_cf=True, decode_times=True,
                 decode_coords=True, engine=None, gridfile=None, **kwargs):
    """
    Open an instance of :class:`xarray.Dataset`.

    This method has the same functionality as the :func:`xarray.open_dataset`
    method except that is supports an additional 'gdal' engine to open
    gdal Rasters (e.g. GeoTiffs) and that is supports absolute time units like
    ``'day as %Y%m%d.%f'`` (if `decode_cf` and `decode_times` are True).

    Parameters
    ----------
    %(xarray.open_dataset.parameters.no_engine)s
    engine: {'netcdf4', 'scipy', 'pydap', 'h5netcdf', 'gdal'}, optional
        Engine to use when reading netCDF files. If not provided, the default
        engine is chosen based on available dependencies, with a preference for
        'netcdf4'.
    %(CFDecoder.decode_coords.parameters.gridfile)s

    Returns
    -------
    xarray.Dataset
        The dataset that contains the variables from `filename_or_obj`"""
    # use the absolute path name (is saver when saving the project)
    if isstring(filename_or_obj) and osp.exists(filename_or_obj):
        filename_or_obj = osp.abspath(filename_or_obj)
    if engine == 'gdal':
        from psyplot.gdal_store import GdalStore
        filename_or_obj = GdalStore(filename_or_obj)
        engine = None
    ds = xr.open_dataset(filename_or_obj, decode_cf=decode_cf,
                         decode_coords=False, engine=engine,
                         decode_times=decode_times, **kwargs)
    if isstring(filename_or_obj):
        ds.psy.filename = filename_or_obj
    if decode_cf:
        ds = CFDecoder.decode_ds(
            ds, decode_coords=decode_coords, decode_times=decode_times,
            gridfile=gridfile)
    return ds


docstrings.get_sections(
    inspect.cleandoc(xr.open_mfdataset.__doc__.split('\n', 1)[1]),
    'xarray.open_mfdataset')
docstrings.delete_params('xarray.open_mfdataset.parameters', 'engine')
docstrings.keep_params('get_tdata.parameters', 't_format')

docstrings.params['xarray.open_mfdataset.parameters.no_engine'] = \
    docstrings.params['xarray.open_mfdataset.parameters.no_engine'].replace(
        '**kwargs', '``**kwargs``').replace('"path/to/my/files/*.nc"',
                                            '``"path/to/my/files/*.nc"``')


docstrings.keep_params('open_dataset.parameters', 'engine')


@docstrings.dedent
def open_mfdataset(paths, decode_cf=True, decode_times=True,
                   decode_coords=True, engine=None, gridfile=None,
                   t_format=None, **kwargs):
    """
    Open multiple files as a single dataset.

    This function is essentially the same as the :func:`xarray.open_mfdataset`
    function but (as the :func:`open_dataset`) supports additional decoding
    and the ``'gdal'`` engine.
    You can further specify the `t_format` parameter to get the time
    information from the files and use the results to concatenate the files

    Parameters
    ----------
    %(xarray.open_mfdataset.parameters.no_engine)s
    %(open_dataset.parameters.engine)s
    %(get_tdata.parameters.t_format)s
    %(CFDecoder.decode_coords.parameters.gridfile)s

    Returns
    -------
    xarray.Dataset
        The dataset that contains the variables from `filename_or_obj`"""
    if t_format is not None or engine == 'gdal':
        if isinstance(paths, six.string_types):
            paths = sorted(glob(paths))
        if not paths:
            raise IOError('no files to open')
    if t_format is not None:
        time, paths = get_tdata(t_format, paths)
        kwargs['concat_dim'] = 'time'
        if xr_version > (0, 11):
            kwargs['combine'] = 'nested'
    if all(map(isstring, paths)):
        filenames = list(paths)
    else:
        filenames = None
    if engine == 'gdal':
        from psyplot.gdal_store import GdalStore
        paths = list(map(GdalStore, paths))
        engine = None
        if xr_version < (0, 18):
            kwargs['lock'] = False

    ds = xr.open_mfdataset(
        paths, decode_cf=decode_cf, decode_times=decode_times, engine=engine,
        decode_coords=False, **kwargs)
    ds.psy.filename = filenames
    if decode_cf:
        ds = CFDecoder.decode_ds(ds, gridfile=gridfile,
                                 decode_coords=decode_coords,
                                 decode_times=decode_times)
    ds.psy._concat_dim = kwargs.get('concat_dim')
    ds.psy._combine = kwargs.get('combine')
    if t_format is not None:
        ds['time'] = time
    return ds


class InteractiveBase(object):
    """Class for the communication of a data object with a suitable plotter

    This class serves as an interface for data objects (in particular as a
    base for :class:`InteractiveArray` and :class:`InteractiveList`) to
    communicate with the corresponding :class:`~psyplot.plotter.Plotter` in the
    :attr:`plotter` attribute"""

    #: The :class:`psyplot.project.DataArrayPlotter`
    _plot = None

    @property
    def plotter(self):
        """:class:`psyplot.plotter.Plotter` instance that makes the interactive
        plotting of the data"""
        return self._plotter

    @plotter.setter
    def plotter(self, value):
        self._plotter = value

    @plotter.deleter
    def plotter(self):
        self._plotter = None

    no_auto_update = property(_no_auto_update_getter,
                              doc=_no_auto_update_getter.__doc__)

    @property
    def plot(self):
        """An object to visualize this data object

        To make a 2D-plot with the :mod:`psy-simple <psy_simple.plugin>`
        plugin, you can just type

        .. code-block:: python

            plotter = da.psy.plot.plot2d()

        It will create a new :class:`psyplot.plotter.Plotter` instance with the
        extracted and visualized data.

        See Also
        --------
        psyplot.project.DataArrayPlotter: for the different plot methods"""
        if self._plot is None:
            import psyplot.project as psy
            self._plot = psy.DataArrayPlotter(self)
        return self._plot

    @no_auto_update.setter
    def no_auto_update(self, value):
        if self.plotter is not None:
            self.plotter.no_auto_update = value
        self.no_auto_update.value = bool(value)

    @property
    def logger(self):
        """:class:`logging.Logger` of this instance"""
        try:
            return self._logger
        except AttributeError:
            name = '%s.%s.%s' % (self.__module__, self.__class__.__name__,
                                 self.arr_name)
            self._logger = logging.getLogger(name)
            self.logger.debug('Initializing...')
            return self._logger

    @logger.setter
    def logger(self, value):
        self._logger = value

    @property
    def ax(self):
        """The matplotlib axes the plotter of this data object plots on"""
        return None if self.plotter is None else self.plotter.ax

    @ax.setter
    def ax(self, value):
        if self.plotter is None:
            raise ValueError(
                'Cannot set the axes because the plotter attribute is None!')
        self.plotter.ax = value

    block_signals = utils._temp_bool_prop(
        'block_signals', "Block the emitting of signals of this instance")

    # -------------------------------------------------------------------------
    # -------------------------------- SIGNALS --------------------------------
    # -------------------------------------------------------------------------

    #: :class:`Signal` to be emitted when the object has been updated
    onupdate = Signal('_onupdate')
    _onupdate = None

    _plotter = None

    @property
    @docstrings.get_docstring(base='InteractiveBase._njobs')
    @dedent
    def _njobs(self):
        """
        The number of jobs taken from the queue during an update process

        Returns
        -------
        list of int
            The length of the list determines the number of neccessary queues,
            the numbers in the list determines the number of tasks per queue
            this instance fullfills during the update process"""
        return self.plotter._njobs if self.plotter is not None else []

    @property
    def arr_name(self):
        """:class:`str`. The internal name of the :class:`InteractiveBase`"""
        return self._arr_name

    @arr_name.setter
    def arr_name(self, value):
        self._arr_name = value
        try:
            del self._logger
        except AttributeError:
            pass
        self.onupdate.emit()

    _arr_name = None

    _no_auto_update = None

    @docstrings.get_sections(base='InteractiveBase')
    @dedent
    def __init__(self, plotter=None, arr_name='arr0', auto_update=None):
        """
        Parameters
        ----------
        plotter: Plotter
            Default: None. Interactive plotter that makes the plot via
            formatoption keywords.
        arr_name: str
            Default: ``'data'``. unique string of the array
        auto_update: bool
            Default: None. A boolean indicating whether this list shall
            automatically update the contained arrays when calling the
            :meth:`update` method or not. See also the :attr:`no_auto_update`
            attribute. If None, the value from the ``'lists.auto_update'``
            key in the :attr:`psyplot.rcParams` dictionary is used."""
        self.plotter = plotter
        self.arr_name = arr_name
        if auto_update is None:
            auto_update = rcParams['lists.auto_update']
        self.no_auto_update = not bool(auto_update)
        self.replot = False

    def _finish_all(self, queues):
        for n, queue in zip(safe_list(self._njobs), safe_list(queues)):
            if queue is not None:
                for i in range(n):
                    queue.task_done()

    @docstrings.get_sections(base='InteractiveBase._register_update')
    @dedent
    def _register_update(self, replot=False, fmt={}, force=False,
                         todefault=False):
        """
        Register new formatoptions for updating

        Parameters
        ----------
        replot: bool
            Boolean that determines whether the data specific formatoptions
            shall be updated in any case or not. Note, if `dims` is not empty
            or any coordinate keyword is in ``**kwargs``, this will be set to
            True automatically
        fmt: dict
            Keys may be any valid formatoption of the formatoptions in the
            :attr:`plotter`
        force: str, list of str or bool
            If formatoption key (i.e. string) or list of formatoption keys,
            thery are definitely updated whether they changed or not.
            If True, all the given formatoptions in this call of the are
            :meth:`update` method are updated
        todefault: bool
            If True, all changed formatoptions (except the registered ones)
            are updated to their default value as stored in the
            :attr:`~psyplot.plotter.Plotter.rc` attribute

        See Also
        --------
        start_update"""
        self.replot = self.replot or replot
        if self.plotter is not None:
            self.plotter._register_update(replot=self.replot, fmt=fmt,
                                          force=force, todefault=todefault)

    @docstrings.get_sections(base='InteractiveBase.start_update',
                              sections=['Parameters', 'Returns'])
    @dedent
    def start_update(self, draw=None, queues=None):
        """
        Conduct the formerly registered updates

        This method conducts the updates that have been registered via the
        :meth:`update` method. You can call this method if the
        :attr:`no_auto_update` attribute of this instance and the `auto_update`
        parameter in the :meth:`update` method has been set to False

        Parameters
        ----------
        draw: bool or None
            Boolean to control whether the figure of this array shall be drawn
            at the end. If None, it defaults to the `'auto_draw'`` parameter
            in the :attr:`psyplot.rcParams` dictionary
        queues: list of :class:`Queue.Queue` instances
            The queues that are passed to the
            :meth:`psyplot.plotter.Plotter.start_update` method to ensure a
            thread-safe update. It can be None if only one single plotter is
            updated at the same time. The number of jobs that are taken from
            the queue is determined by the :meth:`_njobs` attribute. Note that
            there this parameter is automatically configured when updating
            from a :class:`~psyplot.project.Project`.

        Returns
        -------
        bool
            A boolean indicating whether a redrawing is necessary or not

        See Also
        --------
        :attr:`no_auto_update`, update
        """
        if self.plotter is not None:
            return self.plotter.start_update(draw=draw, queues=queues)

    docstrings.keep_params('InteractiveBase.start_update.parameters', 'draw')

    @docstrings.get_sections(base='InteractiveBase.update',
                              sections=['Parameters', 'Notes'])
    @docstrings.dedent
    def update(self, fmt={}, replot=False, draw=None, auto_update=False,
               force=False, todefault=False, **kwargs):
        """
        Update the coordinates and the plot

        This method updates all arrays in this list with the given coordinate
        values and formatoptions.

        Parameters
        ----------
        %(InteractiveBase._register_update.parameters)s
        auto_update: bool
            Boolean determining whether or not the :meth:`start_update` method
            is called at the end. This parameter has no effect if the
            :attr:`no_auto_update` attribute is set to ``True``.
        %(InteractiveBase.start_update.parameters.draw)s
        ``**kwargs``
            Any other formatoption that shall be updated (additionally to those
            in `fmt`)

        Notes
        -----
        If the :attr:`no_auto_update` attribute is True and the given
        `auto_update` parameter are is False, the update of the plots are
        registered and conducted at the next call of the :meth:`start_update`
        method or the next call of this method (if the `auto_update` parameter
        is then True).
        """
        fmt = dict(fmt)
        fmt.update(kwargs)

        self._register_update(replot=replot, fmt=fmt, force=force,
                              todefault=todefault)

        if not self.no_auto_update or auto_update:
            self.start_update(draw=draw)

    def to_interactive_list(self):
        """Return a :class:`InteractiveList` that contains this object"""
        raise NotImplementedError('Not implemented for the %s class' % (
            self.__class__.__name__, ))


@xr.register_dataarray_accessor('psy')
class InteractiveArray(InteractiveBase):
    """Interactive psyplot accessor for the data array

    This class keeps reference to the base :class:`xarray.Dataset` where the
    :class:`array.DataArray` originates from and enables to switch between the
    coordinates in the array. Furthermore it has a :attr:`plotter` attribute to
    enable interactive plotting via an :class:`psyplot.plotter.Plotter`
    instance."""

    @property
    def base(self):
        """Base dataset this instance gets its data from"""
        if self._base is None:
            if 'variable' in self.arr.dims:
                def to_dataset(i):
                    ret = self.isel(variable=i).to_dataset(
                        name=self.arr.coords['variable'].values[i])
                    try:
                        return ret.drop_vars('variable')
                    except ValueError:  # 'variable' Variable not defined
                        pass
                    return ret
                ds = to_dataset(0)
                if len(self.arr.coords['variable']) > 1:
                    for i in range(1, len(self.arr.coords['variable'])):
                        ds.update(ds.merge(to_dataset(i)))
                self._base = ds
            else:
                self._base = self.arr.to_dataset(
                    name=self.arr.name or self.arr_name)
            self.onbasechange.emit()
        return self._base

    @base.setter
    def base(self, value):
        self._base = value
        self.onbasechange.emit()

    @property
    def decoder(self):
        """The decoder of this array"""
        try:
            return self._decoder
        except AttributeError:
            self._decoder = CFDecoder.get_decoder(self.base, self.arr)
        return self._decoder

    @decoder.setter
    def decoder(self, value):
        self._decoder = value

    @property
    def idims(self):
        """Coordinates in the :attr:`base` dataset as int or slice

        This attribute holds a mapping from the coordinate names of this
        array to an integer, slice or an array of integer that represent the
        coordinates in the :attr:`base` dataset"""
        if self._idims is None:
            self._idims = self.decoder.get_idims(self.arr)
        return self._idims

    @idims.setter
    def idims(self, value):
        self._idims = value

    @property
    @docstrings
    def _njobs(self):
        """%(InteractiveBase._njobs)s"""
        ret = super(self.__class__, self)._njobs or [0]
        ret[0] += 1
        return ret

    logger = InteractiveBase.logger
    _idims = None
    _base = None

    # -------------- SIGNALS --------------------------------------------------
    #: :class:`Signal` to be emiited when the base of the object changes
    onbasechange = Signal('_onbasechange')
    _onbasechange = None

    @docstrings.dedent
    def __init__(self, xarray_obj, *args, **kwargs):
        """
        The ``*args`` and ``**kwargs`` are essentially the same as for the
        :class:`xarray.DataArray` method, additional ``**kwargs`` are
        described below.

        Other Parameters
        ----------------
        base: xarray.Dataset
            Default: None. Dataset that serves as the origin of the data
            contained in this DataArray instance. This will be used if you want
            to update the coordinates via the :meth:`update` method. If None,
            this instance will serve as a base as soon as it is needed.
        decoder: psyplot.CFDecoder
            The decoder that decodes the `base` dataset and is used to get
            bounds. If not given, a new :class:`CFDecoder` is created
        idims: dict
            Default: None. dictionary with integer values and/or slices in the
            `base` dictionary. If not given, they are determined automatically
        %(InteractiveBase.parameters)s
        """
        self.arr = xarray_obj
        super(InteractiveArray, self).__init__(*args, **kwargs)
        self._registered_updates = {}
        self._new_dims = {}
        self.method = None

    def init_accessor(self, base=None, idims=None, decoder=None,
                      *args, **kwargs):
        """
        Initialize the accessor instance

        This method initializes the accessor

        Parameters
        ----------
        base: xr.Dataset
            The base dataset for the data
        idims: dict
            A mapping from dimension name to indices. If not provided, it is
            calculated when the :attr:`idims` attribute is accessed
        decoder: CFDecoder
            The decoder of this object
        %(InteractiveBase.parameters)s
        """
        if base is not None:
            self.base = base
        self.idims = idims
        if decoder is not None:
            self.decoder = decoder
        super(InteractiveArray, self).__init__(*args, **kwargs)

    @property
    def iter_base_variables(self):
        """An iterator over the base variables in the :attr:`base` dataset"""
        if VARIABLELABEL in self.arr.coords:
            return (self._get_base_var(name) for name in safe_list(
                self.arr.coords[VARIABLELABEL].values.tolist()))
        name = self.arr.name
        if name is None:
            return iter([self.arr._variable])
        return iter([self.base.variables[name]])

    def _get_base_var(self, name):
        try:
            return self.base.variables[name]
        except KeyError:
            return self.arr.sel(**{VARIABLELABEL: name}).rename(name)

    @property
    def base_variables(self):
        """A mapping from the variable name to the variablein the :attr:`base`
        dataset."""
        if VARIABLELABEL in self.arr.coords:
            return OrderedDict([
                (name, self._get_base_var(name)) for name in safe_list(
                    self.arr.coords[VARIABLELABEL].values.tolist())])
        name = self.arr.name
        if name is None:
            return {name: self.arr._variable}
        else:
            return {self.arr.name: self.base.variables[self.arr.name]}

    docstrings.keep_params('setup_coords.parameters', 'dims')

    @docstrings.get_sections(base='InteractiveArray._register_update')
    @docstrings.dedent
    def _register_update(self, method='isel', replot=False, dims={}, fmt={},
                         force=False, todefault=False):
        """
        Register new dimensions and formatoptions for updating

        Parameters
        ----------
        method: {'isel', None, 'nearest', ...}
            Selection method of the xarray.Dataset to be used for setting the
            variables from the informations in `dims`.
            If `method` is 'isel', the :meth:`xarray.Dataset.isel` method is
            used. Otherwise it sets the `method` parameter for the
            :meth:`xarray.Dataset.sel` method.
        %(setup_coords.parameters.dims)s
        %(InteractiveBase._register_update.parameters)s

        See Also
        --------
        start_update"""
        if self._new_dims and self.method != method:
            raise ValueError(
                "New dimensions were already specified for with the %s method!"
                " I can not choose a new method %s" % (self.method, method))
        else:
            self.method = method
        if 'name' in dims:
            self._new_dims['name'] = dims.pop('name')
        if 'name' in self._new_dims:
            name = self._new_dims['name']
            if not isstring(name):
                name = name[0]  # concatenated array
            arr = self.base[name]
        else:
            arr= next(six.itervalues(self.base_variables))
        self._new_dims.update(self.decoder.correct_dims(arr, dims))
        InteractiveBase._register_update(
            self, fmt=fmt, replot=replot or bool(self._new_dims), force=force,
            todefault=todefault)

    def _update_concatenated(self, dims, method):
        """Updates a concatenated array to new dimensions"""

        def is_unequal(v1, v2):
            try:
                return bool(v1 != v2)
            except ValueError:  # arrays
                try:
                    (v1 == v2).all()
                except AttributeError:
                    return False

        def filter_attrs(item):
            """Checks whether the attribute is from the base variable"""
            return (item[0] not in self.base.attrs or
                    is_unequal(item[1], self.base.attrs[item[0]]))
        saved_attrs = list(filter(filter_attrs, six.iteritems(self.arr.attrs)))
        saved_name = self.arr.name
        self.arr.name = 'None'
        if 'name' in dims:
            name = dims.pop('name')
        else:
            name = list(self.arr.coords['variable'].values)
        base_dims = self.base[name].dims
        if method == 'isel':
            self.idims.update(dims)
            dims = self.idims
            for dim in set(base_dims) - set(dims):
                dims[dim] = slice(None)
            for dim in set(dims) - set(self.base[name].dims):
                del dims[dim]
            res = self.base[name].isel(**dims).to_array()
        else:
            self._idims = None
            for key, val in six.iteritems(self.arr.coords):
                if key in base_dims and key != 'variable':
                    dims.setdefault(key, val)
            kws = dims.copy()
            # the sel method does not work with slice objects
            if not any(isinstance(idx, slice) for idx in dims.values()):
                kws['method'] = method
            try:
                res = self.base[name].sel(**kws)
            except KeyError:
                _fix_times(kws)
                res = self.base[name].sel(**kws)
            res = res.to_array()
        if 'coordinates' in self.base[name[0]].encoding:
            res.encoding['coordinates'] = self.base[name[0]].encoding[
                'coordinates']
        self.arr._variable = res._variable
        self.arr._coords = res._coords
        try:
            self.arr._indexes = (
                res._indexes.copy() if res._indexes is not None else None)
        except AttributeError:  # res.indexes not existent for xr<0.12
            pass
        self.arr.name = saved_name
        for key, val in saved_attrs:
            self.arr.attrs[key] = val

    def _update_array(self, dims, method):
        """Updates the array to the new dims from then :attr:`base` dataset"""

        def is_unequal(v1, v2):
            try:
                return bool(v1 != v2)
            except ValueError:  # arrays
                try:
                    (v1 == v2).all()
                except AttributeError:
                    return False

        def filter_attrs(item):
            """Checks whether the attribute is from the base variable"""
            return (item[0] not in base_var.attrs or
                    is_unequal(item[1], base_var.attrs[item[0]]))

        base_var = self.base.variables[self.arr.name]
        if 'name' in dims:
            name = dims.pop('name')
            self.arr.name = name
        else:
            name = self.arr.name
        # save attributes that have been changed by the user
        saved_attrs = list(filter(filter_attrs, six.iteritems(self.arr.attrs)))
        if method == 'isel':
            self.idims.update(dims)
            dims = self.idims
            for dim in set(self.base[name].dims) - set(dims):
                dims[dim] = slice(None)
            for dim in set(dims) - set(self.base[name].dims):
                del dims[dim]
            res = self.base[name].isel(**dims)
        else:
            self._idims = None
            old_dims = self.arr.dims[:]
            for key, val in six.iteritems(self.arr.coords):
                if key in base_var.dims:
                    dims.setdefault(key, val)
            kws = dims.copy()
            # the sel method does not work with slice objects
            if not any(isinstance(idx, slice) for idx in dims.values()):
                kws['method'] = method
            try:
                res = self.base[name].sel(**kws)
            except KeyError:
                _fix_times(kws)
                res = self.base[name].sel(**kws)
            # squeeze the 0-dimensional dimensions
            res = res.isel(**{
                dim: 0 for i, dim in enumerate(res.dims) if (
                    res.shape[i] == 1 and dim not in old_dims)})
        self.arr._variable = res._variable
        self.arr._coords = res._coords
        try:
            self.arr._indexes = (
                res._indexes.copy() if res._indexes is not None else None)
        except AttributeError:  # res.indexes not existent for xr<0.12
            pass
        # update to old attributes
        for key, val in saved_attrs:
            self.arr.attrs[key] = val

    def shiftlon(self, central_longitude):
        """
        Shift longitudes and the data so that they match map projection region.

        Only valid for cylindrical/pseudo-cylindrical global projections and
        data on regular lat/lon grids. longitudes need to be 1D.

        Parameters
        ----------
        central_longitude
            center of map projection region

        References
        ----------
        This function is copied and taken from the
        :class:`mpl_toolkits.basemap.Basemap` class. The only difference is
        that we do not mask values outside the map projection region
        """
        if xr_version < (0, 10):
            raise NotImplementedError(
                "xarray>=0.10 is required for the shiftlon method!")
        arr = self.arr
        ret = arr.copy(True, arr.values.copy())
        if arr.ndim > 2:
            xname = self.get_dim('x')
            yname = self.get_dim('y')
            shapes = OrderedDict(
                [(dim, range(i)) for dim, i in zip(arr.dims, arr.shape)
                 if dim not in [xname, yname]])
            dims = list(shapes)
            for indexes in product(*shapes.values()):
                d = dict(zip(dims, indexes))
                shifted = ret[d].psy.shiftlon(central_longitude)
                ret[d] = shifted.values

            x = shifted.psy.get_coord('x')
            ret[x.name] = shifted[x.name].variable

            return ret

        lon = self.get_coord('x').variable
        xname = self.get_dim('x')
        ix = arr.dims.index(xname)
        lon = lon.copy(True, lon.values.copy())
        lonsin = lon.values
        datain = arr.values.copy()

        clon = np.asarray(central_longitude)

        if lonsin.ndim not in [1]:
            raise ValueError('1D longitudes required')
        elif clon.ndim:
            raise ValueError("Central longitude must be a scalar, not "
                             "%i-dimensional!" % clon.ndim)

        lonsin = np.where(lonsin > clon+180, lonsin-360, lonsin)
        lonsin = np.where(lonsin < clon-180, lonsin+360, lonsin)
        londiff = np.abs(lonsin[0:-1]-lonsin[1:])
        londiff_sort = np.sort(londiff)
        thresh = 360.-londiff_sort[-2]
        itemindex = len(lonsin) - np.where(londiff >= thresh)[0]
        if itemindex.size:
            # check to see if cyclic (wraparound) point included
            # if so, remove it.
            if np.abs(lonsin[0]-lonsin[-1]) < 1.e-4:
                hascyclic = True
                lonsin_save = lonsin.copy()
                lonsin = lonsin[1:]
                if datain is not None:
                    datain_save = datain.copy()
                    datain = datain[1:]
            else:
                hascyclic = False
            lonsin = np.roll(lonsin, itemindex-1)
            if datain is not None:
                datain = np.roll(datain, itemindex-1, [ix])
            # add cyclic point back at beginning.
            if hascyclic:
                lonsin_save[1:] = lonsin
                lonsin_save[0] = lonsin[-1]-360.
                lonsin = lonsin_save
                if datain is not None:
                    datain_save[1:] = datain
                    datain_save[0] = datain[-1]
                    datain = datain_save
        ret = ret.copy(True, datain)
        lon.values[:] = lonsin
        ret[lon.name] = lon
        return ret

    @docstrings.dedent
    def start_update(self, draw=None, queues=None):
        """
        Conduct the formerly registered updates

        This method conducts the updates that have been registered via the
        :meth:`update` method. You can call this method if the
        :attr:`no_auto_update` attribute of this instance is True and the
        `auto_update` parameter in the :meth:`update` method has been set to
        False

        Parameters
        ----------
        %(InteractiveBase.start_update.parameters)s

        Returns
        -------
        %(InteractiveBase.start_update.returns)s

        See Also
        --------
        :attr:`no_auto_update`, update
        """
        def filter_attrs(item):
            return (item[0] not in self.base.attrs or
                    item[1] != self.base.attrs[item[0]])
        if queues is not None:
            # make sure that no plot is updated during gathering the data
            queues[0].get()
        try:
            dims = self._new_dims
            method = self.method
            if dims:
                if VARIABLELABEL in self.arr.coords:
                    self._update_concatenated(dims, method)
                else:
                    self._update_array(dims, method)
            if queues is not None:
                queues[0].task_done()
            self._new_dims = {}
            self.onupdate.emit()
        except Exception:
            self._finish_all(queues)
            raise
        return InteractiveBase.start_update(self, draw=draw, queues=queues)

    @docstrings.get_sections(base='InteractiveArray.update',
                              sections=['Parameters', 'Notes'])
    @docstrings.dedent
    def update(self, method='isel', dims={}, fmt={}, replot=False,
               auto_update=False, draw=None, force=False, todefault=False,
               **kwargs):
        """
        Update the coordinates and the plot

        This method updates all arrays in this list with the given coordinate
        values and formatoptions.

        Parameters
        ----------
        %(InteractiveArray._register_update.parameters)s
        auto_update: bool
            Boolean determining whether or not the :meth:`start_update` method
            is called after the end.
        %(InteractiveBase.start_update.parameters)s
        ``**kwargs``
            Any other formatoption or dimension that shall be updated
            (additionally to those in `fmt` and `dims`)

        Notes
        -----
        When updating to a new array while trying to set the dimensions at the
        same time, you have to specify the new dimensions via the `dims`
        parameter, e.g.::

            da.psy.update(name='new_name', dims={'new_dim': 3})

        if ``'new_dim'`` is not yet a dimension of this array

        %(InteractiveBase.update.notes)s"""
        dims = dict(dims)
        fmt = dict(fmt)
        vars_and_coords = set(chain(
            self.arr.dims, self.arr.coords, ['name', 'x', 'y', 'z', 't']))
        furtherdims, furtherfmt = utils.sort_kwargs(kwargs, vars_and_coords)
        dims.update(furtherdims)
        fmt.update(furtherfmt)

        self._register_update(method=method, replot=replot, dims=dims,
                              fmt=fmt, force=force, todefault=todefault)

        if not self.no_auto_update or auto_update:
            self.start_update(draw=draw)

    def _short_info(self, intend=0, maybe=False):
        str_intend = ' ' * intend
        if 'variable' in self.arr.coords:
            name = ', '.join(self.arr.coords['variable'].values)
        else:
            name = self.arr.name
        if self.arr.ndim > 0:
            dims = ', with (%s)=%s' % (', '.join(self.arr.dims),
                                       self.arr.shape)
        else:
            dims = ''
        return str_intend + "%s: %i-dim %s of %s%s, %s" % (
            self.arr_name, self.arr.ndim, self.arr.__class__.__name__, name,
            dims, ", ".join(
                "%s=%s" % (coord, format_item(val.values))
                for coord, val in six.iteritems(self.arr.coords)
                if val.ndim == 0))

    def __getitem__(self, key):
        ret = self.arr.__getitem__(key)
        ret.psy._base = self.base
        return ret

    def isel(self, *args, **kwargs):
        # reimplemented to keep the base. The doc is set below
        ret = self.arr.isel(*args, **kwargs)
        ret.psy._base = self._base
        return ret

    def sel(self, *args, **kwargs):
        # reimplemented to keep the base. The doc is set below
        ret = self.arr.sel(*args, **kwargs)
        ret.psy._base = self._base
        return ret

    def copy(self, deep=False):
        """Copy the array

        This method returns a copy of the underlying array in the :attr:`arr`
        attribute. It is more stable because it creates a new `psy` accessor"""
        arr = self.arr.copy(deep)
        try:
            arr.psy = InteractiveArray(arr)
        except AttributeError:  # attribute is read-only for xarray >=0.13
            pass
        return arr

    def to_interactive_list(self):
        return InteractiveList([self], arr_name=self.arr_name)

    @docstrings.get_sections(base='InteractiveArray.get_coord')
    @docstrings.dedent
    def get_coord(self, what, base=False):
        """
        The x-coordinate of this data array

        Parameters
        ----------
        what: {'t', 'x', 'y', 'z'}
            The letter of the axis
        base: bool
            If True, use the base variable in the :attr:`base` dataset."""
        what = what.lower()
        return getattr(self.decoder, 'get_' + what)(
            next(six.itervalues(self.base_variables)) if base else self.arr,
            self.arr.coords)

    @docstrings.dedent
    def get_dim(self, what, base=False):
        """
        The name of the x-dimension of this data array

        Parameters
        ----------
        %(InteractiveArray.get_coord.parameters)s"""
        what = what.lower()
        return getattr(self.decoder, 'get_%sname' % what)(
            next(six.itervalues(self.base_variables)) if base else self.arr)

    # ------------------ Calculations -----------------------------------------

    def _gridweights(self):
        """Calculate the gridweights with a simple rectangular approximation"""
        arr = self.arr
        xcoord = self.get_coord('x')
        ycoord = self.get_coord('y')
        # convert the units
        xcoord_orig = xcoord
        ycoord_orig = ycoord
        units = xcoord.attrs.get('units', '')
        in_metres = False
        in_degree = False
        if 'deg' in units or (
                'rad' not in units and 'lon' in xcoord.name and
                'lat' in ycoord.name):
            xcoord = xcoord * np.pi / 180
            ycoord = ycoord * np.pi / 180
            in_degree = True
        elif 'rad' in units:
            pass
        else:
            in_metres = True

        # calculate the gridcell boundaries
        xbounds = self.decoder.get_plotbounds(xcoord, arr.coords)
        ybounds = self.decoder.get_plotbounds(ycoord, arr.coords)
        if xbounds.ndim == 1:
            xbounds, ybounds = np.meshgrid(xbounds, ybounds)

        # calculate the weights based on the units
        if xcoord.ndim == 2 or self.decoder.is_unstructured(self.arr):
            warn("[%s] - Curvilinear grids are not supported! "
                 "Using constant grid cell area weights!" % self.logger.name,
                 PsyPlotRuntimeWarning)
            weights = np.ones_like(xcoord.values)
        elif in_metres:
            weights = np.abs(xbounds[:-1, :-1] - xbounds[1:, 1:]) * (
                np.abs(ybounds[:-1, :-1] - ybounds[1:, 1:]))
        else:
            weights = np.abs(xbounds[:-1, :-1] - xbounds[1:, 1:]) * (
                np.sin(ybounds[:-1, :-1]) - np.sin(ybounds[1:, 1:]))

        # normalize the weights by dividing through the sum
        if in_degree:
            xmask = (xcoord_orig.values < -400) | (xcoord_orig.values > 400)
            ymask = (ycoord_orig.values < -200) | (ycoord_orig.values > 200)
            if xmask.any() or ymask.any():
                if xmask.ndim == 1 and weights.ndim != 1:
                    xmask, ymask = np.meshgrid(xmask, ymask)
                weights[xmask | ymask] = np.nan
        if np.any(~np.isnan(weights)):
            weights /= np.nansum(weights)
        return weights

    def _gridweights_cdo(self):
        """Estimate the gridweights using CDOs"""
        from cdo import Cdo
        from tempfile import NamedTemporaryFile
        sdims = {self.get_dim('y'), self.get_dim('x')}
        cdo = Cdo()
        fname = NamedTemporaryFile(prefix='psy', suffix='.nc').name
        arr = self.arr
        base = arr.psy.base
        dims = arr.dims
        ds = arr.isel(**{d: 0 for d in set(dims) - sdims}).to_dataset()
        for coord in six.itervalues(ds.coords):
            bounds = coord.attrs.get('bounds', coord.encoding.get('bounds'))
            if (bounds and bounds in set(base.coords) - set(ds.coords) and
                    sdims.intersection(base.coords[bounds].dims)):
                ds[bounds] = base.sel(
                    **{d: arr.coords[d].values for d in sdims}
                    ).coords[bounds]
            ds = ds.drop_vars([c.name for c in six.itervalues(ds.coords)
                               if not c.ndim])
        to_netcdf(ds, fname)
        ret = cdo.gridweights(input=fname, returnArray='cell_weights')
        try:
            os.remove(fname)
        except Exception:
            pass
        return ret

    def _weights_to_da(self, weights, keepdims=False, keepshape=False):
        """Convert the 2D weights into a DataArray and potentially enlarge it
        """
        arr = self.arr
        xcoord = self.get_coord('x')
        ycoord = self.get_coord('y')
        sdims = (self.get_dim('y'), self.get_dim('x'))
        if sdims[0] == sdims[1]:   # unstructured grids
            sdims = sdims[:1]
        if (ycoord.name, xcoord.name) != sdims:
            attrs = dict(coordinates=ycoord.name + ' ' + xcoord.name)
        else:
            attrs = {}

        # reshape and expand if necessary
        if not keepdims and not keepshape:
            coords = {ycoord.name: ycoord, xcoord.name: xcoord}
            dims = sdims
        elif keepshape:
            if with_dask:
                from dask.array import broadcast_to, notnull
            else:
                from numpy import broadcast_to, isnan

                def notnull(a):
                    return ~isnan(a)

            dims = arr.dims
            coords = arr.coords
            weights = broadcast_to(weights / weights.sum(), arr.shape)
            # set nans to zero weigths. This step takes quite a lot of time for
            # large arrays since it involves a copy of the entire `arr`
            weights = weights * notnull(arr)
            # normalize the weights
            if with_dask:
                summed_weights = weights.sum(
                    axis=tuple(map(dims.index, sdims)), keepdims=True
                )
            else:
                summed_weights = weights.sum(
                    axis=tuple(map(dims.index, sdims))
                )
            weights = weights / summed_weights
        else:
            dims = arr.dims
            coords = arr.isel(
                **{d: 0 if d not in sdims else slice(None)
                   for d in dims}).coords
            weights = weights.reshape(
                tuple(1 if dim not in sdims else s
                      for s, dim in zip(arr.shape, arr.dims)))
        return xr.DataArray(weights, dims=dims, coords=coords,
                            name='cell_weights', attrs=attrs)

    def gridweights(self, keepdims=False, keepshape=False, use_cdo=None):
        """Calculate the cell weights for each grid cell

        Parameters
        ----------
        keepdims: bool
            If True, keep the number of dimensions
        keepshape: bool
            If True, keep the exact shape as the source array and the missing
            values in the array are masked
        use_cdo: bool or None
            If True, use Climate Data Operators (CDOs) to calculate the
            weights. Note that this is used automatically for unstructured
            grids. If None, it depends on the ``'gridweights.use_cdo'``
            item in the :attr:`psyplot.rcParams`.

        Returns
        -------
        xarray.DataArray
            The 2D-DataArray with the grid weights"""
        if use_cdo is None:
            use_cdo = rcParams['gridweights.use_cdo']
        if not use_cdo and self.decoder.is_unstructured(self.arr):
            use_cdo = True
        if use_cdo is None or use_cdo:
            try:
                weights = self._gridweights_cdo()
            except Exception:
                if use_cdo:
                    raise
                else:
                    weights = self._gridweights()
        else:
            weights = self._gridweights()

        return self._weights_to_da(weights, keepdims=keepdims,
                                   keepshape=keepshape)

    def _fldaverage_args(self):
        """Masked array, xname, yname and axis for calculating the average"""
        arr = self.arr
        sdims = (self.get_dim('y'), self.get_dim('x'))
        if sdims[0] == sdims[1]:
            sdims = sdims[:1]
        axis = tuple(map(arr.dims.index, sdims))
        return arr, sdims, axis

    def _insert_fldmean_bounds(self, da, keepdims=False):
        xcoord = self.get_coord('x')
        ycoord = self.get_coord('y')
        sdims = (self.get_dim('y'), self.get_dim('x'))
        xbounds = np.array([[xcoord.min(), xcoord.max()]])
        ybounds = np.array([[ycoord.min(), ycoord.max()]])
        xdims = (sdims[-1], 'bnds') if keepdims else ('bnds', )
        ydims = (sdims[0], 'bnds') if keepdims else ('bnds', )
        xattrs = xcoord.attrs.copy()
        xattrs.pop('bounds', None)
        yattrs = ycoord.attrs.copy()
        yattrs.pop('bounds', None)
        da.psy.base.coords[xcoord.name + '_bnds'] = xr.Variable(
            xdims, xbounds if keepdims else xbounds[0], attrs=xattrs)
        da.psy.base.coords[ycoord.name + '_bnds'] = xr.Variable(
            ydims, ybounds if keepdims else ybounds[0], attrs=yattrs)

    def fldmean(self, keepdims=False):
        """Calculate the weighted mean over the x- and y-dimension

        This method calculates the weighted mean of the spatial dimensions.
        Weights are calculated using the :meth:`gridweights` method, missing
        values are ignored. x- and y-dimensions are identified using the
        :attr:`decoder`s :meth:`~CFDecoder.get_xname` and
        :meth:`~CFDecoder.get_yname` methods.

        Parameters
        ----------
        keepdims: bool
            If True, the dimensionality of this array is maintained

        Returns
        -------
        xr.DataArray
            The computed fldmeans. The dimensions are the same as in this
            array, only the spatial dimensions are omitted if `keepdims` is
            False.

        See Also
        --------
        fldstd: For calculating the weighted standard deviation
        fldpctl: For calculating weighted percentiles
        """
        gridweights = self.gridweights()
        arr, sdims, axis = self._fldaverage_args()

        xcoord = self.decoder.get_x(next(six.itervalues(self.base_variables)),
                                    arr.coords)
        ycoord = self.decoder.get_y(next(six.itervalues(self.base_variables)),
                                    arr.coords)
        means = ((arr * gridweights)).sum(axis=axis) * (
            gridweights.size / arr.notnull().sum(axis=axis))
        if keepdims:
            means = means.expand_dims(sdims, axis=axis)

        if keepdims:
            means[xcoord.name] = xcoord.mean().expand_dims(xcoord.dims[0])
            means[ycoord.name] = ycoord.mean().expand_dims(ycoord.dims[0])
        else:
            means[xcoord.name] = xcoord.mean()
            means[ycoord.name] = ycoord.mean()
        means.coords[xcoord.name].attrs['bounds'] = xcoord.name + '_bnds'
        means.coords[ycoord.name].attrs['bounds'] = ycoord.name + '_bnds'
        self._insert_fldmean_bounds(means, keepdims)
        means.name = arr.name
        return means

    def fldstd(self, keepdims=False):
        """Calculate the weighted standard deviation over x- and y-dimension

        This method calculates the weighted standard deviation of the spatial
        dimensions. Weights are calculated using the :meth:`gridweights`
        method, missing values are ignored. x- and y-dimensions are identified
        using the :attr:`decoder`s :meth:`~CFDecoder.get_xname` and
        :meth:`~CFDecoder.get_yname` methods.

        Parameters
        ----------
        keepdims: bool
            If True, the dimensionality of this array is maintained

        Returns
        -------
        xr.DataArray
            The computed standard deviations. The dimensions are the same as
            in this array, only the spatial dimensions are omitted if
            `keepdims` is  False.

        See Also
        --------
        fldmean: For calculating the weighted mean
        fldpctl: For calculating weighted percentiles
        """
        arr, sdims, axis = self._fldaverage_args()
        means = self.fldmean(keepdims=True)
        weights = self.gridweights(keepshape=True)
        variance = ((arr - means.values)**2 * weights).sum(axis=axis)
        if keepdims:
            variance = variance.expand_dims(sdims, axis=axis)
        for key, coord in six.iteritems(means.coords):
            if key not in variance.coords:
                dims = set(sdims).intersection(coord.dims)
                variance[key] = coord if keepdims else coord.isel(
                    **dict(zip(dims, repeat(0))))
        for key, coord in six.iteritems(means.psy.base.coords):
            if key not in variance.psy.base.coords:
                dims = set(sdims).intersection(coord.dims)
                variance.psy.base[key] = coord if keepdims else coord.isel(
                    **dict(zip(dims, repeat(0))))
        std = variance**0.5
        std.name = arr.name
        return std

    def fldpctl(self, q, keepdims=False):
        """Calculate the percentiles along the x- and y-dimensions

        This method calculates the specified percentiles along the given
        dimension. Percentiles are weighted by the :meth:`gridweights` method
        and missing values are ignored. x- and y-dimensions are estimated
        through the :attr:`decoder`s :meth:`~CFDecoder.get_xname` and
        :meth:`~CFDecoder.get_yname` methods

        Parameters
        ----------
        q: float or list of floats between 0 and 100
            The quantiles to estimate
        keepdims: bool
            If True, the number of dimensions of the array are maintained

        Returns
        -------
        xr.DataArray
            The data array with the dimensions. If `q` is a list or `keepdims`
            is True, the first dimension will be the percentile ``'pctl'``.
            The other dimensions are the same as in this array, only the
            spatial dimensions are omitted if `keepdims` is False.

        See Also
        --------
        fldstd: For calculating the weighted standard deviation
        fldmean: For calculating the weighted mean

        Warnings
        --------
        This method does load the entire array into memory! So take care if you
        handle big data."""
        gridweights = self.gridweights(keepshape=True)
        arr = self.arr

        q = np.asarray(q) / 100.
        if not (np.all(q >= 0) and np.all(q <= 100)):
            raise ValueError('q should be in [0, 100]')
        reduce_shape = False if keepdims else (not bool(q.ndim))
        if not q.ndim:
            q = q[np.newaxis]
        data = arr.values.copy()
        sdims, axis = self._fldaverage_args()[1:]
        weights = gridweights.values
        # flatten along the spatial axis
        for ax in axis:
            data = np.rollaxis(data, ax, 0)
            weights = np.rollaxis(weights, ax, 0)
        data = data.reshape(
            (np.product(data.shape[:len(axis)]), ) + data.shape[len(axis):])
        weights = weights.reshape(
            (np.product(weights.shape[:len(axis)]), ) +
            weights.shape[len(axis):])

        # sort the data
        sorter = np.argsort(data, axis=0)
        all_indices = map(tuple, product(*map(range, data.shape[1:])))
        for indices in all_indices:
            indices = (slice(None), ) + indices
            data.__setitem__(
                indices, data.__getitem__(indices)[
                    sorter.__getitem__(indices)])
            weights.__setitem__(
                indices, weights.__getitem__(indices)[
                    sorter.__getitem__(indices)])

        # compute the percentiles
        try:
            weights = np.nancumsum(weights, axis=0) - 0.5 * weights
        except AttributeError:
            notnull = ~np.isnan(weights)
            weights[notnull] = np.cumsum(weights[notnull])
        all_indices = map(tuple, product(*map(range, data.shape[1:])))
        pctl = np.zeros((len(q), ) + data.shape[1:])

        for indices in all_indices:
            indices = (slice(None), ) + indices
            mask = ~np.isnan(data.__getitem__(indices))
            pctl.__setitem__(indices, np.interp(
                q, weights.__getitem__(indices)[mask],
                data.__getitem__(indices)[mask]))

        # setup the data array and it's coordinates
        xcoord = self.decoder.get_x(next(six.itervalues(self.base_variables)),
                                    arr.coords)
        ycoord = self.decoder.get_y(next(six.itervalues(self.base_variables)),
                                    arr.coords)
        coords = dict(arr.coords)
        if keepdims:
            pctl = pctl.reshape(
                (len(q), ) +
                tuple(1 if i in axis else s for i, s in enumerate(arr.shape)))
            coords[xcoord.name] = xcoord.mean().expand_dims(xcoord.dims[0])
            coords[ycoord.name] = ycoord.mean().expand_dims(ycoord.dims[0])
            dims = arr.dims
        else:
            coords[xcoord.name] = xcoord.mean()
            coords[ycoord.name] = ycoord.mean()
            dims = tuple(d for d in arr.dims if d not in sdims)
        if reduce_shape:
            pctl = pctl[0]
            coords['pctl'] = xr.Variable((), q[0] * 100.,
                                         attrs={'long_name': 'Percentile'})
        else:
            coords['pctl'] = xr.Variable(('pctl', ), q * 100.,
                                         attrs={'long_name': 'Percentile'})
            dims = ('pctl', ) + dims
        coords[xcoord.name].attrs['bounds'] = xcoord.name + '_bnds'
        coords[ycoord.name].attrs['bounds'] = ycoord.name + '_bnds'
        coords = {name: c for name, c in coords.items()
                  if set(c.dims) <= set(dims)}
        ret = xr.DataArray(pctl, name=arr.name, dims=dims, coords=coords,
                           attrs=arr.attrs.copy())
        self._insert_fldmean_bounds(ret, keepdims)
        return ret

    isel.__doc__ = xr.DataArray.isel.__doc__
    sel.__doc__ = xr.DataArray.sel.__doc__


class ArrayList(list):
    """Base class for creating a list of interactive arrays from a dataset

    This list contains and manages :class:`InteractiveArray` instances"""

    docstrings.keep_params('InteractiveBase.parameters', 'auto_update')

    @property
    def dims(self):
        """Dimensions of the arrays in this list"""
        return set(chain(*(arr.dims for arr in self)))

    @property
    def dims_intersect(self):
        """Dimensions of the arrays in this list that are used in all arrays
        """
        return set.intersection(*map(
            set, (getattr(arr, 'dims_intersect', arr.dims) for arr in self)))

    @property
    def arr_names(self):
        """Names of the arrays (!not of the variables!) in this list

        This attribute can be set with an iterable of unique names to change
        the array names of the data objects in this list."""
        return list(arr.psy.arr_name for arr in self)

    @arr_names.setter
    def arr_names(self, value):
        value = list(islice(value, 0, len(self)))
        if not len(set(value)) == len(self):
            raise ValueError(
                "Got %i unique array names for %i data objects!" % (
                    len(set(value)), len(self)))
        for arr, n in zip(self, value):
            arr.psy.arr_name = n

    @property
    def names(self):
        """Set of the variable in this list"""
        ret = set()
        for arr in self:
            if isinstance(arr, InteractiveList):
                ret.update(arr.names)
            else:
                ret.add(arr.name)
        return ret

    @property
    def all_names(self):
        """The variable names for each of the arrays in this list"""
        return [
            _get_variable_names(arr) if not isinstance(arr, ArrayList) else
            arr.all_names
            for arr in self]

    @property
    def all_dims(self):
        """The dimensions for each of the arrays in this list"""
        return [
            _get_dims(arr) if not isinstance(arr, ArrayList) else
            arr.all_dims
            for arr in self]

    @property
    def is_unstructured(self):
        """A boolean for each array whether it is unstructured or not"""
        return [
            arr.psy.decoder.is_unstructured(arr)
            if not isinstance(arr, ArrayList) else
            arr.is_unstructured
            for arr in self]

    @property
    def coords(self):
        """Names of the coordinates of the arrays in this list"""
        return set(chain(*(arr.coords for arr in self)))

    @property
    def coords_intersect(self):
        """Coordinates of the arrays in this list that are used in all arrays
        """
        return set.intersection(*map(
            set, (getattr(arr, 'coords_intersect', arr.coords) for arr in self)
            ))

    @property
    def with_plotter(self):
        """The arrays in this instance that are visualized with a plotter"""
        return self.__class__(
            (arr for arr in self if arr.psy.plotter is not None),
            auto_update=bool(self.auto_update))

    no_auto_update = property(_no_auto_update_getter,
                              doc=_no_auto_update_getter.__doc__)

    @no_auto_update.setter
    def no_auto_update(self, value):
        for arr in self:
            arr.psy.no_auto_update = value
        self.no_auto_update.value = bool(value)

    @property
    def logger(self):
        """:class:`logging.Logger` of this instance"""
        try:
            return self._logger
        except AttributeError:
            name = '%s.%s' % (self.__module__, self.__class__.__name__)
            self._logger = logging.getLogger(name)
            self.logger.debug('Initializing...')
            return self._logger

    @logger.setter
    def logger(self, value):
        self._logger = value

    @property
    def arrays(self):
        """A list of all the :class:`xarray.DataArray` instances in this list
        """
        return list(chain.from_iterable(
            ([arr] if not isinstance(arr, InteractiveList) else arr.arrays
             for arr in self)))

    @docstrings.get_sections(base='ArrayList.rename', sections=[
        'Parameters', 'Raises'])
    @dedent
    def rename(self, arr, new_name=True):
        """
        Rename an array to find a name that isn't already in the list

        Parameters
        ----------
        arr: InteractiveBase
            A :class:`InteractiveArray` or :class:`InteractiveList` instance
            whose name shall be checked
        new_name: bool or str
            If False, and the ``arr_name`` attribute of the new array is
            already in the list, a ValueError is raised.
            If True and the ``arr_name`` attribute of the new array is not
            already in the list, the name is not changed. Otherwise, if the
            array name is already in use, `new_name` is set to 'arr{0}'.
            If not True, this will be used for renaming (if the array name of
            `arr` is in use or not). ``'{0}'`` is replaced by a counter

        Returns
        -------
        InteractiveBase
            `arr` with changed ``arr_name`` attribute
        bool or None
            True, if the array has been renamed, False if not and None if the
            array is already in the list

        Raises
        ------
        ValueError
            If it was impossible to find a name that isn't already  in the list
        ValueError
            If `new_name` is False and the array is already in the list"""
        name_in_me = arr.psy.arr_name in self.arr_names
        if not name_in_me:
            return arr, False
        elif name_in_me and not self._contains_array(arr):
            if new_name is False:
                raise ValueError(
                    "Array name %s is already in use! Set the `new_name` "
                    "parameter to None for renaming!" % arr.psy.arr_name)
            elif new_name is True:
                new_name = new_name if isstring(new_name) else 'arr{0}'
                arr.psy.arr_name = self.next_available_name(new_name)
                return arr, True
        return arr, None

    docstrings.keep_params('ArrayList.rename.parameters', 'new_name')
    docstrings.keep_params('InteractiveBase.parameters', 'auto_update')

    @docstrings.get_sections(base='ArrayList')
    @docstrings.dedent
    def __init__(self, iterable=[], attrs={}, auto_update=None, new_name=True):
        """
        Parameters
        ----------
        iterable: iterable
            The iterable (e.g. another list) defining this list
        attrs: dict-like or iterable, optional
            Global attributes of this list
        %(InteractiveBase.parameters.auto_update)s
        %(ArrayList.rename.parameters.new_name)s"""
        super(ArrayList, self).__init__()
        self.attrs = OrderedDict(attrs)
        if auto_update is None:
            auto_update = rcParams['lists.auto_update']
        self.auto_update = not bool(auto_update)
        # append the data in order to set the correct names
        self.extend(filter(
            lambda arr: isinstance(getattr(arr, 'psy', None),
                                   InteractiveBase),
            iterable), new_name=new_name)

    def copy(self, deep=False):
        """Returns a copy of the list

        Parameters
        ----------
        deep: bool
            If False (default), only the list is copied and not the contained
            arrays, otherwise the contained arrays are deep copied"""
        if not deep:
            return self.__class__(self[:], attrs=self.attrs.copy(),
                                  auto_update=not bool(self.no_auto_update))
        else:
            return self.__class__(
                [arr.psy.copy(deep) for arr in self], attrs=self.attrs.copy(),
                auto_update=not bool(self.auto_update))

    docstrings.keep_params('InteractiveArray.update.parameters', 'method')

    @classmethod
    @docstrings.get_sections(base='ArrayList.from_dataset', sections=[
        'Parameters', 'Other Parameters', 'Returns'])
    @docstrings.dedent
    def from_dataset(cls, base, method='isel', default_slice=None,
                     decoder=None, auto_update=None, prefer_list=False,
                     squeeze=True, attrs=None, load=False, **kwargs):
        """
        Construct an ArrayList instance from an existing base dataset

        Parameters
        ----------
        base: xarray.Dataset
            Dataset instance that is used as reference
        %(InteractiveArray.update.parameters.method)s
        %(InteractiveBase.parameters.auto_update)s
        prefer_list: bool
            If True and multiple variable names pher array are found, the
            :class:`InteractiveList` class is used. Otherwise the arrays are
            put together into one :class:`InteractiveArray`.
        default_slice: indexer
            Index (e.g. 0 if `method` is 'isel') that shall be used for
            dimensions not covered by `dims` and `furtherdims`. If None, the
            whole slice will be used. Note that the `default_slice` is always
            based on the `isel` method.
        decoder: CFDecoder or dict
            Arguments for the decoder. This can be one of

            - an instance of :class:`CFDecoder`
            - a subclass of :class:`CFDecoder`
            - a dictionary with keyword-arguments to the automatically
              determined decoder class
            - None to automatically set the decoder
        squeeze: bool, optional
            Default True. If True, and the created arrays have a an axes with
            length 1, it is removed from the dimension list (e.g. an array
            with shape (3, 4, 1, 5) will be squeezed to shape (3, 4, 5))
        attrs: dict, optional
            Meta attributes that shall be assigned to the selected data arrays
            (additional to those stored in the `base` dataset)
        load: bool or dict
            If True, load the data from the dataset using the
            :meth:`xarray.DataArray.load` method. If :class:`dict`, those will
            be given to the above mentioned ``load`` method

        Other Parameters
        ----------------
        %(setup_coords.parameters)s

        Returns
        -------
        ArrayList
            The list with the specified :class:`InteractiveArray` instances
            that hold a reference to the given `base`"""
        try:
            load = dict(load)
        except (TypeError, ValueError):
            def maybe_load(arr):
                return arr.load() if load else arr
        else:
            def maybe_load(arr):
                return arr.load(**load)

        def iter_dims(dims):
            """Split the given dictionary into multiples and iterate over it"""
            if not dims:
                while 1:
                    yield {}
            else:
                dims = OrderedDict(dims)
                keys = dims.keys()
                for vals in zip(*map(cycle, map(safe_list, dims.values()))):
                    yield dict(zip(keys, vals))

        def recursive_selection(key, dims, names):
            names = safe_list(names)
            if len(names) > 1 and prefer_list:
                keys = ('arr%i' % i for i in range(len(names)))
                return InteractiveList(
                    starmap(sel_method, zip(keys, iter_dims(dims), names)),
                    auto_update=auto_update, arr_name=key)
            elif len(names) > 1:
                return sel_method(key, dims, tuple(names))
            else:
                return sel_method(key, dims, names[0])

        def ds2arr(arr):
            base_var = next(var for key, var in arr.variables.items()
                            if key not in arr.coords)
            attrs = base_var.attrs
            arr = arr.to_array()
            if 'coordinates' in base_var.encoding:
                arr.encoding['coordinates'] = base_var.encoding[
                    'coordinates']
            arr.attrs.update(attrs)
            return arr

        decoder_input = decoder

        def get_decoder(arr):
            if decoder_input is None:
                return CFDecoder.get_decoder(base, arr)
            elif isinstance(decoder_input, CFDecoder):
                return decoder_input
            elif isinstance(decoder_input, dict):
                return CFDecoder.get_decoder(base, arr, **decoder_input)
            else:
                return decoder_input(base)

        def add_missing_dimensions(arr):
            # add the missing dimensions to the dataset. This is not anymore
            # done by default from xarray >= 0.9 but we need it to ensure the
            # interactive treatment of DataArrays
            missing = set(arr.dims).difference(base.coords) - {'variable'}
            for dim in missing:
                base[dim] = arr.coords[dim] = np.arange(base.dims[dim])

        if squeeze:
            def squeeze_array(arr):
                return arr.isel(**{dim: 0 for i, dim in enumerate(arr.dims)
                                   if arr.shape[i] == 1})
        else:
            def squeeze_array(arr):
                return arr
        if method == 'isel':
            def sel_method(key, dims, name=None):
                if name is None:
                    return recursive_selection(key, dims, dims.pop('name'))
                elif (isinstance(name, six.string_types) or
                      not utils.is_iterable(name)):
                    arr = base[name]
                    decoder = get_decoder(arr)
                    dims = decoder.correct_dims(arr, dims)
                else:
                    arr = base[list(name)]
                    decoder = get_decoder(base[name[0]])
                    dims = decoder.correct_dims(base[name[0]], dims)
                def_slice = slice(None) if default_slice is None else \
                    default_slice
                dims.update({
                    dim: def_slice for dim in set(arr.dims).difference(
                        dims) if dim != 'variable'})
                add_missing_dimensions(arr)
                ret = arr.isel(**dims)
                if not isinstance(ret, xr.DataArray):
                    ret = ds2arr(ret)
                ret = squeeze_array(ret)
                # delete the variable dimension for the idims
                dims.pop('variable', None)
                ret.psy.init_accessor(arr_name=key, base=base, idims=dims,
                                      decoder=decoder)
                return maybe_load(ret)
        else:
            def sel_method(key, dims, name=None):
                if name is None:
                    return recursive_selection(key, dims, dims.pop('name'))
                elif (isinstance(name, six.string_types) or
                      not utils.is_iterable(name)):
                    arr = base[name]
                    decoder = get_decoder(arr)
                    dims = decoder.correct_dims(arr, dims)
                else:
                    arr = base[list(name)]
                    decoder = get_decoder(base[name[0]])
                    dims = decoder.correct_dims(base[name[0]], dims)
                if default_slice is not None:
                    if isinstance(default_slice, slice):
                        dims.update({
                            dim: default_slice
                            for dim in set(arr.dims).difference(dims)
                            if dim != 'variable'})
                    else:
                        dims.update({
                            dim: arr.coords[dim][default_slice]
                            for dim in set(arr.dims).difference(dims)
                            if dim != 'variable'})
                kws = dims.copy()
                kws['method'] = method
                # the sel method does not work with slice objects
                for dim, val in dims.items():
                    if isinstance(val, slice):
                        if val == slice(None):
                            kws.pop(dim)  # the full slice is the default
                        else:
                            kws.pop("method", None)
                add_missing_dimensions(arr)
                try:
                    ret = arr.sel(**kws)
                except KeyError:
                    _fix_times(kws)
                    ret = arr.sel(**kws)
                if not isinstance(ret, xr.DataArray):
                    ret = ds2arr(ret)
                ret = squeeze_array(ret)
                ret.psy.init_accessor(arr_name=key, base=base, decoder=decoder)
                return maybe_load(ret)
        if 'name' not in kwargs:
            default_names = list(
                key for key in base.variables if key not in base.coords)
            try:
                default_names.sort()
            except TypeError:
                pass
            kwargs['name'] = default_names
        names = setup_coords(**kwargs)
        # check coordinates
        possible_keys = ['t', 'x', 'y', 'z', 'name'] + list(base.dims)
        for key in set(chain(*six.itervalues(names))):
            utils.check_key(key, possible_keys, name='dimension')
        instance = cls(starmap(sel_method, six.iteritems(names)),
                       attrs=base.attrs, auto_update=auto_update)
        # convert to interactive lists if an instance is not
        if prefer_list and any(
                not isinstance(arr, InteractiveList) for arr in instance):
            # if any instance is an interactive list, than convert the others
            if any(isinstance(arr, InteractiveList) for arr in instance):
                for i, arr in enumerate(instance):
                    if not isinstance(arr, InteractiveList):
                        instance[i] = InteractiveList([arr])
            else:  # put everything into one single interactive list
                instance = cls([InteractiveList(instance, attrs=base.attrs,
                                                auto_update=auto_update)])
                instance[0].psy.arr_name = instance[0][0].psy.arr_name
        if attrs is not None:
            for arr in instance:
                arr.attrs.update(attrs)
        return instance

    @classmethod
    def _get_dsnames(cls, data, ignore_keys=['attrs', 'plotter', 'ds'],
                     concat_dim=False, combine=False):
        """Recursive method to get all the file names out of a dictionary
        `data` created with the :meth`array_info` method"""
        def filter_ignores(item):
            return item[0] not in ignore_keys and isinstance(item[1], dict)
        if 'fname' in data:
            return {tuple(
                [data['fname'], data['store']] +
                ([data.get('concat_dim')] if concat_dim else []) +
                ([data.get('combine')] if combine else []))}
        return set(chain(*map(partial(cls._get_dsnames, concat_dim=concat_dim,
                                      combine=combine,
                                      ignore_keys=ignore_keys),
                              dict(filter(filter_ignores,
                                          six.iteritems(data))).values())))

    @classmethod
    def _get_ds_descriptions(
            cls, data, ds_description={'ds', 'fname', 'arr'}, **kwargs):
        def new_dict():
            return defaultdict(list)
        ret = defaultdict(new_dict)
        ds_description = set(ds_description)
        for d in cls._get_ds_descriptions_unsorted(data, **kwargs):
            try:
                num = d.get('num') or d['ds'].psy.num
            except KeyError:
                raise ValueError(
                    'Could not find either the dataset number nor the dataset '
                    'in the data! However one must be provided.')
            d_ret = ret[num]
            for key, val in six.iteritems(d):
                if key == 'arr':
                    d_ret['arr'].append(d['arr'])
                else:
                    d_ret[key] = val
        return ret

    @classmethod
    def _get_ds_descriptions_unsorted(
            cls, data, ignore_keys=['attrs', 'plotter'], nums=None):
        """Recursive method to get all the file names or datasets out of a
        dictionary `data` created with the :meth`array_info` method"""
        ds_description = {'ds', 'fname', 'num', 'arr', 'store'}
        if 'ds' in data:
            # make sure that the data set has a number assigned to it
            data['ds'].psy.num
        keys_in_data = ds_description.intersection(data)
        if keys_in_data:
            return {key: data[key] for key in keys_in_data}
        for key in ignore_keys:
            data.pop(key, None)
        func = partial(cls._get_ds_descriptions_unsorted,
                       ignore_keys=ignore_keys, nums=nums)
        return chain(*map(lambda d: [d] if isinstance(d, dict) else d,
                          map(func, six.itervalues(data))))

    @classmethod
    @docstrings.get_sections(base='ArrayList.from_dict')
    @docstrings.dedent
    def from_dict(cls, d, alternative_paths={}, datasets=None,
                  pwd=None, ignore_keys=['attrs', 'plotter', 'ds'],
                  only=None, chname={}, **kwargs):
        """
        Create a list from the dictionary returned by :meth:`array_info`

        This classmethod creates an :class:`~psyplot.data.ArrayList` instance
        from a dictionary containing filename, dimension infos and array names

        Parameters
        ----------
        d: dict
            The dictionary holding the data
        alternative_paths: dict or list or str
            A mapping from original filenames as used in `d` to filenames that
            shall be used instead. If `alternative_paths` is not None,
            datasets must be None. Paths must be accessible from the current
            working directory.
            If `alternative_paths` is a list (or any other iterable) is
            provided, the file names will be replaced as they appear in `d`
            (note that this is very unsafe if `d` is not and OrderedDict)
        datasets: dict or list or None
            A mapping from original filenames in `d` to the instances of
            :class:`xarray.Dataset` to use. If it is an iterable, the same
            holds as for the `alternative_paths` parameter
        pwd: str
            Path to the working directory from where the data can be imported.
            If None, use the current working directory.
        ignore_keys: list of str
            Keys specified in this list are ignored and not seen as array
            information (note that ``attrs`` are used anyway)
        only: string, list or callable
            Can be one of the following three things:

            - a string that represents a pattern to match the array names
              that shall be included
            - a list of array names to include
            - a callable with two arguments, a string and a dict such as

              .. code-block:: python

                  def filter_func(arr_name: str, info: dict): -> bool
                      '''
                      Filter the array names

                      This function should return True if the array shall be
                      included, else False

                      Parameters
                      ----------
                      arr_name: str
                          The array name (i.e. the ``arr_name`` attribute)
                      info: dict
                          The dictionary with the array informations. Common
                          keys are ``'name'`` that points to the variable name
                          and ``'dims'`` that points to the dimensions and
                          ``'fname'`` that points to the file name
                      '''
                      return True or False

              The function should return ``True`` if the array shall be
              included, else ``False``. This function will also be given to
              subsequents instances of :class:`InteractiveList` objects that
              are contained in the returned value
        chname: dict
            A mapping from variable names in the project to variable names
            that should be used instead

        Other Parameters
        ----------------
        ``**kwargs``
            Any other parameter from the `psyplot.data.open_dataset` function
        %(open_dataset.parameters)s

        Returns
        -------
        psyplot.data.ArrayList
            The list with the interactive objects

        See Also
        --------
        from_dataset, array_info"""
        pwd = pwd or getcwd()
        if only is None:
            def only_filter(arr_name, info):
                return True
        elif callable(only):
            only_filter = only
        elif isstring(only):
            def only_filter(arr_name, info):
                return patt.search(arr_name) is not None
            patt = re.compile(only)
            only = None
        else:
            def only_filter(arr_name, info):
                return arr_name in save_only
            save_only = only
            only = None

        def get_fname_use(fname):
            squeeze = isstring(fname)
            fname = safe_list(fname)
            ret = tuple(f if utils.is_remote_url(f) or osp.isabs(f) else
                        osp.join(pwd, f)
                        for f in fname)
            return ret[0] if squeeze else ret

        def get_name(name):
            if not isstring(name):
                return list(map(get_name, name))
            else:
                return chname.get(name, name)

        if not isinstance(alternative_paths, dict):
            it = iter(alternative_paths)
            alternative_paths = defaultdict(partial(next, it, None))
        # first open all datasets if not already done
        if datasets is None:
            replace_concat_dim = 'concat_dim' not in kwargs
            replace_combine = 'combine' not in kwargs

            names_and_stores = cls._get_dsnames(
                d, concat_dim=True, combine=True)
            datasets = {}
            for fname, (store_mod, store_cls), concat_dim, combine in names_and_stores:
                fname_use = fname
                got = True
                if replace_concat_dim and concat_dim is not None:
                    kwargs['concat_dim'] = concat_dim
                elif replace_concat_dim and concat_dim is None:
                    kwargs.pop('concat_dim', None)
                if replace_combine and combine is not None:
                    kwargs['combine'] = combine
                elif replace_combine and combine is None:
                    kwargs.pop('combine', None)
                try:
                    fname_use = alternative_paths[fname]
                except KeyError:
                    got = False
                if not got or not fname_use:
                    if fname is not None:
                        fname_use = get_fname_use(fname)
                if fname_use is not None:
                    datasets[fname] = _open_ds_from_store(
                        fname_use, store_mod, store_cls, **kwargs)
            if alternative_paths is not None:
                for fname in set(alternative_paths).difference(datasets):
                    datasets[fname] = _open_ds_from_store(fname, **kwargs)
        elif not isinstance(datasets, dict):
            it_datasets = iter(datasets)
            datasets = defaultdict(partial(next, it_datasets, None))
        arrays = [0] * len(d)
        i = 0
        for arr_name, info in six.iteritems(d):
            if arr_name in ignore_keys or not only_filter(arr_name, info):
                arrays.pop(i)
                continue
            if not {'fname', 'ds', 'arr'}.intersection(info):
                # the described object is an InteractiveList
                arr = InteractiveList.from_dict(
                    info, alternative_paths=alternative_paths,
                    datasets=datasets, chname=chname)
                if not arr:
                    warn("Skipping empty list %s!" % arr_name)
                    arrays.pop(i)
                    continue
            else:
                if 'arr' in info:
                    arr = info.pop('arr')
                elif 'ds' in info:
                    arr = cls.from_dataset(
                        info['ds'], dims=info['dims'],
                        name=get_name(info['name']))[0]
                else:
                    fname = info['fname']
                    if fname is None:
                        warn("Could not open array %s because no filename was "
                             "specified!" % arr_name)
                        arrays.pop(i)
                        continue
                    try:  # in case, datasets is a defaultdict
                        datasets[fname]
                    except KeyError:
                        pass
                    if fname not in datasets:
                        warn("Could not open array %s because %s was not in "
                             "the list of datasets!" % (arr_name, fname))
                        arrays.pop(i)
                        continue
                    arr = cls.from_dataset(
                        datasets[fname], dims=info['dims'],
                        name=get_name(info['name']))[0]
                for key, val in six.iteritems(info.get('attrs', {})):
                    arr.attrs.setdefault(key, val)
            arr.psy.arr_name = arr_name
            arrays[i] = arr
            i += 1
        return cls(arrays, attrs=d.get('attrs', {}))

    docstrings.delete_params('get_filename_ds.parameters', 'ds', 'dump')

    @docstrings.get_sections(base='ArrayList.array_info')
    @docstrings.dedent
    def array_info(self, dump=None, paths=None, attrs=True,
                   standardize_dims=True, pwd=None, use_rel_paths=True,
                   alternative_paths={}, ds_description={'fname', 'store'},
                   full_ds=True, copy=False, **kwargs):
        """
        Get dimension informations on you arrays

        This method returns a dictionary containing informations on the
        array in this instance

        Parameters
        ----------
        dump: bool
            If True and the dataset has not been dumped so far, it is dumped to
            a temporary file or the one generated by `paths` is used. If it is
            False or both, `dump` and `paths` are None, no data will be stored.
            If it is None and `paths` is not None, `dump` is set to True.
        %(get_filename_ds.parameters.no_ds|dump)s
        attrs: bool, optional
            If True (default), the :attr:`ArrayList.attrs` and
            :attr:`xarray.DataArray.attrs` attributes are included in the
            returning dictionary
        standardize_dims: bool, optional
            If True (default), the real dimension names in the dataset are
            replaced by x, y, z and t to be more general.
        pwd: str
            Path to the working directory from where the data can be imported.
            If None, use the current working directory.
        use_rel_paths: bool, optional
            If True (default), paths relative to the current working directory
            are used. Otherwise absolute paths to `pwd` are used
        ds_description: 'all' or set of {'fname', 'ds', 'num', 'arr', 'store'}
            Keys to describe the datasets of the arrays. If all, all keys
            are used. The key descriptions are

            fname
                the file name is inserted in the ``'fname'`` key
            store
                the data store class and module is inserted in the ``'store'``
                key
            ds
                the dataset is inserted in the ``'ds'`` key
            num
                The unique number assigned to the dataset is inserted in the
                ``'num'`` key
            arr
                The array itself is inserted in the ``'arr'`` key
        full_ds: bool
            If True and ``'ds'`` is in `ds_description`, the entire dataset is
            included. Otherwise, only the DataArray converted to a dataset is
            included
        copy: bool
            If True, the arrays and datasets are deep copied


        Other Parameters
        ----------------
        %(get_filename_ds.other_parameters)s

        Returns
        -------
        OrderedDict
            An ordered mapping from array names to dimensions and filename
            corresponding to the array

        See Also
        --------
        from_dict"""
        saved_ds = kwargs.pop('_saved_ds', {})

        def get_alternative(f):
            return next(filter(lambda t: osp.samefile(f, t[0]),
                               six.iteritems(alternative_paths)), [False, f])

        if copy:
            def copy_obj(obj):
                # try to get the number of the dataset and create only one copy
                # copy for each dataset
                try:
                    num = obj.psy.num
                except AttributeError:
                    pass
                else:
                    try:
                        return saved_ds[num]
                    except KeyError:
                        saved_ds[num] = obj.psy.copy(True)
                        return saved_ds[num]
                return obj.psy.copy(True)
        else:
            def copy_obj(obj):
                return obj
        ret = OrderedDict()
        if ds_description == 'all':
            ds_description = {'fname', 'ds', 'num', 'arr', 'store'}
        if paths is not None:
            if dump is None:
                dump = True
            paths = iter(paths)
        elif dump is None:
            dump = False
        if pwd is None:
            pwd = getcwd()
        for arr in self:
            if isinstance(arr, InteractiveList):
                ret[arr.arr_name] = arr.array_info(
                    dump, paths, pwd=pwd, attrs=attrs,
                    standardize_dims=standardize_dims,
                    use_rel_paths=use_rel_paths, ds_description=ds_description,
                    alternative_paths=alternative_paths, copy=copy,
                    _saved_ds=saved_ds, **kwargs)
            else:
                if standardize_dims:
                    idims = arr.psy.decoder.standardize_dims(
                        next(arr.psy.iter_base_variables), arr.psy.idims)
                else:
                    idims = arr.psy.idims
                ret[arr.psy.arr_name] = d = {'dims': idims}
                if 'variable' in arr.coords:
                    d['name'] = [list(arr.coords['variable'].values)]
                else:
                    d['name'] = arr.name
                if 'fname' in ds_description or 'store' in ds_description:
                    fname, store_mod, store_cls = get_filename_ds(
                        arr.psy.base, dump=dump, paths=paths, **kwargs)
                    if 'store' in ds_description:
                        d['store'] = (store_mod, store_cls)
                    if 'fname' in ds_description:
                        d['fname'] = []
                        for i, f in enumerate(safe_list(fname)):
                            if (f is None or utils.is_remote_url(f)):
                                d['fname'].append(f)
                            else:
                                found, f = get_alternative(f)
                                if use_rel_paths:
                                    f = osp.relpath(f, pwd)
                                else:
                                    f = osp.abspath(f)
                                d['fname'].append(f)
                        if fname is None or isinstance(fname,
                                                       six.string_types):
                            d['fname'] = d['fname'][0]
                        else:
                            d['fname'] = tuple(safe_list(fname))
                        if arr.psy.base.psy._concat_dim is not None:
                            d['concat_dim'] = arr.psy.base.psy._concat_dim
                        if arr.psy.base.psy._combine is not None:
                            d['combine'] = arr.psy.base.psy._combine
                if 'ds' in ds_description:
                    if full_ds:
                        d['ds'] = copy_obj(arr.psy.base)
                    else:
                        d['ds'] = copy_obj(arr.to_dataset())
                if 'num' in ds_description:
                    d['num'] = arr.psy.base.psy.num
                if 'arr' in ds_description:
                    d['arr'] = copy_obj(arr)
                if attrs:
                    d['attrs'] = arr.attrs
        ret['attrs'] = self.attrs
        return ret

    def _get_tnames(self):
        """Get the name of the time coordinate of the objects in this list"""
        tnames = set()
        for arr in self:
            if isinstance(arr, InteractiveList):
                tnames.update(arr.get_tnames())
            else:
                tnames.add(arr.psy.decoder.get_tname(
                    next(arr.psy.iter_base_variables), arr.coords))
        return tnames - {None}

    @docstrings.dedent
    def _register_update(self, method='isel', replot=False, dims={}, fmt={},
                         force=False, todefault=False):
        """
        Register new dimensions and formatoptions for updating. The keywords
        are the same as for each single array

        Parameters
        ----------
        %(InteractiveArray._register_update.parameters)s"""

        for arr in self:
            arr.psy._register_update(method=method, replot=replot, dims=dims,
                                     fmt=fmt, force=force, todefault=todefault)

    @docstrings.get_sections(base='ArrayList.start_update')
    @dedent
    def start_update(self, draw=None):
        """
        Conduct the registered plot updates

        This method starts the updates from what has been registered by the
        :meth:`update` method. You can call this method if you did not set the
        `auto_update` parameter when calling the :meth:`update` method to True
        and when the :attr:`no_auto_update` attribute is True.

        Parameters
        ----------
        draw: bool or None
            If True, all the figures of the arrays contained in this list will
            be drawn at the end. If None, it defaults to the `'auto_draw'``
            parameter in the :attr:`psyplot.rcParams` dictionary

        See Also
        --------
        :attr:`no_auto_update`, update"""
        def worker(arr):
            results[arr.psy.arr_name] = arr.psy.start_update(
                draw=False, queues=queues)
        if len(self) == 0:
            return

        results = {}
        threads = [Thread(target=worker, args=(arr,),
                          name='update_%s' % arr.psy.arr_name)
                   for arr in self]
        jobs = [arr.psy._njobs for arr in self]
        queues = [Queue() for _ in range(max(map(len, jobs)))]
        # populate the queues
        for i, arr in enumerate(self):
            for j, n in enumerate(jobs[i]):
                for k in range(n):
                    queues[j].put(arr.psy.arr_name)
        for thread in threads:
            thread.setDaemon(True)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        if draw is None:
            draw = rcParams['auto_draw']
        if draw:
            self(arr_name=[name for name, adraw in six.iteritems(results)
                           if adraw]).draw()
            if rcParams['auto_show']:
                self.show()

    docstrings.keep_params('InteractiveArray.update.parameters',
                           'auto_update')

    @docstrings.get_sections(base='ArrayList.update')
    @docstrings.dedent
    def update(self, method='isel', dims={}, fmt={}, replot=False,
               auto_update=False, draw=None, force=False, todefault=False,
               enable_post=None, **kwargs):
        """
        Update the coordinates and the plot

        This method updates all arrays in this list with the given coordinate
        values and formatoptions.

        Parameters
        ----------
        %(InteractiveArray._register_update.parameters)s
        %(InteractiveArray.update.parameters.auto_update)s
        %(ArrayList.start_update.parameters)s
        enable_post: bool
            If not None, enable (``True``) or disable (``False``) the
            :attr:`~psyplot.plotter.Plotter.post`  formatoption in the plotters
        ``**kwargs``
            Any other formatoption or dimension that shall be updated
            (additionally to those in `fmt` and `dims`)

        Notes
        -----
        %(InteractiveArray.update.notes)s

        See Also
        --------
        no_auto_update, start_update"""
        dims = dict(dims)
        fmt = dict(fmt)
        vars_and_coords = set(chain(
            self.dims, self.coords, ['name', 'x', 'y', 'z', 't']))
        furtherdims, furtherfmt = utils.sort_kwargs(kwargs, vars_and_coords)
        dims.update(furtherdims)
        fmt.update(furtherfmt)

        self._register_update(method=method, replot=replot, dims=dims, fmt=fmt,
                              force=force, todefault=todefault)
        if enable_post is not None:
            for arr in self.with_plotter:
                arr.psy.plotter.enable_post = enable_post
        if not self.no_auto_update or auto_update:
            self.start_update(draw)

    def draw(self):
        """Draws all the figures in this instance"""
        for fig in set(chain(*map(
                lambda arr: arr.psy.plotter.figs2draw, self.with_plotter))):
            self.logger.debug("Drawing figure %s", fig.number)
            fig.canvas.draw()
        for arr in self:
            if arr.psy.plotter is not None:
                arr.psy.plotter._figs2draw.clear()
        self.logger.debug("Done drawing.")

    def __call__(self, types=None, method='isel', fmts=[], **attrs):
        """Get the arrays specified by their attributes

        Parameters
        ----------
        types: type or tuple of types
            Any class that shall be used for an instance check via
            :func:`isinstance`. If not None, the :attr:`plotter` attribute
            of the array is checked against this `types`
        method: {'isel', 'sel'}
            Selection method for the dimensions in the arrays to be used.
            If `method` is 'isel', dimension values in `attrs` must correspond
            to integer values as they are found in the
            :attr:`InteractiveArray.idims` attribute.
            Otherwise the :meth:`xarray.DataArray.coords` attribute is used.
        fmts: list
            List of formatoption strings. Only arrays with plotters who have
            this formatoption are returned
        ``**attrs``
            Parameters may be any attribute of the arrays in this instance,
            including the matplotlib axes (``ax``), matplotlib figure
            (``fig``) and the array name (``arr_name``).
            Values may be iterables (e.g. lists) of the attributes to consider
            or callable functions that accept the attribute as a value. If the
            value is a string, it will be put into a list."""
        def safe_item_list(key, val):
            return key, val if callable(val) else safe_list(val)

        def filter_list(arr):
            other_attrs = attrs.copy()
            arr_names = other_attrs.pop('arr_name', None)
            return ((arr_names is None or (
                        arr_names(arr.psy.arr_name) if callable(arr_names)
                        else arr.psy.arr_name in arr_names)) and
                    len(arr) == len(arr(types=types, method=method,
                                        **other_attrs)))
        if not attrs:
            def filter_by_attrs(arr):
                return True
        elif method == 'sel':
            def filter_by_attrs(arr):
                if isinstance(arr, InteractiveList):
                    return filter_list(arr)
                tname = arr.psy.decoder.get_tname(
                    next(six.itervalues(arr.psy.base_variables)))

                def check_values(arr, key, vals):
                    if key == 'arr_name':
                        attr = arr.psy.arr_name
                    elif key == 'ax':
                        attr = arr.psy.ax
                    elif key == 'fig':
                        attr = getattr(arr.psy.ax, 'figure', None)
                    else:
                        try:
                            attr = getattr(arr, key)
                        except AttributeError:
                            return False
                    if np.ndim(attr):  # do not filter for multiple items
                        return False
                    if hasattr(arr.psy, 'decoder') and (
                            arr.name == tname):
                        try:
                            vals = np.asarray(vals, dtype=np.datetime64)
                        except ValueError:
                            pass
                        else:
                            return attr.values.astype(vals.dtype) in vals
                    if callable(vals):
                        return vals(attr)
                    return getattr(attr, 'values', attr) in vals
                return all(
                    check_values(arr, key, val)
                    for key, val in six.iteritems(
                        arr.psy.decoder.correct_dims(next(six.itervalues(
                            arr.psy.base_variables)), attrs, remove=False)))
        else:
            def check_values(arr, key, vals):
                if key == 'arr_name':
                    attr = arr.psy.arr_name
                elif key == 'ax':
                    attr = arr.psy.ax
                elif key == 'fig':
                    attr = getattr(arr.psy.ax, 'figure', None)
                elif key in arr.coords:
                    attr = arr.psy.idims[key]
                else:
                    try:
                        attr = getattr(arr, key)
                    except AttributeError:
                        return False
                if np.ndim(attr):  # do not filter for multiple items
                    return False
                if callable(vals):
                    return vals(attr)
                return attr in vals

            def filter_by_attrs(arr):
                if isinstance(arr, InteractiveList):
                    return filter_list(arr)
                return all(
                    check_values(arr, key, val)
                    for key, val in six.iteritems(
                        arr.psy.decoder.correct_dims(next(six.itervalues(
                            arr.psy.base_variables)), attrs, remove=False)))
        attrs = dict(starmap(safe_item_list, six.iteritems(attrs)))
        ret = self.__class__(
            # iterable
            (arr for arr in self if
             (types is None or isinstance(arr.psy.plotter, types)) and
             filter_by_attrs(arr)),
            # give itself as base and the auto_update parameter
            auto_update=bool(self.auto_update))
        # now filter for the formatoptions
        if fmts:
            fmts = set(safe_list(fmts))
            ret = self.__class__(
                filter(lambda arr: (arr.psy.plotter and
                                    fmts <= set(arr.psy.plotter)),
                       ret))
        return ret

    def __contains__(self, val):
        try:
            name = val if isstring(val) else val.psy.arr_name
        except AttributeError:
            return False
        else:
            return name in self.arr_names and (
                isstring(val) or self._contains_array(val))

    def _contains_array(self, val):
        """Checks whether exactly this array is in the list"""
        arr = self(arr_name=val.psy.arr_name)[0]
        is_not_list = any(
            map(lambda a: not isinstance(a, InteractiveList),
                [arr, val]))
        is_list = any(map(lambda a: isinstance(a, InteractiveList),
                          [arr, val]))
        # if one is an InteractiveList and the other not, they differ
        if is_list and is_not_list:
            return False
        # if both are interactive lists, check the lists
        if is_list:
            return all(a in arr for a in val) and all(a in val for a in arr)
        # else we check the shapes and values
        return arr is val

    def _short_info(self, intend=0, maybe=False):
        if maybe:
            intend = 0
        str_intend = ' ' * intend
        if len(self) == 1:
            return str_intend + "%s%s.%s([%s])" % (
                '' if not hasattr(self, 'arr_name') else self.arr_name + ': ',
                self.__class__.__module__, self.__class__.__name__,
                self[0].psy._short_info(intend+4, maybe=True))
        return str_intend + "%s%s.%s([\n%s])" % (
            '' if not hasattr(self, 'arr_name') else self.arr_name + ': ',
            self.__class__.__module__, self.__class__.__name__,
            ",\n".join(
                '%s' % (
                    arr.psy._short_info(intend+4))
                for arr in self))

    def __str__(self):
        return self._short_info()

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, key):
        """Overwrites lists __getitem__ by returning an ArrayList if `key` is a
        slice"""
        if isinstance(key, slice):  # return a new ArrayList
            return self.__class__(
                super(ArrayList, self).__getitem__(key))
        else:  # return the item
            return super(ArrayList, self).__getitem__(key)

    if six.PY2:  # for compatibility to python 2.7
        def __getslice__(self, *args):
            return self[slice(*args)]

    def next_available_name(self, fmt_str='arr{0}', counter=None):
        """Create a new array out of the given format string

        Parameters
        ----------
        format_str: str
            The base string to use. ``'{0}'`` will be replaced by a counter
        counter: iterable
            An iterable where the numbers should be drawn from. If None,
            ``range(100)`` is used

        Returns
        -------
        str
            A possible name that is not in the current project"""
        names = self.arr_names
        counter = counter or iter(range(1000))
        try:
            new_name = next(
                filter(lambda n: n not in names,
                       map(fmt_str.format, counter)))
        except StopIteration:
            raise ValueError(
                "{0} already in the list".format(fmt_str))
        return new_name

    @docstrings.dedent
    def append(self, value, new_name=False):
        """
        Append a new array to the list

        Parameters
        ----------
        value: InteractiveBase
            The data object to append to this list
        %(ArrayList.rename.parameters.new_name)s

        Raises
        ------
        %(ArrayList.rename.raises)s

        See Also
        --------
        list.append, extend, rename"""
        arr, renamed = self.rename(value, new_name)
        if renamed is not None:
            super(ArrayList, self).append(value)

    @docstrings.dedent
    def extend(self, iterable, new_name=False):
        """
        Add further arrays from an iterable to this list

        Parameters
        ----------
        iterable
            Any iterable that contains :class:`InteractiveBase` instances
        %(ArrayList.rename.parameters.new_name)s

        Raises
        ------
        %(ArrayList.rename.raises)s

        See Also
        --------
        list.extend, append, rename"""
        # extend those arrays that aren't alredy in the list
        super(ArrayList, self).extend(t[0] for t in filter(
            lambda t: t[1] is not None, (
                self.rename(arr, new_name) for arr in iterable)))

    def remove(self, arr):
        """Removes an array from the list

        Parameters
        ----------
        arr: str or :class:`InteractiveBase`
            The array name or the data object in this list to remove

        Raises
        ------
        ValueError
            If no array with the specified array name is in the list"""
        name = arr if isinstance(arr, six.string_types) else arr.psy.arr_name
        if arr not in self:
            raise ValueError(
                "Array {0} not in the list".format(name))
        for i, arr in enumerate(self):
            if arr.psy.arr_name == name:
                del self[i]
                return
        raise ValueError(
            "No array found with name {0}".format(name))


@xr.register_dataset_accessor('psy')
class DatasetAccessor(object):
    """A dataset accessor to interface with the psyplot package"""

    _filename = None
    _data_store = None
    _num = None
    _plot = None

    #: The concatenation dimension for datasets opened with open_mfdataset
    _concat_dim = None

    #: The combine method to open multiple datasets with open_mfdataset
    _combine = None

    @property
    def num(self):
        """A unique number for the dataset"""
        if self._num is None:
            self._num = next(_ds_counter)
        return self._num

    @num.setter
    def num(self, value):
        self._num = value

    def __init__(self, ds):
        self.ds = ds

    @property
    def plot(self):
        """An object to generate new plots from this dataset

        To make a 2D-plot with the :mod:`psy-simple <psy_simple.plugin>`
        plugin, you can just type

        .. code-block:: python

            project = ds.psy.plot.plot2d(name='variable-name')

        It will create a new subproject with the extracted and visualized data.

        See Also
        --------
        psyplot.project.DatasetPlotter: for the different plot methods
        """
        if self._plot is None:
            import psyplot.project as psy
            self._plot = psy.DatasetPlotter(self.ds)
        return self._plot

    @property
    def filename(self):
        """The name of the file that stores this dataset"""
        fname = self._filename
        if fname is None:
            fname = get_filename_ds(self.ds, dump=False)[0]
        return fname

    @filename.setter
    def filename(self, value):
        self._filename = value

    @property
    def data_store(self):
        """The :class:`xarray.backends.common.AbstractStore` used to save the
        dataset"""
        store_info = self._data_store
        if store_info is None or any(s is None for s in store_info):
            store = getattr(self.ds, '_file_obj', None)
            store_mod = store.__module__ if store is not None else None
            store_cls = store.__class__.__name__ if store is not None else None
            return store_mod, store_cls
        return store_info

    @data_store.setter
    def data_store(self, value):
        self._data_store = value

    @docstrings.dedent
    def create_list(self, *args, **kwargs):
        """
        Create a :class:`psyplot.data.ArrayList` with arrays from this dataset

        Parameters
        ----------
        %(ArrayList.from_dataset.parameters)s

        Other Parameters
        ----------------
        %(ArrayList.from_dataset.other_parameters)s

        Returns
        -------
        %(ArrayList.from_dataset.returns)s

        See Also
        --------
        psyplot.data.ArrayList.from_dataset"""
        return ArrayList.from_dataset(self.ds, *args, **kwargs)

    def to_array(self, *args, **kwargs):
        """Same as :meth:`xarray.Dataset.to_array` but sets the base"""
        # the docstring is set below
        ret = self.ds.to_array(*args, **kwargs)
        ret.psy.base = self.ds
        return ret

    to_array.__doc__ = xr.Dataset.to_array.__doc__

    def __getitem__(self, key):
        ret = self.ds[key]
        if isinstance(ret, xr.DataArray):
            ret.psy.base = self.ds
        return ret

    def __getattr__(self, attr):
        if attr != 'ds' and attr in self.ds:
            ret = getattr(self.ds, attr)
            ret.psy.base = self.ds
            return ret
        else:
            raise AttributeError("%s has not Attribute %s" % (
                self.__class__.__name__, attr))

    def copy(self, deep=False):
        """Copy the array

        This method returns a copy of the underlying array in the :attr:`arr`
        attribute. It is more stable because it creates a new `psy` accessor"""
        ds = self.ds.copy(deep)
        ds.psy = DatasetAccessor(ds)
        return ds


class InteractiveList(ArrayList, InteractiveBase):
    """List of :class:`InteractiveArray` instances that can be plotted itself

    This class combines the :class:`ArrayList` and the interactive plotting
    through :class:`psyplot.plotter.Plotter` classes. It is mainly used by the
    :mod:`psyplot.plotter.simple` module"""

    no_auto_update = property(_no_auto_update_getter,
                              doc=_no_auto_update_getter.__doc__)

    @no_auto_update.setter
    def no_auto_update(self, value):
        ArrayList.no_auto_update.fset(self, value)
        InteractiveBase.no_auto_update.fset(self, value)

    @property
    @docstrings
    def _njobs(self):
        """%(InteractiveBase._njobs)s"""
        ret = super(self.__class__, self)._njobs or [0]
        ret[0] += 1
        return ret

    @property
    def psy(self):
        """Return the list itself"""
        return self

    logger = InteractiveBase.logger

    docstrings.delete_params('InteractiveBase.parameters', 'auto_update')

    @docstrings.dedent
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        %(ArrayList.parameters)s
        %(InteractiveBase.parameters.no_auto_update)s"""
        ibase_kwargs, array_kwargs = utils.sort_kwargs(
            kwargs, ['plotter', 'arr_name'])
        self._registered_updates = {}
        InteractiveBase.__init__(self, **ibase_kwargs)
        with self.block_signals:
            ArrayList.__init__(self, *args, **kwargs)

    @docstrings.dedent
    def _register_update(self, method='isel', replot=False, dims={}, fmt={},
                         force=False, todefault=False):
        """
        Register new dimensions and formatoptions for updating

        Parameters
        ----------
        %(InteractiveArray._register_update.parameters)s"""
        ArrayList._register_update(self, method=method, dims=dims)
        InteractiveBase._register_update(self, fmt=fmt, todefault=todefault,
                                         replot=bool(dims) or replot,
                                         force=force)

    @docstrings.dedent
    def start_update(self, draw=None, queues=None):
        """
        Conduct the formerly registered updates

        This method conducts the updates that have been registered via the
        :meth:`update` method. You can call this method if the
        :attr:`auto_update` attribute of this instance is True and the
        `auto_update` parameter in the :meth:`update` method has been set to
        False

        Parameters
        ----------
        %(InteractiveBase.start_update.parameters)s

        Returns
        -------
        %(InteractiveBase.start_update.returns)s

        See Also
        --------
        :attr:`no_auto_update`, update
        """
        if queues is not None:
            queues[0].get()
        try:
            for arr in self:
                arr.psy.start_update(draw=False)
            self.onupdate.emit()
        except Exception:
            self._finish_all(queues)
            raise
        if queues is not None:
            queues[0].task_done()
        return InteractiveBase.start_update(self, draw=draw, queues=queues)

    def to_dataframe(self):
        def to_df(arr):
            df = arr.to_pandas()
            if hasattr(df, 'to_frame'):
                df = df.to_frame()
            if not keep_names:
                return df.rename(columns={df.keys()[0]: arr.psy.arr_name})
            return df
        if len(self) == 1:
            return self[0].to_series().to_frame()
        else:
            keep_names = len(set(arr.name for arr in self)) == self
            df = to_df(self[0])
            for arr in self[1:]:
                df = df.merge(to_df(arr), left_index=True, right_index=True,
                              how='outer')
            return df

    docstrings.delete_params('ArrayList.from_dataset.parameters', 'plotter')
    docstrings.delete_kwargs('ArrayList.from_dataset.other_parameters',
                             'args', 'kwargs')

    @classmethod
    @docstrings.dedent
    def from_dataset(cls, *args, **kwargs):
        """
        Create an InteractiveList instance from the given base dataset

        Parameters
        ----------
        %(ArrayList.from_dataset.parameters.no_plotter)s
        plotter: psyplot.plotter.Plotter
            The plotter instance that is used to visualize the data in this
            list
        make_plot: bool
            If True, the plot is made

        Other Parameters
        ----------------
        %(ArrayList.from_dataset.other_parameters.no_args_kwargs)s
        ``**kwargs``
            Further keyword arguments may point to any of the dimensions of the
            data (see `dims`)

        Returns
        -------
        %(ArrayList.from_dataset.returns)s"""
        plotter = kwargs.pop('plotter', None)
        make_plot = kwargs.pop('make_plot', True)
        instance = super(InteractiveList, cls).from_dataset(*args, **kwargs)
        if plotter is not None:
            plotter.initialize_plot(instance, make_plot=make_plot)
        return instance

    def extend(self, *args, **kwargs):
        # reimplemented to emit onupdate
        super(InteractiveList, self).extend(*args, **kwargs)
        self.onupdate.emit()

    def append(self, *args, **kwargs):
        # reimplemented to emit onupdate
        super(InteractiveList, self).append(*args, **kwargs)
        self.onupdate.emit()

    def to_interactive_list(self):
        return self


class _MissingModule(object):
    """Class that can be used if an optional module is not avaible.

    This class raises an error if any attribute is accessed or it is called"""
    def __init__(self, error):
        """
        Parameters
        ----------
        error: ImportError
            The error that has been raised when tried to import the module"""
        self.error = error

    def __getattr__(self, attr):
        raise self.error

    def __call__(self, *args, **kwargs):
        raise self.error


def _open_ds_from_store(fname, store_mod=None, store_cls=None, **kwargs):
    """Open a dataset and return it"""
    if isinstance(fname, xr.Dataset):
        return fname
    if not isstring(fname):
        try:  # test iterable
            fname[0]
        except TypeError:
            pass
        else:
            if store_mod is not None and store_cls is not None:
                if isstring(store_mod):
                    store_mod = repeat(store_mod)
                if isstring(store_cls):
                    store_cls = repeat(store_cls)
                fname = [_open_store(sm, sc, f)
                         for sm, sc, f in zip(store_mod, store_cls, fname)]
                kwargs['engine'] = None
                kwargs['lock'] = False
                return open_mfdataset(fname, **kwargs)
            else:
                # try guessing with open_dataset
                return open_mfdataset(fname, **kwargs)
    if store_mod is not None and store_cls is not None:
        fname = _open_store(store_mod, store_cls, fname)
    return open_dataset(fname, **kwargs)


def decode_absolute_time(times):
    def decode(t):
        day = np.floor(t).astype(int)
        sub = t - day
        rest = dt.timedelta(days=sub)
        # round microseconds
        if rest.microseconds:
            rest += dt.timedelta(microseconds=1e6 - rest.microseconds)
        return np.datetime64(dt.datetime.strptime(
            "%i" % day, "%Y%m%d") + rest)
    return np.vectorize(decode, [np.datetime64])(times)


def encode_absolute_time(times):
    def encode(t):
        t = to_datetime(t)
        return float(t.strftime('%Y%m%d')) + (
            t - dt.datetime(t.year, t.month, t.day)).total_seconds() / 86400.
    return np.vectorize(encode, [float])(times)


class AbsoluteTimeDecoder(NDArrayMixin):

    def __init__(self, array):
        self.array = array
        example_value = first_n_items(array, 1) or 0
        try:
            result = decode_absolute_time(example_value)
        except Exception:
            logger.error("Could not interprete absolute time values!")
            raise
        else:
            self._dtype = getattr(result, 'dtype', np.dtype('object'))

    @property
    def dtype(self):
        return self._dtype

    def __getitem__(self, key):
        return decode_absolute_time(self.array[key])


class AbsoluteTimeEncoder(NDArrayMixin):

    def __init__(self, array):
        self.array = array
        example_value = first_n_items(array, 1) or 0
        try:
            result = encode_absolute_time(example_value)
        except Exception:
            logger.error("Could not interprete absolute time values!")
            raise
        else:
            self._dtype = getattr(result, 'dtype', np.dtype('object'))

    @property
    def dtype(self):
        return self._dtype

    def __getitem__(self, key):
        return encode_absolute_time(self.array[key])
