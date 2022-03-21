"""Project module of the psyplot Package.

This module contains the :class:`Project` class that serves as the main
part of the psyplot API. One instance of the :class:`Project` class serves as
coordinator of multiple plots and can be distributed into subprojects that
keep reference to the main project without holding all array instances

Furthermore this module contains an easy pyplot-like API to the current
subproject."""

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

import os
import os.path as osp
import yaml
import sys
import six
from copy import deepcopy as _deepcopy
import logging
import inspect
import pickle
from importlib import import_module
from itertools import chain, repeat, cycle, count, islice
from collections import defaultdict
from functools import wraps, partial
import xarray
import pandas as pd

import matplotlib as mpl
import matplotlib.figure as mfig
import numpy as np
import psyplot
from psyplot import rcParams, get_versions
import psyplot.utils as utils
from psyplot.config.rcsetup import get_configdir, psyplot_fname
from psyplot.warning import warn, critical
from psyplot.docstring import docstrings, dedent, safe_modulo
import psyplot.data as psyd
from psyplot.data import (
    ArrayList, open_dataset, open_mfdataset, _MissingModule,
    to_netcdf, Signal, CFDecoder, safe_list, InteractiveList)
from psyplot.plotter import unique_everseen, Plotter
from psyplot.compat.pycompat import (OrderedDict, range, getcwd,
                                     get_default_value as _get_default_value)
try:
    from cdo import Cdo as _CdoBase, CDO_PY_VERSION as cdo_version
    with_cdo = True
    cdo_version = tuple(map(int, cdo_version.split('.')[:2]))
except ImportError as e:
    Cdo = _MissingModule(e)
    with_cdo = False
    cdo_version = None

try:  # try import show_colormaps for convenience
    from psy_simple.colors import show_colormaps, get_cmap
except ImportError:
    pass

if rcParams['project.import_seaborn'] is not False:
    try:
        import seaborn as _sns
    except ImportError as e:
        if rcParams['project.import_seaborn']:
            raise
        _sns = _MissingModule(e)

_open_projects = []  # list of open projects
_current_project = None  # current main project
_current_subproject = None  # current subproject

# the informations on the psyplot and plugin versions
_versions = get_versions(requirements=False)


_concat_dim_default = _get_default_value(xarray.open_mfdataset, 'concat_dim')


def _update_versions():
    """Update :attr:`_versions` with the registered plotter methods"""
    for pm_name in plot._plot_methods:
        pm = getattr(plot, pm_name)
        plugin = pm._plugin
        if (plugin is not None and plugin not in _versions and
                pm.module in sys.modules):
            _versions.update(get_versions(key=lambda s: s == plugin))


@docstrings.get_sections(base='multiple_subplots')
@docstrings.dedent
def multiple_subplots(rows=1, cols=1, maxplots=None, n=1, delete=True,
                      for_maps=False, *args, **kwargs):
    """
    Function to create subplots.

    This function creates so many subplots on so many figures until the
    specified number `n` is reached.

    Parameters
    ----------
    rows: int
        The number of subplots per rows
    cols: int
        The number of subplots per column
    maxplots: int
        The number of subplots per figure (if None, it will be row*cols)
    n: int
        number of subplots to create
    delete: bool
        If True, the additional subplots per figure are deleted
    for_maps: bool
        If True this is a simple shortcut for setting
        ``subplot_kw=dict(projection=cartopy.crs.PlateCarree())`` and is
        useful if you want to use the :attr:`~ProjectPlotter.mapplot`,
        :attr:`~ProjectPlotter.mapvector` or
        :attr:`~ProjectPlotter.mapcombined` plotting methods
    ``*args`` and ``**kwargs``
        anything that is passed to the :func:`matplotlib.pyplot.subplots`
        function

    Returns
    -------
    list
        list of maplotlib.axes.SubplotBase instances"""
    import matplotlib.pyplot as plt
    axes = np.array([])
    maxplots = maxplots or rows * cols
    kwargs.setdefault('figsize', [
        min(8.*cols, 16), min(6.5*rows, 12)])
    if for_maps:
        import cartopy.crs as ccrs
        subplot_kw = kwargs.setdefault('subplot_kw', {})
        subplot_kw['projection'] = ccrs.PlateCarree()
    for i in range(0, n, maxplots):
        fig, ax = plt.subplots(rows, cols, *args, **kwargs)
        try:
            axes = np.append(axes, ax.ravel()[:maxplots])
            if delete:
                for iax in range(maxplots, rows * cols):
                    fig.delaxes(ax.ravel()[iax])
        except AttributeError:  # got a single subplot
            axes = np.append(axes, [ax])
        if i + maxplots > n and delete:
            for ax2 in axes[n:]:
                fig.delaxes(ax2)
                axes = axes[:n]
    return axes


def _is_slice(val):
    return isinstance(val, slice)


def _only_main(func):
    """Call the given `func` only from the main project"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.is_main:
            return getattr(self.main, func.__name__)(*args, **kwargs)
        return func(self, *args, **kwargs)
    return wrapper


def _first_main(func):
    """Call the given `func` with the same arguments but after the function
    of the main project"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.is_main:
            getattr(self.main, func.__name__)(*args, **kwargs)
        return func(self, *args, **kwargs)
    return wrapper


class Project(ArrayList):
    """A manager of multiple interactive data projects"""

    _main = None

    _registered_plotters = {}  #: registered plotter identifiers

    #: signal to be emiitted when the current main and/or subproject changes
    oncpchange = Signal(name='oncpchange', cls_signal=True)

    # block the signals of this class
    block_signals = utils._TempBool()

    @property
    def main(self):
        """:class:`Project`. The main project of this subproject"""
        return self._main if self._main is not None else self

    @main.setter
    def main(self, value):
        self._main = value

    @property
    @dedent
    def plot(self):
        """
        Plotting instance of this :class:`Project`. See the
        :class:`ProjectPlotter` class for method documentations"""
        return self._plot

    @property
    def _fmtos(self):
        """An iterator over formatoption objects

        Contains only the formatoption whose keys are in all plotters in this
        list"""
        plotters = self.plotters
        if len(plotters) == 0:
            return {}
        p0 = plotters[0]
        if len(plotters) == 1:
            return p0._fmtos
        return (getattr(p0, key) for key in set(p0).intersection(
            *map(set, plotters[1:])))

    @property
    def is_csp(self):
        """Boolean that is True if the project is the current subproject"""
        return self is _current_subproject

    @property
    def is_cmp(self):
        """Boolean that is True if the project is the current main project"""
        return self is _current_project

    @property
    def figs(self):
        """A mapping from figures to data objects with the plotter in this
        figure"""
        ret = utils.DefaultOrderedDict(lambda: self[1:0])
        for arr in self:
            if arr.psy.plotter is not None:
                ret[arr.psy.plotter.ax.get_figure()].append(arr)
        return OrderedDict(ret)

    @property
    def axes(self):
        """A mapping from axes to data objects with the plotter in this axes
        """
        ret = utils.DefaultOrderedDict(lambda: self[1:0])
        for arr in self:
            if arr.psy.plotter is not None:
                ret[arr.psy.plotter.ax].append(arr)
        return OrderedDict(ret)

    @property
    def is_main(self):
        """:class:`bool`. True if this :class:`Project` is a main project"""
        return self._main is None

    @property
    def logger(self):
        """:class:`logging.Logger` of this instance"""
        if not self.is_main:
            return self.main.logger
        try:
            return self._logger
        except AttributeError:
            name = '%s.%s.%s' % (self.__module__, self.__class__.__name__,
                                 self.num)
            self._logger = logging.getLogger(name)
            self.logger.debug('Initializing...')
            return self._logger

    @logger.setter
    def logger(self, value):
        self._logger = value

    def with_plotter(self):
        ret = super(Project, self).with_plotter
        ret.main = self.main
        return ret

    with_plotter = property(with_plotter, doc=ArrayList.with_plotter.__doc__)

    @property
    def arr_names(self):
        """Names of the arrays (!not of the variables!) in this list

        This attribute can be set with an iterable of unique names to change
        the array names of the data objects in this list."""
        return list(arr.psy.arr_name for arr in self)

    @arr_names.setter
    def arr_names(self, value):
        value = list(islice(value, len(self)))
        if not len(set(value)) == len(self):
            raise ValueError(
                "Got %i unique array names for %i data objects!" % (
                    len(set(value)), len(self)))
        elif not self.is_main and set(value) & (
                set(self.main.arr_names) - set(self.arr_names)):
            raise ValueError(
                "Cannot rename arrays because there are duplicates with the "
                "main project: %s" % (
                    set(value) & (
                        set(self.main.arr_names) - set(self.arr_names)), ))
        for arr, n in zip(self, value):
            arr.psy.arr_name = n
        if self.main is gcp(True):
            for arr in self:
                arr.psy.onupdate.emit()

    @property
    def plotters(self):
        """A list of all the plotters in this instance"""
        return [arr.psy.plotter for arr in self.with_plotter]

    @property
    def datasets(self):
        """A mapping from dataset numbers to datasets in this list"""
        return {key: val['ds'] for key, val in six.iteritems(
            self._get_ds_descriptions(self.array_info(ds_description=['ds'])))}

    @property
    def dsnames_map(self):
        """A dictionary from the dataset numbers in this list to their
        filenames"""
        return {key: val['fname'] for key, val in six.iteritems(
            self._get_ds_descriptions(self.array_info(
                ds_description=['num', 'fname']), ds_description={'fname'}))}

    @property
    def dsnames(self):
        """The set of dataset names in this instance"""
        return {t[0] for t in self._get_dsnames(self.array_info()) if t[0]}

    @docstrings.get_sections(base='Project')
    @docstrings.dedent
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        %(ArrayList.parameters)s
        main: Project
            The main project this subproject belongs to (or None if this
            project is the main project)
        num: int
            The number of the project
        """
        self.main = kwargs.pop('main', None)
        self._plot = ProjectPlotter(self)
        self.num = kwargs.pop('num', 1)
        self._ds_counter = count()
        with self.block_signals:
            super(Project, self).__init__(*args, **kwargs)

    @classmethod
    @docstrings.get_sections(base='Project._register_plotter')
    @dedent
    def _register_plotter(cls, identifier, module, plotter_name,
                          plotter_cls=None):
        """
        Register a plotter in the :class:`Project` class to easy access it

        Parameters
        ----------
        identifier: str
            Name of the attribute that is used to filter for the instances
            belonging to this plotter
        module: str
            The module from where to import the `plotter_name`
        plotter_name: str
            The name of the plotter class in `module`
        plotter_cls: type
            The imported class of `plotter_name`. If None, it will be imported
            when it is needed
        """
        if plotter_cls is not None:  # plotter has already been imported
            def get_x(self):
                return self(plotter_cls)
        else:
            def get_x(self):
                return self(getattr(import_module(module), plotter_name))
        setattr(cls, identifier, property(get_x, doc=(
            "List of data arrays that are plotted by :class:`%s.%s`"
            " plotters") % (module, plotter_name)))
        cls._registered_plotters[identifier] = (module, plotter_name)

    def disable(self):
        """Disables the plotters in this list"""
        for arr in self:
            if arr.psy.plotter:
                arr.psy.plotter.disabled = True

    def enable(self):
        for arr in self:
            if arr.psy.plotter:
                arr.psy.plotter.disabled = False

    def __call__(self, *args, **kwargs):
        ret = super(Project, self).__call__(*args, **kwargs)
        ret.main = self.main
        return ret

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close(True, True, True)

    @staticmethod
    @docstrings.get_sections(base='Project._load_preset',
                              sections=["Parameters", "Notes"])
    def _load_preset(preset: str):
        """Load a preset from disk

        Parameters
        ----------
        preset: str or dict
            The filename or identifier of a preset. If the given `preset` is
            the path to an existing yaml file, it will be loaded. Otherwise we
            look up the `preset` in the psyplot configuration directory (see
            :func:`~psyplot.config.rcsetup.get_configdir`).
            If a dictionary is provided, we assume that this is the preset

        Returns
        -------
        dict
            The loaded preset

        Notes
        -----
        An identifier is the filename without extension. If you want to list
        the available presets, run ``psyplot -lp`` from the command-line"""
        if isinstance(preset, dict):
            config = preset
        else:
            path = Project._resolve_preset_path(preset)
            if path in rcParams['presets.trusted']:
                loader = yaml.Loader
            else:
                loader = yaml.SafeLoader
            with open(path) as f:
                try:
                    config = yaml.load(f, loader)
                except yaml.constructor.ConstructorError as e:
                    e.note = (e.note or '') + (
                        ' You might want to add it to the trusted presets '
                        'via\n\npsy.rcParams["presets.trusted"].append("{}")\n\n'
                        'and run this method again. To permanently store '
                        'this preset, edit the file at\n\n{} ').format(
                            path, psyplot_fname())
                    raise

        return config

    @staticmethod
    def _resolve_preset_path(preset, if_exists=True):
        if osp.exists(preset):
            return preset
        else:
            confdir = get_configdir()
            presets_dir = osp.join(confdir, 'presets')
            if osp.exists(osp.join(presets_dir, preset)):
                return osp.join(presets_dir, preset)
            elif osp.exists(osp.join(presets_dir, preset + '.yml')):
                return osp.join(presets_dir, preset + '.yml')
            else:
                if if_exists:
                    raise ValueError(
                        f"Could not find a preset with name {preset}")
                else:
                    if not preset.endswith('.yml'):
                        return osp.join(presets_dir, preset + '.yml')
                    return preset

    @docstrings.dedent
    def load_preset(self, preset: str, **kwargs):
        """Load a preset from disk and apply it to the open project.

        This method loads a preset and updates the corresponding plots

        Parameters
        ----------
        %(Project._load_preset.parameters)s
        ``**kwargs``
            Any other parameter that shall be passed to the
            :meth:`~psyplot.data.ArrayList.update` method

        Notes
        -----
        %(Project._load_preset.notes)s
        """
        config = self._load_preset(preset)
        plotmethods = self.plot._plot_methods
        pm_config, defaults = utils.sort_kwargs(config, plotmethods)
        with self.no_auto_update:
            for pm in plotmethods:
                method = getattr(self.plot, pm)
                if method.is_imported:
                    sp = getattr(self, pm)
                    if sp:
                        valid = list(method.plotter_cls._get_formatoptions())
                        fmts = {key: val for key, val in defaults.items()
                                if key in valid}
                        fmts.update(pm_config.get(pm, {}))
                        sp.update(fmt=fmts, **kwargs)
        self.start_update()

    @staticmethod
    def extract_fmts_from_preset(preset: str, plotmethod: str):
        """Extract the formatoptions for a plotmethod from a given preset

        This method takes the preset and extracts the formatoptions valid for
        the given plotmethod

        Parameters
        ----------
        %(Project._load_preset.parameters)s
        plotmethod: str
            The plotmethod to use"""
        preset = Project._load_preset(preset)
        try:
            plotmethod._method
        except AttributeError:
            method = getattr(plot, plotmethod)
        else:
            method = plotmethod
            plotmethod = method._method

        plotmethods = plot._plot_methods
        pm_config, defaults = utils.sort_kwargs(preset, plotmethods)
        valid = list(method.plotter_cls._get_formatoptions())
        fmts = {key: val for key, val in defaults.items()
                if key in valid}
        fmts.update(pm_config.get(plotmethod, {}))
        return fmts


    def save_preset(self, fname=None, include_defaults=False, update=False):
        """Save the formatoptions of this project as a preset

        This method takes the formatoptions in the plotters of this project and
        saves it as a preset file"""

        def include(fmto, plotters):
            key = fmto.key
            for plotter in plotters:
                if fmto.diff(plotter[key]):
                    return False
            return True if include_defaults else fmto.changed

        if update:
            with open(f) as f:
                preset = yaml.load(f, yaml.Loader)
        else:
            preset = {}
        plotters = self.plotters

        for fmto in self._fmtos:
            if include(fmto, plotters):
                preset[fmto.key] = fmto.value

        for pm in self.plot._plot_methods:
            method = getattr(self.plot, pm)
            if method.is_imported:
                sp = getattr(self, pm)
                plotters = sp.plotters
                for fmto in sp._fmtos:
                    if fmto.key not in preset and include(fmto, plotters):
                        preset.setdefault(pm, {})
                        preset[pm][fmto.key] = fmto.value
        if fname is not None:
            fname = self._resolve_preset_path(fname, False)
            os.makedirs(osp.dirname(fname), exist_ok=True)
            with open(fname, 'w') as f:
                yaml.dump(preset, f)
        else:
            return preset

    @_first_main
    def extend(self, *args, **kwargs):
        len0 = len(self)
        ret = super(Project, self).extend(*args, **kwargs)
        if self._main is None:
            for arr in self:
                if arr.psy.plotter is not None:
                    arr.psy.plotter._project = self
        if len(self) > len0 and (self.is_csp or self.is_cmp):
            self.oncpchange.emit(self)
        return ret

    extend.__doc__ = ArrayList.extend.__doc__

    @_first_main
    def append(self, *args, **kwargs):
        len0 = len(self)
        ret = super(Project, self).append(*args, **kwargs)
        if self._main is None:
            for arr in self:
                if arr.psy.plotter is not None:
                    arr.psy.plotter._project = self
        if len(self) > len0 and (self.is_csp or self.is_cmp):
            self.oncpchange.emit(self)
        return ret

    append.__doc__ = ArrayList.append.__doc__

    __call__.__doc__ = ArrayList.__call__.__doc__

    @docstrings.get_sections(base='Project.close')
    @dedent
    def close(self, figs=True, data=False, ds=False, remove_only=False):
        """
        Close this project instance

        Parameters
        ----------
        figs: bool
            Close the figures
        data: bool
            delete the arrays from the (main) project
        ds: bool
            If True, close the dataset as well
        remove_only: bool
            If True and `figs` is True, the figures are not closed but the
            plotters are removed"""
        import matplotlib.pyplot as plt
        close_ds = ds
        for arr in self[:]:
            if figs and arr.psy.plotter is not None:
                if remove_only:
                    for fmto in arr.psy.plotter._fmtos:
                        try:
                            fmto.remove()
                        except Exception:
                            pass
                else:
                    plt.close(arr.psy.plotter.ax.get_figure().number)
                arr.psy.plotter = None
            if data:
                self.remove(arr)
                if not self.is_main:
                    try:
                        self.main.remove(arr)
                    except ValueError:  # arr not in list
                        pass
            if close_ds:
                if isinstance(arr, InteractiveList):
                    for ds in [val['ds'] for val in six.itervalues(
                               arr._get_ds_descriptions(
                                    arr.array_info(ds_description=['ds'],
                                                   standardize_dims=False)))]:
                        ds.close()
                else:
                    arr.psy.base.close()
        if self.is_main and self is gcp(True) and data:
            scp(None)
        elif self.is_main and self.is_cmp:
            self.oncpchange.emit(self)
        elif self.main.is_cmp:
            self.oncpchange.emit(self.main)

    docstrings.keep_params('multiple_subplots.parameters', 'delete')
    docstrings.delete_params('ArrayList.from_dataset.parameters', 'base')
    docstrings.delete_kwargs('ArrayList.from_dataset.other_parameters',
                             kwargs='kwargs')
    docstrings.keep_params('xarray.open_mfdataset.parameters', 'concat_dim')
    docstrings.keep_params('Project._load_preset.parameters', 'preset')

    @_only_main
    @docstrings.get_sections(base='Project._add_data',
                              sections=['Parameters', 'Other Parameters',
                                        'Returns'])
    @docstrings.dedent
    def _add_data(self, plotter_cls, filename_or_obj, fmt={}, make_plot=True,
                  draw=False, mf_mode=False, ax=None, engine=None, delete=True,
                  share=False, clear=False, enable_post=None,
                  concat_dim=_concat_dim_default, load=False,
                  *args, **kwargs):
        """
        Extract data from a dataset and visualize it with the given plotter

        Parameters
        ----------
        plotter_cls: type
            The subclass of :class:`psyplot.plotter.Plotter` to use for
            visualization
        filename_or_obj: filename, :class:`xarray.Dataset` or data store
            The object (or file name) to open. If not a dataset, the
            :func:`psyplot.data.open_dataset` will be used to open a dataset
        fmt: dict
            Formatoptions that shall be when initializing the plot (you can
            however also specify them as extra keyword arguments)
        make_plot: bool
            If True, the data is plotted at the end. Otherwise you have to
            call the :meth:`psyplot.plotter.Plotter.initialize_plot` method or
            the :meth:`psyplot.plotter.Plotter.reinit` method by yourself
        %(InteractiveBase.start_update.parameters.draw)s
        mf_mode: bool
            If True, the :func:`psyplot.open_mfdataset` method is used.
            Otherwise we use the :func:`psyplot.open_dataset` method which can
            open only one single dataset
        ax: None, tuple (x, y[, z]) or (list of) matplotlib.axes.Axes
            Specifies the subplots on which to plot the new data objects.

            - If None, a new figure will be created for each created plotter
            - If tuple (x, y[, z]), `x` specifies the number of rows, `y` the
              number of columns and the optional third parameter `z` the
              maximal number of subplots per figure.
            - If :class:`matplotlib.axes.Axes` (or list of those, e.g. created
              by the :func:`matplotlib.pyplot.subplots` function), the data
              will be plotted on these subplots
        %(open_dataset.parameters.engine)s
        %(multiple_subplots.parameters.delete)s
        share: bool, fmt key or list of fmt keys
            Determines whether the first created plotter shares it's
            formatoptions with the others. If True, all formatoptions are
            shared. Strings or list of strings specify the keys to share.
        clear: bool
            If True, axes are cleared before making the plot. This is only
            necessary if the `ax` keyword consists of subplots with projection
            that differs from the one that is needed
        enable_post: bool
            If True, the :attr:`~psyplot.plotter.Plotter.post` formatoption is
            enabled and post processing scripts are allowed. If ``None``, this
            parameter is set to True if there is a value given for the `post`
            formatoption in `fmt` or `kwargs`
        %(xarray.open_mfdataset.parameters.concat_dim)s
            This parameter only does have an effect if `mf_mode` is True.
        load: bool
            If True, load the complete dataset into memory before plotting.
            This might be useful if the data of other variables in the dataset
            has to be accessed multiple times, e.g. for unstructured grids.
        %(ArrayList.from_dataset.parameters.no_base)s

        Other Parameters
        ----------------
        %(ArrayList.from_dataset.other_parameters.no_args_kwargs)s
        ``**kwargs``
            Any other dimension or formatoption that shall be passed to `dims`
            or `fmt` respectively.

        Returns
        -------
        Project
            The subproject that contains the new (visualized) data array"""
        if not isinstance(filename_or_obj, xarray.Dataset):
            if mf_mode:
                filename_or_obj = open_mfdataset(filename_or_obj,
                                                 engine=engine,
                                                 concat_dim=concat_dim)
            else:
                filename_or_obj = open_dataset(filename_or_obj,
                                               engine=engine)
        if load:
            old = filename_or_obj
            filename_or_obj = filename_or_obj.load()
            old.close()

        fmt = dict(fmt)
        possible_fmts = list(plotter_cls._get_formatoptions())
        additional_fmt, kwargs = utils.sort_kwargs(
            kwargs, possible_fmts)
        fmt.update(additional_fmt)
        if enable_post is None:
            enable_post = bool(fmt.get('post'))
        # create the subproject
        sub_project = self.from_dataset(filename_or_obj, **kwargs)
        sub_project.main = self
        sub_project.no_auto_update = not (
            not sub_project.no_auto_update or not self.no_auto_update)
        # create the subplots
        proj = plotter_cls._get_sample_projection()
        if isinstance(ax, tuple):
            axes = iter(multiple_subplots(
                *ax, n=len(sub_project), subplot_kw={'projection': proj}))
        elif ax is None or isinstance(ax, (mpl.axes.SubplotBase,
                                           mpl.axes.Axes)):
            axes = repeat(ax)
        else:
            axes = iter(ax)
        clear = clear or (isinstance(ax, tuple) and proj is not None)

        for arr in sub_project:
            plotter_cls(arr, make_plot=(not bool(share) and make_plot),
                        draw=False, ax=next(axes), clear=clear,
                        project=self, enable_post=enable_post, **fmt)
        if share:
            if share is True:
                share = possible_fmts
            elif isinstance(share, six.string_types):
                share = [share]
            else:
                share = list(share)
            sub_project[0].psy.plotter.share(
                [arr.psy.plotter for arr in sub_project[1:]], keys=share,
                draw=False)
            if make_plot:
                for arr in sub_project:
                    arr.psy.plotter.reinit(draw=False, clear=clear)
        if draw is None:
            draw = rcParams['auto_draw']
        if draw:
            sub_project.draw()
            if rcParams['auto_show']:
                self.show()
        self.extend(sub_project, new_name=True)
        if self is gcp(True):
            scp(sub_project)
        return sub_project

    def __getitem__(self, key):
        """Overwrites lists __getitem__ by returning subproject if `key` is a
        slice"""
        if isinstance(key, slice):  # return a new project
            ret = self.__class__(
                super(Project, self).__getitem__(key))
            ret.main = self.main
        else:  # return the item
            ret = super(Project, self).__getitem__(key)
        return ret

    if six.PY2:  # for compatibility to python 2.7
        def __getslice__(self, *args):
            return self[slice(*args)]

    def __add__(self, other):
        # overwritte to return a subproject
        ret = self.__class__(super(Project, self).__add__(other))
        ret.main = self.main
        return ret

    @staticmethod
    def show():
        """Shows all open figures"""
        import matplotlib.pyplot as plt
        plt.show(block=False)

    docstrings.keep_params('join_dicts.parameters', 'delimiter')
    docstrings.keep_params('join_dicts.parameters', 'keep_all')

    @docstrings.get_sections(base='Project.joined_attrs')
    @docstrings.with_indent(8)
    def joined_attrs(self, delimiter=', ', enhanced=True, plot_data=False,
                     keep_all=True):
        """Join the attributes of the arrays in this project

        Parameters
        ----------
        %(join_dicts.parameters.delimiter)s
        enhanced: bool
            If True, the :meth:`psyplot.plotter.Plotter.get_enhanced_attrs`
            method is used, otherwise the :attr:`xarray.DataArray.attrs`
            attribute is used.
        plot_data: bool
            It True, use the :attr:`psyplot.plotter.Plotter.plot_data`
            attribute of the plotters rather than the raw data in this project
        %(join_dicts.parameters.keep_all)s

        Returns
        -------
        dict
            A mapping from the attribute to the joined attributes which are
            either strings or (if there is only one attribute value), the
            data type of the corresponding value"""
        if enhanced:
            all_attrs = [
                plotter.get_enhanced_attrs(
                    getattr(plotter, 'plot_data' if plot_data else 'data'))
                for plotter in self.plotters]
        else:
            if plot_data:
                all_attrs = [plotter.plot_data.attrs
                             for plotter in self.plotters]
            else:
                all_attrs = [arr.attrs for arr in self]
        return utils.join_dicts(all_attrs, delimiter=delimiter,
                                keep_all=keep_all)

    @docstrings.get_sections(base='Project.format_string')
    @docstrings.with_indent(8)
    def format_string(self, s, use_time=False, format_args=None, *args,
                      **kwargs):
        """Format a string with the attributes in this project

        Parameters
        ----------
        s: str
            The string that is subject to be formatted
        use_time: bool
            If True, formatting strings for the
            :meth:`datetime.datetime.strftime` are expected to be found in
            `output` (e.g. ``'%%m'``, ``'%%Y'``, etc.). If so, other formatting
            strings must be escaped by double ``'%%'`` (e.g. ``'%%%i'``
            instead of (``'%%i'``))
        format_args: tuple
            A tuple of arguments that shall be inserted in `s` via
            ``s %% format_args``. (There will be no error, when this fails!)
        %(Project.joined_attrs.parameters)s

        Returns
        -------
        str
            The formatted string `s`
        """
        attrs = self.joined_attrs(*args, **kwargs)
        if use_time:
            tnames = self._get_tnames()
            tname = next(iter(tnames)) if len(tnames) == 1 else None

            time = attrs[tname]
            try:  # assume a valid datetime.datetime instance
                s = pd.to_datetime(time).strftime(s)
            except ValueError:
                pass
        if format_args is not None:
            try:
                s = safe_modulo(s, format_args, print_warning=False)
            except TypeError:
                pass
        return safe_modulo(s, attrs)

    docstrings.keep_params('Project.format_string.parameters', 'use_time')

    @docstrings.with_indent(8)
    def export(self, output, tight=False, concat=True, close_pdf=None,
               use_time=False, **kwargs):
        """Exports the figures of the project to one or more image files

        Parameters
        ----------
        output: str, iterable or matplotlib.backends.backend_pdf.PdfPages
            if string or list of strings, those define the names of the output
            files. Otherwise you may provide an instance of
            :class:`matplotlib.backends.backend_pdf.PdfPages` to save the
            figures in it.
            If string (or iterable of strings), attribute names in the
            xarray.DataArray.attrs attribute as well as index dimensions
            are replaced by the respective value (see examples below).
            Furthermore a single format string without key (e.g. %%i, %%s, %%d,
            etc.) is replaced by a counter.
        tight: bool
            If True, it is tried to figure out the tight bbox of the figure
            (same as bbox_inches='tight')
        concat: bool
            if True and the output format is `pdf`, all figures are
            concatenated into one single pdf
        close_pdf: bool or None
            If True and the figures are concatenated into one single pdf,
            the resulting pdf instance is closed. If False it remains open.
            If None and `output` is a string, it is the same as
            ``close_pdf=True``, if None and `output` is neither a string nor an
            iterable, it is the same as ``close_pdf=False``
        %(Project.format_string.parameters.use_time)s
        ``**kwargs``
            Any valid keyword for the :func:`matplotlib.pyplot.savefig`
            function

        Returns
        -------
        matplotlib.backends.backend_pdf.PdfPages or None
            a PdfPages instance if output is a string and close_pdf is False,
            otherwise None

        Examples
        --------
        Simply save all figures into one single pdf::

            >>> p = psy.gcp()
            >>> p.export('my_plots.pdf')

        Save all figures into separate pngs with increasing numbers (e.g.
        ``'my_plots_1.png'``)::

            >>> p.export('my_plots_%%i.png')

        Save all figures into separate pngs with the name of the variables
        shown in each figure (e.g. ``'my_plots_t2m.png'``)::

            >>> p.export('my_plots_%%(name)s.png')

        Save all figures into separate pngs with the name of the variables
        shown in each figure and with increasing numbers (e.g.
        ``'my_plots_1_t2m.png'``)::

            >>> p.export('my_plots_%%i_%%(name)s.png')

        Specify the names for each figure directly via a list::

            >>> p.export(['my_plots1.pdf', 'my_plots2.pdf'])
        """
        from matplotlib.backends.backend_pdf import PdfPages
        if tight:
            kwargs['bbox_inches'] = 'tight'

        not_enough_files_warnings = (
            "Not enough output files specified! %i figures are open "
            "but only %i filenames have been given! This will cause "
            "that some figures may be overwritten after being "
            "exported! Use a pdf instead if you want to save all "
            "figures or include a '%%i' string in the filename to "
            "avoid duplicates.")

        if isinstance(output, six.string_types):  # a single string
            out_fmt = kwargs.pop('format', os.path.splitext(output))[1][1:]
            if out_fmt.lower() == 'pdf' and concat:
                output = self.format_string(output, use_time, delimiter='-')
                pdf = PdfPages(output)

                for fig in self.figs:
                    pdf.savefig(fig, **kwargs)
                if close_pdf is None or close_pdf:
                    pdf.close()
                    return
                else:
                    return pdf
            else:
                output = [output] * len(self.figs)

        if utils.is_iterable(output):  # a list of strings
            output = [sp.format_string(out, use_time, i, delimiter='-')
                      for i, (out, sp) in enumerate(
                          zip(output, self.figs.values()), 1)]
            if len(set(output)) != len(output):
                warn(not_enough_files_warnings % (
                    len(output), len(self.figs)))
            output = iter(output)

            for fig, out in zip(self.figs, output):
                fig.savefig(out, **kwargs)
        else:  # an instances of matplotlib.backends.backend_pdf.PdfPages
            for fig in self.figs:
                output.savefig(fig, **kwargs)
            if close_pdf:
                output.close()

    docstrings.keep_params('Plotter.share.parameters', 'keys')
    docstrings.delete_params('Plotter.share.parameters', 'keys', 'plotters')

    @docstrings.dedent
    def share(self, base=None, keys=None, by=None, **kwargs):
        """
        Share the formatoptions of one plotter with all the others

        This method shares specified formatoptions from `base` with all the
        plotters in this instance.

        Parameters
        ----------
        base: None, Plotter, xarray.DataArray, InteractiveList, or list of them
            The source of the plotter that shares its formatoptions with the
            others. It can be None (then the first instance in this project
            is used), a :class:`~psyplot.plotter.Plotter` or any data object
            with a *psy* attribute. If `by` is not None, then it is expected
            that `base` is a list of data objects for each figure/axes
        %(Plotter.share.parameters.keys)s
        by: {'fig', 'figure', 'ax', 'axes'}
            Share the formatoptions only with the others on the same
            ``'figure'`` or the same ``'axes'``. In this case, base must either
            be ``None`` or a list of the types specified for `base`
        %(Plotter.share.parameters.no_keys|plotters)s

        See Also
        --------
        psyplot.plotter.share"""
        if by is not None:
            if base is not None:
                if hasattr(base, 'psy') or isinstance(base, Plotter):
                    base = [base]
                if by.lower() in ['ax', 'axes']:
                    bases = {ax: p[0] for ax, p in six.iteritems(
                        Project(base).axes)}
                elif by.lower() in ['fig', 'figure']:
                    bases = {fig: p[0] for fig, p in six.iteritems(
                        Project(base).figs)}
                else:
                    raise ValueError(
                        "*by* must be out of {'fig', 'figure', 'ax', 'axes'}. "
                        "Not %s" % (by, ))
            else:
                bases = {}
            projects = self.axes if by == 'axes' else self.figs
            for obj, p in projects.items():
                p.share(bases.get(obj), keys, **kwargs)
        else:
            plotters = self.plotters
            if not plotters:
                return
            if base is None:
                if len(plotters) == 1:
                    return
                base = plotters[0]
                plotters = plotters[1:]
            elif not isinstance(base, Plotter):
                base = getattr(getattr(base, 'psy', base), 'plotter', base)
            base.share(plotters, keys=keys, **kwargs)

    @docstrings.dedent
    def unshare(self, **kwargs):
        """
        Unshare the formatoptions of all the plotters in this instance

        This method uses the :meth:`psyplot.plotter.Plotter.unshare_me`
        method to release the specified formatoptions in `keys`.

        Parameters
        ----------
        %(Plotter.unshare_me.parameters)s

        See Also
        --------
        psyplot.plotter.Plotter.unshare, psyplot.plotter.Plotter.unshare_me"""
        for plotter in self.plotters:
            plotter.unshare_me(**kwargs)

    docstrings.delete_params('ArrayList.array_info.parameters', 'pwd', 'copy')

    @docstrings.get_sections(base='Project.save_project')
    @docstrings.dedent
    def save_project(self, fname=None, pwd=None, pack=False, **kwargs):
        """
        Save this project to a file

        Parameters
        ----------
        fname: str or None
            If None, the dictionary will be returned. Otherwise the necessary
            information to load this project via the :meth:`load` method is
            saved to `fname` using the :mod:`pickle` module
        pwd: str or None, optional
            Path to the working directory from where the data can be imported.
            If None and `fname` is the path to a file, `pwd` is set to the
            directory of this file. Otherwise the current working directory is
            used.
        pack: bool
            If True, all datasets are packed into the folder of `fname`
            and will be used if the data is loaded
        %(ArrayList.array_info.parameters.no_pwd|copy)s

        Notes
        -----
        You can also store the entire data in the pickled file by setting
        ``ds_description={'ds'}``"""
        # store the figure informatoptions and array informations
        if fname is not None and pwd is None and not pack:
            pwd = os.path.dirname(fname)
        if pack and fname is not None:
            target_dir = os.path.dirname(fname)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            def tmp_it():
                from tempfile import NamedTemporaryFile
                while True:
                    yield NamedTemporaryFile(
                        dir=target_dir, suffix='.nc').name

            kwargs.setdefault('paths', tmp_it())
        if fname is not None:
            kwargs['copy'] = True

        _update_versions()
        ret = {'figs': dict(map(_ProjectLoader.inspect_figure, self.figs)),
               'arrays': self.array_info(pwd=pwd, **kwargs),
               'versions': _deepcopy(_versions)}
        if pack and fname is not None:
            # we get the filenames out of the results and copy the datasets
            # there. After that we check the filenames again and force them
            # to the desired directory
            from shutil import copyfile
            fnames = (f[0] for f in self._get_dsnames(ret['arrays']))
            alternative_paths = kwargs.pop('alternative_paths', {})
            counters = defaultdict(int)
            if kwargs.get('use_rel_paths', True):
                get_path = partial(os.path.relpath, start=target_dir)
            else:
                get_path = os.path.abspath
            for ds_fname in unique_everseen(chain(alternative_paths, fnames)):
                if ds_fname is None or utils.is_remote_url(ds_fname):
                    continue
                dst_file = alternative_paths.get(
                    ds_fname, os.path.join(target_dir, os.path.basename(
                        ds_fname)))
                orig_dst_file = dst_file
                if counters[dst_file] and (
                        not os.path.exists(dst_file) or
                        not os.path.samefile(ds_fname, dst_file)):
                    dst_file, ext = os.path.splitext(dst_file)
                    dst_file += '-' + str(counters[orig_dst_file]) + ext
                if (not os.path.exists(dst_file) or
                        not os.path.samefile(ds_fname, dst_file)):
                    copyfile(ds_fname, dst_file)
                    counters[orig_dst_file] += 1
                alternative_paths.setdefault(ds_fname, get_path(dst_file))
            ret['arrays'] = self.array_info(
                pwd=pwd, alternative_paths=alternative_paths, **kwargs)
        # store the plotter settings
        for arr, d in zip(self, six.itervalues(ret['arrays'])):
            if arr.psy.plotter is None:
                continue
            plotter = arr.psy.plotter
            d['plotter'] = {
                'ax': _ProjectLoader.inspect_axes(plotter.ax),
                'fmt': {key: getattr(plotter, key).value2pickle
                        for key in plotter},
                'cls': (plotter.__class__.__module__,
                        plotter.__class__.__name__),
                'shared': {}}
            d['plotter']['ax']['shared'] = set(
                other.psy.arr_name for other in self
                if other.psy.ax == plotter.ax)
            if plotter.ax._sharex:
                d['plotter']['ax']['sharex'] = next(
                    (other.psy.arr_name for other in self
                     if other.psy.ax == plotter.ax._sharex), None)
            if plotter.ax._sharey:
                d['plotter']['ax']['sharey'] = next(
                    (other.psy.arr_name for other in self
                     if other.psy.ax == plotter.ax._sharey), None)
            shared = d['plotter']['shared']
            for fmto in plotter._fmtos:
                if fmto.shared:
                    shared[fmto.key] = [other_fmto.plotter.data.psy.arr_name
                                        for other_fmto in fmto.shared]
        if fname is not None:
            with open(fname, 'wb') as f:
                pickle.dump(ret, f)
            return None

        return ret

    @docstrings.dedent
    def keys(self, *args, **kwargs):
        """
        Show the available formatoptions in this project

        Parameters
        ----------
        %(Plotter.show_keys.parameters)s

        Other Parameters
        ----------------
        %(Plotter.show_keys.other_parameters)s

        Returns
        -------
        %(Plotter.show_keys.returns)s"""

        class TmpClass(Plotter):
            pass
        for fmto in self._fmtos:
            setattr(TmpClass, fmto.key, type(fmto)(fmto.key))
        return TmpClass.show_keys(*args, **kwargs)

    @docstrings.dedent
    def summaries(self, *args, **kwargs):
        """
        Show the available formatoptions and their summaries in this project

        Parameters
        ----------
        %(Plotter.show_keys.parameters)s

        Other Parameters
        ----------------
        %(Plotter.show_keys.other_parameters)s

        Returns
        -------
        %(Plotter.show_keys.returns)s"""

        class TmpClass(Plotter):
            pass
        for fmto in self._fmtos:
            setattr(TmpClass, fmto.key, type(fmto)(fmto.key))
        return TmpClass.show_summaries(*args, **kwargs)

    @docstrings.dedent
    def docs(self, *args, **kwargs):
        """
        Show the available formatoptions in this project and their full docu

        Parameters
        ----------
        %(Plotter.show_keys.parameters)s

        Other Parameters
        ----------------
        %(Plotter.show_keys.other_parameters)s

        Returns
        -------
        %(Plotter.show_keys.returns)s"""

        class TmpClass(Plotter):
            pass
        for fmto in self._fmtos:
            setattr(TmpClass, fmto.key, type(fmto)(fmto.key))
        return TmpClass.show_docs(*args, **kwargs)

    @classmethod
    @docstrings.with_indent(8)
    def from_dataset(cls, *args, **kwargs):
        """Construct an ArrayList instance from an existing base dataset

        Parameters
        ----------
        %(ArrayList.from_dataset.parameters)s
        main: Project
            The main project that this project corresponds to

        Other Parameters
        ----------------
        %(ArrayList.from_dataset.other_parameters)s

        Returns
        -------
        Project
            The newly created project instance
        """
        main = kwargs.pop('main', None)
        ret = super(Project, cls).from_dataset(*args, **kwargs)
        if main is not None:
            ret.main = main
            main.extend(ret, new_name=False)
        return ret

    docstrings.delete_params('ArrayList.from_dict.parameters', 'd', 'pwd')
    docstrings.keep_params('Project._add_data.parameters', 'make_plot')
    docstrings.keep_params('Project._add_data.parameters', 'clear')

    @classmethod
    @docstrings.get_sections(base='Project.load_project')
    @docstrings.dedent
    def load_project(cls, fname, auto_update=None, make_plot=True,
                     draw=False, alternative_axes=None, main=False,
                     encoding=None, enable_post=False, new_fig=True,
                     clear=None, **kwargs):
        """
        Load a project from a file or dict

        This classmethod allows to load a project that has been stored using
        the :meth:`save_project` method and reads all the data and creates the
        figures.

        Since the data is stored in external files when saving a project,
        make sure that the data is accessible under the relative paths
        as stored in the file `fname` or from the current working directory
        if `fname` is a dictionary. Alternatively use the `alternative_paths`
        parameter or the `pwd` parameter

        Parameters
        ----------
        fname: str or dict
            The string might be the path to a file created with the
            :meth:`save_project` method, or it might be a dictionary from this
            method
        %(InteractiveBase.parameters.auto_update)s
        %(Project._add_data.parameters.make_plot)s
        %(InteractiveBase.start_update.parameters.draw)s
        alternative_axes: dict, None or list
            alternative axes instances to use

            - If it is None, the axes and figures from the saving point will be
              reproduced.
            - a dictionary should map from array names in the created
              project to matplotlib axes instances
            - a list should contain axes instances that will be used for
              iteration
        main: bool, optional
            If True, a new main project is created and returned.
            Otherwise (by default default) the data is added to the current
            main project.
        encoding: str
            The encoding to use for loading the project. If None, it is
            automatically determined by pickle. Note: Set this to ``'latin1'``
            if using a project created with python2 on python3.
        enable_post: bool
            If True, the :attr:`~psyplot.plotter.Plotter.post` formatoption is
            enabled and post processing scripts are allowed. Do only set this
            parameter to ``True`` if you know you can trust the information in
            `fname`
        new_fig: bool
            If True (default) and `alternative_axes` is None, new figures are
            created if the figure already exists
        %(Project._add_data.parameters.clear)s
        pwd: str or None, optional
            Path to the working directory from where the data can be imported.
            If None and `fname` is the path to a file, `pwd` is set to the
            directory of this file. Otherwise the current working directory is
            used.
        %(ArrayList.from_dict.parameters.no_d|pwd)s

        Other Parameters
        ----------------
        %(ArrayList.from_dict.parameters)s

        Returns
        -------
        Project
            The project in state of the saving point"""
        from pkg_resources import iter_entry_points

        def get_ax_base(name, alternatives):
            ax_base = next(iter(obj(arr_name=name).axes), None)
            if ax_base is None:
                ax_base = next(iter(obj(arr_name=alternatives).axes), None)
            if ax_base is not None:
                alternatives.difference_update(obj(ax=ax_base).arr_names)
            return ax_base

        pwd = kwargs.pop('pwd', None)
        if isinstance(fname, six.string_types):
            with open(fname, 'rb') as f:
                pickle_kws = {} if not encoding else {'encoding': encoding}
                d = pickle.load(f, **pickle_kws)
            pwd = pwd or os.path.dirname(fname)
        else:
            d = dict(fname)
            pwd = pwd or getcwd()
        # check for patches of plugins
        for ep in iter_entry_points('psyplot', name='patches'):
            patches = ep.load()
            for arr_d in d.get('arrays').values():
                plotter_cls = arr_d.get('plotter', {}).get('cls')
                if plotter_cls is not None and plotter_cls in patches:
                    # apply the patch
                    patches[plotter_cls](arr_d['plotter'],
                                         d.get('versions', {}))
        fig_map = {}
        if alternative_axes is None:
            for fig_dict in six.itervalues(d.get('figs', {})):
                orig_num = fig_dict.get('num') or 1
                fig_map[orig_num] = _ProjectLoader.load_figure(
                    fig_dict, new_fig=new_fig).number
        elif not isinstance(alternative_axes, dict):
            alternative_axes = cycle(iter(alternative_axes))
        obj = cls.from_dict(d['arrays'], pwd=pwd, **kwargs)
        if main:
            # we create a new project with the project factory to make sure
            # that everything is handled correctly
            obj = project(None, obj)
        axes = {}
        arr_names = obj.arr_names
        sharex = defaultdict(set)
        sharey = defaultdict(set)
        for arr, (arr_name, arr_dict) in zip(
                obj, filter(lambda t: t[0] in arr_names,
                            six.iteritems(d['arrays']))):
            if not arr_dict.get('plotter'):
                continue
            plot_dict = arr_dict['plotter']
            plotter_cls = getattr(
                import_module(plot_dict['cls'][0]), plot_dict['cls'][1])
            ax = None
            if alternative_axes is not None:
                if isinstance(alternative_axes, dict):
                    ax = alternative_axes.get(arr.arr_name)
                else:
                    ax = next(alternative_axes, None)
            if ax is None and 'ax' in plot_dict:
                already_opened = plot_dict['ax'].get(
                    'shared', set()).intersection(axes)
                if already_opened:
                    ax = axes[next(iter(already_opened))]
                else:
                    plot_dict['ax'].pop('shared', None)
                    plot_dict['ax']['fig'] = fig_map[
                        plot_dict['ax'].get('fig') or 1]
                    if plot_dict['ax'].get('sharex'):
                        sharex[plot_dict['ax'].pop('sharex')].add(
                            arr.psy.arr_name)
                    if plot_dict['ax'].get('sharey'):
                        sharey[plot_dict['ax'].pop('sharey')].add(
                            arr.psy.arr_name)
                    axes[arr.psy.arr_name] = ax = _ProjectLoader.load_axes(
                        plot_dict['ax'])
            plotter_cls(
                arr, make_plot=False, draw=False, clear=False,
                ax=ax, project=obj.main, enable_post=enable_post,
                **plot_dict['fmt'])
        # handle shared x and y-axes
        for key, names in sharex.items():
            ax_base = get_ax_base(key, names)
            if ax_base is not None:
                ax_base.get_shared_x_axes().join(
                    ax_base, *obj(arr_name=names).axes)
                for ax in obj(arr_name=names).axes:
                    ax._sharex = ax_base
        for key, names in sharey.items():
            ax_base = get_ax_base(key, names)
            if ax_base is not None:
                ax_base.get_shared_y_axes().join(
                    ax_base, *obj(arr_name=names).axes)
                for ax in obj(arr_name=names).axes:
                    ax._sharey = ax_base
        for arr in obj.with_plotter:
            shared = d['arrays'][arr.psy.arr_name]['plotter'].get('shared', {})
            for key, arr_names in six.iteritems(shared):
                arr.psy.plotter.share(obj(arr_name=arr_names).plotters,
                                      keys=[key])
        if make_plot:
            for plotter in obj.plotters:
                plotter.reinit(
                    draw=False,
                    clear=clear or (
                        clear is None and
                        plotter_cls._get_sample_projection() is not None))
            if draw is None:
                draw = rcParams['auto_draw']
            if draw:
                obj.draw()
                if rcParams['auto_show']:
                    obj.show()
        if auto_update is None:
            auto_update = rcParams['lists.auto_update']
        if not main:
            obj._main = gcp(True)
            obj.main.extend(obj, new_name=True)
        obj.no_auto_update = not auto_update
        scp(obj)
        return obj

    @classmethod
    @docstrings.get_sections(base='Project.scp')
    @dedent
    def scp(cls, project):
        """
        Set the current project

        Parameters
        ----------
        project: Project or None
            The project to set. If it is None, the current subproject is set
            to empty. If it is a sub project (see:attr:`Project.is_main`),
            the current subproject is set to this project. Otherwise it
            replaces the current main project

        See Also
        --------
        scp: The global version for setting the current project
        gcp: Returns the current project
        project: Creates a new project"""
        if project is None:
            _scp(None)
            cls.oncpchange.emit(gcp())
        elif not project.is_main:
            if project.main is not _current_project:
                _scp(project.main, True)
                cls.oncpchange.emit(project.main)
            _scp(project)
            cls.oncpchange.emit(project)
        else:
            _scp(project, True)
            cls.oncpchange.emit(project)
            sp = project[:]
            _scp(sp)
            cls.oncpchange.emit(sp)

    docstrings.delete_params('Project.parameters', 'num')

    @classmethod
    @docstrings.dedent
    def new(cls, num=None, *args, **kwargs):
        """
        Create a new main project

        Parameters
        ----------
        num: int
            The number of the project
        %(Project.parameters.no_num)s

        Returns
        -------
        Project
            The with the given `num` (if it does not already exist, it is
            created)

        See Also
        --------
        scp: Sets the current project
        gcp: Returns the current project
        """
        project = cls(*args, num=num, **kwargs)
        scp(project)
        return project

    def __str__(self):
        return (('%i Main ' % self.num) if self.is_main else '') + super(
            Project, self).__str__()


class _ProjectLoader(object):
    """Class to inspect a project and reproduce it"""

    @staticmethod
    def inspect_figure(fig):
        """Get the parameters (heigth, width, etc.) to create a figure

        This method returns the number of the figure and a dictionary
        containing the necessary information for the
        :func:`matplotlib.pyplot.figure` function"""
        return fig.number, {
            'num': fig.number,
            'figsize': (fig.get_figwidth(), fig.get_figheight()),
            'dpi': fig.get_dpi() / getattr(fig.canvas, '_dpi_ratio', 1),
            'facecolor': fig.get_facecolor(),
            'edgecolor': fig.get_edgecolor(),
            'frameon': fig.get_frameon(),
            'tight_layout': fig.get_tight_layout(),
            'subplotpars': vars(fig.subplotpars)}

    @staticmethod
    def load_figure(d, new_fig=True):
        """Create a figure from what is returned by :meth:`inspect_figure`"""
        import matplotlib.pyplot as plt
        subplotpars = d.pop('subplotpars', None)
        if subplotpars is not None:
            subplotpars.pop('validate', None)
            subplotpars.pop('_validate', None)
            subplotpars = mfig.SubplotParams(**subplotpars)
        if new_fig:
            nums = plt.get_fignums()
            if d.get('num') in nums:
                d['num'] = next(
                    i for i in range(max(plt.get_fignums()) + 1, 0, -1)
                    if i not in nums)
        return plt.figure(subplotpars=subplotpars, **d)

    @staticmethod
    def inspect_axes(ax):
        """Inspect an axes or subplot to get the initialization parameters"""
        ret = {'fig': ax.get_figure().number}
        if mpl.__version__ < '2.0':
            ret['axisbg'] = ax.get_axis_bgcolor()
        else:  # axisbg is depreceated
            ret['facecolor'] = ax.get_facecolor()
        proj = getattr(ax, 'projection', None)
        if proj is not None and not isinstance(proj, six.string_types):
            proj = (proj.__class__.__module__, proj.__class__.__name__)
        ret['projection'] = proj
        ret['visible'] = ax.get_visible()
        ret['spines'] = {}
        ret['zorder'] = ax.get_zorder()
        ret['yaxis_inverted'] = ax.yaxis_inverted()
        ret['xaxis_inverted'] = ax.xaxis_inverted()
        for key, val in ax.spines.items():
            ret['spines'][key] = {}
            for prop in ['linestyle', 'edgecolor', 'linewidth',
                         'facecolor', 'visible']:
                ret['spines'][key][prop] = getattr(val, 'get_' + prop)()
        if isinstance(ax, mfig.SubplotBase):
            sp = ax.get_subplotspec().get_topmost_subplotspec()
            ret['grid_spec'] = sp.get_geometry()[:2]
            ret['subplotspec'] = [sp.num1, sp.num2]
            ret['is_subplot'] = True
        else:
            ret['args'] = [ax.get_position(True).bounds]
            ret['is_subplot'] = False
        return ret

    @staticmethod
    def load_axes(d):
        """Create an axes or subplot from what is returned by
        :meth:`inspect_axes`"""
        import matplotlib.pyplot as plt
        fig = plt.figure(d.pop('fig', None))
        proj = d.pop('projection', None)
        spines = d.pop('spines', None)
        invert_yaxis = d.pop('yaxis_inverted', None)
        invert_xaxis = d.pop('xaxis_inverted', None)
        if mpl.__version__ >= '2.0' and 'axisbg' in d:  # axisbg is depreceated
            d['facecolor'] = d.pop('axisbg')
        elif mpl.__version__ < '2.0' and 'facecolor' in d:
            d['axisbg'] = d.pop('facecolor')
        if proj is not None and not isinstance(proj, six.string_types):
            proj = getattr(import_module(proj[0]), proj[1])()
        if d.pop('is_subplot', None):
            grid_spec = mpl.gridspec.GridSpec(*d.pop('grid_spec', (1, 1)))
            subplotspec = mpl.gridspec.SubplotSpec(
                grid_spec, *d.pop('subplotspec', (1, None)))
            return fig.add_subplot(subplotspec, projection=proj, **d)
        ret = fig.add_axes(*d.pop('args', []), projection=proj, **d)
        if spines is not None:
            for key, val in spines.items():
                ret.spines[key].update(val)
        if invert_xaxis:
            if ret.get_xlim()[0] < ret.get_xlim()[1]:
                ret.invert_xaxis()
        if invert_yaxis:
            if ret.get_ylim()[0] < ret.get_ylim()[1]:
                ret.invert_yaxis()
        return ret


class ProjectPlotter(object):
    """Plotting methods of the :class:`psyplot.project.Project` class"""

    #: the base class for new plot methods. Is set below with the
    #: :class:`PlotterInterface` class
    _plot_method_base_cls = None

    @property
    def project(self):
        return self._project if self._project is not None else gcp(True)

    def __init__(self, project=None):
        self._project = project

    docstrings.keep_params('ArrayList.from_dataset.parameters',
                           'default_slice')

    @property
    def _plot_methods(self):
        """A dictionary with mappings from plot method to their summary"""
        ret = {}
        for attr in filter(lambda s: not s.startswith("_"), dir(self)):
            obj = getattr(self, attr)
            if isinstance(obj, PlotterInterface):
                ret[attr] = obj._summary
        return ret

    def show_plot_methods(self):
        """Print the plotmethods of this instance"""
        print_func = PlotterInterface._print_func
        if print_func is None:
            print_func = six.print_
        s = "\n".join(
            "%s\n    %s" % t for t in six.iteritems(self._plot_methods))
        return print_func(s)

    @docstrings.get_sections(base='ProjectPlotter._add_data',
                              sections=['Parameters', 'Other Parameters',
                                        'Returns'])
    @docstrings.dedent
    def _add_data(self, *args, **kwargs):
        """
        Add new plots to the project

        Parameters
        ----------
        %(Project._add_data.parameters)s

        Other Parameters
        ----------------
        %(Project._add_data.other_parameters)s

        Returns
        -------
        %(Project._add_data.returns)s
        """
        # this method is just a shortcut to the :meth:`Project._add_data`
        # method but is reimplemented by subclasses as the
        # :class:`DatasetPlotter` or the :class:`DataArrayPlotter`
        return self.project._add_data(*args, **kwargs)

    @classmethod
    @docstrings.get_sections(base='ProjectPlotter._register_plotter')
    @docstrings.dedent
    def _register_plotter(cls, identifier, module, plotter_name,
                          plotter_cls=None, summary='', prefer_list=False,
                          default_slice=None, default_dims={},
                          show_examples=True,
                          example_call="filename, name=['my_variable'], ...",
                          plugin=None):
        """
        Register a plotter for making plots

        This class method registeres a plot function for the :class:`Project`
        class under the name of the given `identifier`

        Parameters
        ----------
        %(Project._register_plotter.parameters)s

        Other Parameters
        ----------------
        prefer_list: bool
            Determines the `prefer_list` parameter in the `from_dataset`
            method. If True, the plotter is expected to work with instances of
            :class:`psyplot.InteractiveList` instead of
            :class:`psyplot.InteractiveArray`.
        %(ArrayList.from_dataset.parameters.default_slice)s
        default_dims: dict
            Default dimensions that shall be used for plotting (e.g.
            {'x': slice(None), 'y': slice(None)} for longitude-latitude plots)
        show_examples: bool, optional
            If True, examples how to access the plotter documentation are
            included in class documentation
        example_call: str, optional
            The arguments and keyword arguments that shall be included in the
            example of the generated plot method. This call will then appear as
            ``>>> psy.plot.%%(identifier)s(%%(example_call)s)`` in the
            documentation
        plugin: str
            The name of the plugin
        """
        full_name = '%s.%s' % (module, plotter_name)
        if plotter_cls is not None:  # plotter has already been imported
            docstrings.params['%s.formatoptions' % (full_name)] = \
                plotter_cls.show_keys(
                    indent=4, func=str,
                    # include links in sphinx doc
                    include_links=None)
            doc_str = ('Possible formatoptions are\n\n'
                       '%%(%s.formatoptions)s') % full_name
        else:
            doc_str = ''

        summary = summary or (
            'Open and plot data via :class:`%s.%s` plotters' % (
                module, plotter_name))

        if plotter_cls is not None:
            _versions.update(get_versions(key=lambda s: s == plugin))

        class PlotMethod(cls._plot_method_base_cls):
            __doc__ = cls._gen_doc(summary, full_name, identifier,
                                   example_call, doc_str, show_examples)

            _default_slice = default_slice
            _default_dims = default_dims
            _plotter_cls = plotter_cls
            _prefer_list = prefer_list
            _plugin = plugin

            _summary = summary

        setattr(cls, identifier, PlotMethod(identifier, module, plotter_name))

    @classmethod
    def _gen_doc(cls, summary, full_name, identifier, example_call, doc_str,
                 show_examples):
        """Generate the documentation docstring for a PlotMethod"""
        ret = docstrings.dedent("""
            %s

            This plotting method adds data arrays and plots them via
            :class:`%s` plotters

            To plot data from a netCDF file type::

                >>> psy.plot.%s(%s)

            %s""" % (summary, full_name, identifier, example_call, doc_str))

        if show_examples:
            ret += '\n\n' + cls._gen_examples(identifier)
        return ret

    @classmethod
    def _gen_examples(cls, identifier):
        """Generate examples how to axes the formatoption docs"""
        return docstrings.dedent("""
            Examples
            --------
            To explore the formatoptions and their documentations, use the
            ``keys``, ``summaries`` and ``docs`` methods. For example::

                >>> import psyplot.project as psy

                # show the keys corresponding to a group or multiple
                # formatopions
                >>> psy.plot.%(id)s.keys('labels')

                # show the summaries of a group of formatoptions or of a
                # formatoption
                >>> psy.plot.%(id)s.summaries('title')

                # show the full documentation
                >>> psy.plot.%(id)s.docs('plot')

                # or access the documentation via the attribute
                >>> psy.plot.%(id)s.plot""" % {'id': identifier})


class PlotterInterface(object):
    """Base class for visualizing a data array from an predefined plotter

    See the :meth:`__call__` method for details on plotting."""

    @property
    def _logger(self):
        name = '%s.%s.%s' % (self.__module__, self.__class__.__name__,
                             self._method)
        return logging.getLogger(name)

    @property
    def is_imported(self):
        """True if the module for this plot method has been imported already"""
        return self.module in sys.modules

    @property
    def plotter_cls(self):
        """The plotter class"""
        ret = self._plotter_cls
        if ret is None:
            self._logger.debug('importing %s', self.module)
            mod = import_module(self.module)
            plotter = self.plotter_name
            if plotter not in vars(mod):
                raise ImportError("Module %r does not have a %r plotter!" % (
                    mod, plotter))
            ret = self._plotter_cls = getattr(mod, plotter)
            _versions.update(get_versions(key=lambda s: s == self._plugin))
        return ret

    _prefer_list = False
    _default_slice = None
    _default_dims = {}

    _print_func = None

    @property
    def print_func(self):
        """The function that is used to return a formatoption

        By default the :func:`print` function is used (i.e. it is printed to
        the terminal)"""
        return self._print_func or six.print_

    @print_func.setter
    def print_func(self, value):
        self._print_func = value

    def __init__(self, methodname, module, plotter_name, project_plotter=None):
        self._method = methodname
        self._project_plotter = project_plotter
        self.module = module
        self.plotter_name = plotter_name

    docstrings.delete_params('ProjectPlotter._add_data.parameters',
                             'plotter_cls')

    @docstrings.dedent
    def __call__(self, *args, **kwargs):
        """
        Parameters
        ----------
        %(ProjectPlotter._add_data.parameters.no_plotter_cls)s
        %(Project._load_preset.parameters.preset)s

        Other Parameters
        ----------------
        %(ProjectPlotter._add_data.other_parameters)s


        Returns
        -------
        %(ProjectPlotter._add_data.returns)s
        """
        preset = kwargs.pop('preset', None)
        if preset:
            preset = self._project_plotter.project._load_preset(preset)
            if len(args) >= 2:
                fmt = args[1]
            else:
                fmt = kwargs.setdefault('fmt', {})
            for key, val in preset.get(self._method, {}).items():
                fmt.setdefault(key, val)
            valid = list(self.plotter_cls._get_formatoptions())
            for key, val in preset.items():
                if key in valid:
                    fmt.setdefault(key, val)

        return self._project_plotter._add_data(
            self.plotter_cls, *args, **dict(chain(
                [('prefer_list', self._prefer_list),
                 ('default_slice', self._default_slice)],
                six.iteritems(self._default_dims), six.iteritems(kwargs))))

    def __getattr__(self, attr):
        if attr in self.plotter_cls._get_formatoptions():
            return partial(self.print_func,
                           getattr(self.plotter_cls, attr).__doc__)
        else:
            raise AttributeError(
                "%s instance does not have a %s attribute" % (
                    self.__class__.__name__, attr))

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            try:
                return getattr(instance, '_' + self._method)
            except AttributeError:
                setattr(instance, '_' + self._method, self.__class__(
                    self._method, self.module, self.plotter_name,
                    instance))
                return getattr(instance, '_' + self._method)

    def __set__(self, instance, value):
        """Actually not required. We just implement it to ensure the python
        "help" function works well"""
        setattr(instance, '_' + self._method, value)

    def __dir__(self):
        try:
            return sorted(chain(dir(self.__class__), self.__dict__,
                                self.plotter_cls._get_formatoptions()))
        except Exception:
            return sorted(chain(dir(self.__class__), self.__dict__))

    @docstrings.dedent
    def keys(self, *args, **kwargs):
        """
        Classmethod to return a nice looking table with the given formatoptions

        Parameters
        ----------
        %(Plotter.show_keys.parameters)s

        Other Parameters
        ----------------
        %(Plotter.show_keys.other_parameters)s

        Returns
        -------
        %(Plotter.show_keys.returns)s

        See Also
        --------
        summaries, docs"""
        return self.plotter_cls.show_keys(*args, **kwargs)

    @docstrings.dedent
    def summaries(self, *args, **kwargs):
        """
        Method to print the summaries of the formatoptions

        Parameters
        ----------
        %(Plotter.show_keys.parameters)s

        Other Parameters
        ----------------
        %(Plotter.show_keys.other_parameters)s

        Returns
        -------
        %(Plotter.show_keys.returns)s

        See Also
        --------
        keys, docs"""
        return self.plotter_cls.show_summaries(*args, **kwargs)

    @docstrings.dedent
    def docs(self, *args, **kwargs):
        """
        Method to print the full documentations of the formatoptions

        Parameters
        ----------
        %(Plotter.show_keys.parameters)s

        Other Parameters
        ----------------
        %(Plotter.show_keys.other_parameters)s

        Returns
        -------
        %(Plotter.show_keys.returns)s

        See Also
        --------
        keys, docs"""
        return self.plotter_cls.show_docs(*args, **kwargs)

    @docstrings.dedent
    def check_data(self, ds, name, dims, decoder=None, *args, **kwargs):
        """
        A validation method for the data shape

        Parameters
        ----------
        name: list of lists of strings
            The variable names (see the
            :meth:`~psyplot.plotter.Plotter.check_data` method of the
            :attr:`plotter_cls` attribute for details)
        dims: list of dictionaries
            The dimensions of the arrays. It will be enhanced by the default
            dimensions of this plot method
        is_unstructured: bool or list of bool
            True if the corresponding array is unstructured.
        decoder: :class:`psyplot.data.CFDecoder`, dict or a list of them
            The decoders to use per array. Dictionaries are parsed as keyword
            arguments to the :meth:`psyplot.data.CFDecoder.get_decoder`
            method

        Returns
        -------
        %(Plotter.check_data.returns)s
        """
        if isinstance(name, six.string_types):
            name = [name]
            dims = [dims]
            decoders = [decoder]
        else:
            dims = list(dims)
            decoders = list(decoder if decoder is not None else [None])
        variables = [ds[safe_list(n)[0]] for n in name]
        if decoders is None:
            decoders = [CFDecoder.get_decoder(ds, var) for var in variables]
        else:
            for i, (decoder, var) in enumerate(zip(decoders, variables)):
                if decoder is None:
                    decoder = {}
                if isinstance(decoder, dict):
                    decoders[i] = CFDecoder.get_decoder(ds, var, **decoder)
        default_slice = slice(None) if self._default_slice is None else \
            self._default_slice
        for i, (dim_dict, var, decoder) in enumerate(zip(
                dims, variables, decoders)):
            corrected = decoder.correct_dims(var, dict(chain(
                six.iteritems(self._default_dims),
                dim_dict.items())))
            # now use the default slice (we don't do this before because the
            # `correct_dims` method doesn't use 'x', 'y', 'z' and 't' (as used
            # for the _default_dims) if the real dimension name is already in
            # the dictionary)
            for dim in var.dims:
                corrected.setdefault(dim, default_slice)
            dims[i] = [
                dim for dim, val in map(lambda t: (t[0], safe_list(t[1])),
                                        six.iteritems(corrected))
                if val and (len(val) > 1 or _is_slice(val[0]))]
        return self.plotter_cls.check_data(
            name, dims, [decoder.is_unstructured(var) for decoder, var in zip(
                decoders, variables)])


# set the base class for the :class:`ProjectPlotter` plot methods
ProjectPlotter._plot_method_base_cls = PlotterInterface


class DatasetPlotterInterface(PlotterInterface):
    """Interface for the :class:`DatasetPlotter` to a plotter"""

    # there are not changes here compared to :class:`PlotterInterface`, except
    # for a different docstring for the __call__ method

    docstrings.delete_params('ProjectPlotter._add_data.parameters',
                             'plotter_cls', 'filename_or_obj')

    @docstrings.dedent
    def __call__(self, *args, **kwargs):
        """
        Parameters
        ----------
        %(ProjectPlotter._add_data.parameters.no_plotter_cls|filename_or_obj)s

        Other Parameters
        ----------------
        %(ProjectPlotter._add_data.other_parameters)s


        Returns
        -------
        %(ProjectPlotter._add_data.returns)s
        """
        return super(DatasetPlotterInterface, self).__call__(*args, **kwargs)


class DatasetPlotter(ProjectPlotter):
    """Interface between the :class:`xarray.Dataset` and the psyplot project

    This class can be used to make new plots from a given dataset and add them
    to the current :func:`psyplot.project`
    """

    _plot_method_base_cls = DatasetPlotterInterface

    def __init__(self, ds, *args, **kwargs):
        super(DatasetPlotter, self).__init__(*args, **kwargs)
        self._ds = ds

    docstrings.delete_params('ProjectPlotter._add_data.parameters',
                             'filename_or_obj')

    @docstrings.get_sections(base='ProjectPlotter._add_data',
                              sections=['Parameters', 'Other Parameters',
                                        'Returns'])
    @docstrings.dedent
    def _add_data(self, plotter_cls, *args, **kwargs):
        """
        Add new plots to the project

        Parameters
        ----------
        %(ProjectPlotter._add_data.parameters.no_filename_or_obj)s

        Other Parameters
        ----------------
        %(ProjectPlotter._add_data.other_parameters)s

        Returns
        -------
        %(ProjectPlotter._add_data.returns)s
        """
        # this method is just a shortcut to the :meth:`Project._add_data`
        # method but is reimplemented by subclasses as the
        # :class:`DatasetPlotter` or the :class:`DataArrayPlotter`
        return super(DatasetPlotter, self)._add_data(plotter_cls, self._ds,
                                                     *args, **kwargs)

    @classmethod
    def _gen_doc(cls, summary, full_name, identifier, example_call, doc_str,
                 show_examples):
        """Generate the documentation docstring for a PlotMethod"""
        # leave out the first argument
        example_call = ', '.join(map(str.strip, example_call.split(',')[1:]))
        ret = docstrings.dedent("""
            %s

            This plotting method adds data arrays and plots them via
            :class:`%s` plotters

            To plot a variable in this dataset, type::

                >>> ds.psy.plot.%s(%s)

            %s""" % (summary, full_name, identifier, example_call, doc_str))

        if show_examples:
            ret += '\n\n' + cls._gen_examples(identifier)
        return ret

    @classmethod
    def _gen_examples(cls, identifier):
        """Generate examples how to axes the formatoption docs"""
        return docstrings.dedent("""
            Examples
            --------
            To explore the formatoptions and their documentations, use the
            ``keys``, ``summaries`` and ``docs`` methods. For example::

                # show the keys corresponding to a group or multiple
                # formatopions
                >>> ds.psy.plot.%(id)s.keys('labels')

                # show the summaries of a group of formatoptions or of a
                # formatoption
                >>> ds.psy.plot.%(id)s.summaries('title')

                # show the full documentation
                >>> ds.psy.plot.%(id)s.docs('plot')

                # or access the documentation via the attribute
                >>> ds.psy.plot.%(id)s.plot""" % {'id': identifier})


class DataArrayPlotterInterface(PlotterInterface):
    """Interface for the :class:`DataArrayPlotter` to a plotter"""

    # we reimplement the call method because we do not use the
    # prefer_list, etc. keywords. And we reimplment the check_data method
    # because we use the data array directly

    docstrings.delete_params('Plotter.parameters', 'data')

    @docstrings.dedent
    def __call__(self, *args, **kwargs):
        """
        Parameters
        ----------
        %(Plotter.parameters.no_data)s


        Returns
        -------
        psyplot.plotter.Plotter
            The plotter that visualizes the data
        """
        checks, messages = self.check_data()
        if not all(checks):
            raise ValueError(
                'Cannot visualize the data using %s! Reasons:\n    %s' % (
                    self.plotter_name, '\n    '.join(filter(None, messages))))
        return self._project_plotter._add_data(
            self.plotter_cls, *args, **kwargs)

    def check_data(self, *args, **kwargs):
        """Check whether the plotter of this plot method can visualize the data
        """
        plotter_cls = self.plotter_cls
        da_list = self._project_plotter._da.psy.to_interactive_list()
        return plotter_cls.check_data(
            da_list.all_names, da_list.all_dims, da_list.is_unstructured)


class DataArrayPlotter(ProjectPlotter):
    """Interface between the :class:`xarray.Dataset` and the psyplot project

    This class can be used to make new plots from a given dataset and add them
    to the current :func:`psyplot.project`
    """

    _plot_method_base_cls = DataArrayPlotterInterface

    def __init__(self, da, *args, **kwargs):
        super(DataArrayPlotter, self).__init__(*args, **kwargs)
        self._da = getattr(da, 'arr', da)

    @docstrings.dedent
    def _add_data(self, plotter_cls, *args, **kwargs):
        """
        Visualize this data array

        Parameters
        ----------
        %(Plotter.parameters.no_data)s

        Returns
        -------
        psyplot.plotter.Plotter
            The plotter that visualizes the data
        """
        # this method is just a shortcut to the :meth:`Project._add_data`
        # method but is reimplemented by subclasses as the
        # :class:`DatasetPlotter` or the :class:`DataArrayPlotter`
        return plotter_cls(self._da, *args, **kwargs)

    @classmethod
    def _gen_doc(cls, summary, full_name, identifier, example_call, doc_str,
                 show_examples):
        """Generate the documentation docstring for a PlotMethod"""
        # leave out the first argument
        example_call = ', '.join(map(str.strip, example_call.split(',')[1:]))
        ret = docstrings.dedent("""
            %s

            This plotting method visualizes the data via a
            :class:`%s` plotters

            To plot a variable in this dataset, type::

                >>> da.psy.plot.%s()

            %s""" % (summary, full_name, identifier, doc_str))

        if show_examples:
            ret += '\n\n' + cls._gen_examples(identifier)
        return ret

    @classmethod
    def _gen_examples(cls, identifier):
        """Generate examples how to axes the formatoption docs"""
        return docstrings.dedent("""
            Examples
            --------
            To explore the formatoptions and their documentations, use the
            ``keys``, ``summaries`` and ``docs`` methods. For example::

                # show the keys corresponding to a group or multiple
                # formatopions
                >>> da.psy.plot.%(id)s.keys('labels')

                # show the summaries of a group of formatoptions or of a
                # formatoption
                >>> da.psy.plot.%(id)s.summaries('title')

                # show the full documentation
                >>> da.psy.plot.%(id)s.docs('plot')

                # or access the documentation via the attribute
                >>> da.psy.plot.%(id)s.plot""" % {'id': identifier})


if with_cdo:
    CDF_MOD_NCREADER = 'xarray'

    docstrings.keep_params('Project._add_data.parameters', 'dims',
                           'fmt', 'ax', 'make_plot', 'method')

    class Cdo(_CdoBase):

        __doc__ = docstrings.dedent(
            """
            Subclass of the original cdo.Cdo class in the cdo.py module

            Requirements are a working cdo binary and the installed cdo.py
            python module.

            For a documentation of an operator, use the python help function,
            for a list of operators, use the builtin dir function.
            Further documentation on the operators can be found here:
            https://code.zmaw.de/projects/cdo/wiki/Cdo%7Brbpy%7D
            and on the usage of the cdo.py module here:
            https://code.zmaw.de/projects/cdo

            For a demonstration script on how cdos are implemented, see the
            examples of the psyplot package

            Compared to the original cdo.Cdo class, the following things
            changed, the default cdf handler is the
            :func:`psyplot.data.open_dataset` function and the following
            keywords are implemented for each cdo operator. If any of those is
            specified, the return will be a subproject (i.e. an instance of
            :class:`psyplot.project.Project`)

            Other Parameters
            ----------------
            plot_method: str or psyplot.project.PlotterInterface
                An registered plotting function to plot the data (e.g.
                `psyplot.project.plot.mapplot` to plot on a map). If ``None``,
                no plot will be created. In any case, the returned value is a
                subproject. If string, it must correspond to the attribute of
                the :class:`psyplot.project.ProjectPlotter` class
            name: str or list of str
                The variable names to plot/extract
            %(Project._add_data.parameters.dims|fmt|ax|make_plot|method)s

            Examples
            --------
            Calculate the timmean of a 3-dimensional array and plot it on a map
            using the psy-maps package

            .. code-block:: python

                cdo = psy.Cdo()
                sp = cdo.timmean(input='ifile.nc', name='temperature',
                                 plot_method='mapplot')

            which is essentially the same as

            .. code-block:: python

                sp = cdo.timmean(input='ifile.nc', name='temperature',
                                 plot_method=psy.plot.mapplot)
                # and
                sp = psy.plot.mapplot(
                    cdo.timmean(input='ifile.nc', returnCdf=True),
                    name='temperature', plot_method=psy.plot.mapplot)
            """)

        def __init__(self, *args, **kwargs):
            if cdo_version < (1, 5):
                kwargs.setdefault('cdfMod', CDF_MOD_NCREADER)
            super(Cdo, self).__init__(*args, **kwargs)
            if cdo_version < (1, 5):
                self.loadCdf()

        def loadCdf(self, *args, **kwargs):
            """Load data handler as specified by self.cdfMod"""
            if cdo_version < (1, 5):
                def open_nc(*args, **kwargs):
                    kwargs.pop('mode', None)
                    return open_dataset(*args, **kwargs)
                if self.cdfMod == CDF_MOD_NCREADER:
                    self.cdf = open_nc
                else:
                    super(Cdo, self).loadCdf(*args, **kwargs)
            else:
                super(Cdo, self).readCdf(*args, **kwargs)

        def __getattr__(self, method_name):
            def my_get(get):
                """Wrapper for get method of Cdo class to include several plotters
                """
                @wraps(get)
                def wrapper(self, *args, **kwargs):
                    added_kwargs = {'plot_method', 'name', 'dims', 'fmt'}
                    if added_kwargs.intersection(kwargs):
                        plot_method = kwargs.pop('plot_method', None)
                        ax = kwargs.pop('ax', None)
                        make_plot = kwargs.pop('make_plot', True)
                        fmt = kwargs.pop('fmt', {})
                        dims = kwargs.pop('dims', {})
                        name = kwargs.pop('name', None)
                        method = kwargs.pop('method', 'isel')
                        if cdo_version < (1, 5):
                            kwargs['returnCdf'] = True
                        else:
                            kwargs['returnXDataset'] = True
                        ds = get(*args, **kwargs)
                        if isinstance(plot_method, six.string_types):
                            plot_method = getattr(plot, plot_method)
                        if plot_method is None:
                            ret = Project.from_dataset(
                                ds, name=name, dims=dims, method=method)
                            ret.main = gcp(True)
                            return ret
                        else:
                            return plot_method(
                                ds, name=name, fmt=fmt, dims=dims, ax=ax,
                                make_plot=make_plot, method=method)
                    else:
                        return get(*args, **kwargs)
                return wrapper

            get = my_get(super(Cdo, self).__getattr__(method_name))
            setattr(self.__class__, method_name, get)
            return get.__get__(self)


@dedent
def gcp(main=False):
    """
    Get the current project

    Parameters
    ----------
    main: bool
        If True, the current main project is returned, otherwise the current
        subproject is returned.
    See Also
    --------
    scp: Sets the current project
    project: Creates a new project"""
    if main:
        return project() if _current_project is None else _current_project
    else:
        return gcp(True) if _current_subproject is None else \
            _current_subproject


@dedent
def scp(project):
    """
    Set the current project

    Parameters
    ----------
    %(Project.scp.parameters)s

    See Also
    --------
    gcp: Returns the current project
    project: Creates a new project"""
    return PROJECT_CLS.scp(project)


def _scp(p, main=False):
    """scp version that allows a bit more control over whether the project is a
    main project or not"""
    global _current_subproject
    global _current_project
    if p is None:
        mp = project() if main or _current_project is None else \
            _current_project
        _current_subproject = Project(main=mp)
    elif not main:
        _current_subproject = p
    else:
        _current_project = p


@docstrings.dedent
def project(num=None, *args, **kwargs):
    """
    Create a new main project

    Parameters
    ----------
    num: int
        The number of the project
    %(Project.parameters.no_num)s

    Returns
    -------
    Project
        The with the given `num` (if it does not already exist, it is created)

    See Also
    --------
    scp: Sets the current project
    gcp: Returns the current project
    """
    numbers = [project.num for project in _open_projects]
    if num in numbers:
        return _open_projects[numbers.index(num)]
    if num is None:
        num = max(numbers) + 1 if numbers else 1
    project = PROJECT_CLS.new(num, *args, **kwargs)
    _open_projects.append(project)
    return project


@docstrings.dedent
def close(num=None, figs=True, data=True, ds=True, remove_only=False):
    """
    Close the project

    This method closes the current project (figures, data and datasets) or the
    project specified by `num`

    Parameters
    ----------
    num: int, None or 'all'
        if :class:`int`, it specifies the number of the project, if None, the
        current subproject is closed, if ``'all'``, all open projects are
        closed
    %(Project.close.parameters)s

    See Also
    --------
    Project.close"""
    kws = dict(figs=figs, data=data, ds=ds, remove_only=remove_only)
    cp_num = gcp(True).num
    got_cp = False
    if num is None:
        project = gcp()
        scp(None)
        project.close(**kws)
    elif num == 'all':
        for project in _open_projects[:]:
            project.close(**kws)
            got_cp = got_cp or project.main.num == cp_num
            del _open_projects[0]
    else:
        if isinstance(num, Project):
            project = num
        else:
            project = [project for project in _open_projects
                       if project.num == num][0]
        project.close(**kws)
        try:
            _open_projects.remove(project)
        except ValueError:
            pass
        got_cp = got_cp or project.main.num == cp_num
    if got_cp:
        if _open_projects:
            # set last opened project to the current
            scp(_open_projects[-1])
        else:
            _scp(None, True)  # set the current project to None


docstrings.delete_params('Project._register_plotter.parameters', 'plotter_cls')


@docstrings.dedent
def register_plotter(identifier, module, plotter_name, plotter_cls=None,
                     sorter=True, plot_func=True, import_plotter=None,
                     **kwargs):
    """
    Register a :class:`psyplot.plotter.Plotter` for the projects

    This function registers plotters for the :class:`Project` class to allow
    a dynamical handling of different plotter classes.

    Parameters
    ----------
    %(Project._register_plotter.parameters.no_plotter_cls)s
    sorter: bool, optional
        If True, the :class:`Project` class gets a new property with the name
        of the specified `identifier` which allows you to access the instances
        that are plotted by the specified `plotter_name`
    plot_func: bool, optional
        If True, the :class:`ProjectPlotter` (the class that holds the
        plotting method for the :class:`Project` class and can be accessed via
        the :attr:`Project.plot` attribute) gets an additional method to plot
        via the specified `plotter_name` (see `Other Parameters` below.)
    import_plotter: bool, optional
        If True, the plotter is automatically imported, otherwise it is only
        imported when it is needed. If `import_plotter` is None, then it is
        determined by the :attr:`psyplot.rcParams` ``'project.auto_import'``
        item.

    Other Parameters
    ----------------
    %(ProjectPlotter._register_plotter.other_parameters)s
    """
    if plotter_cls is None:
        if ((import_plotter is None and rcParams['project.auto_import']) or
                import_plotter):
            try:
                plotter_cls = getattr(import_module(module), plotter_name)
            except Exception as e:
                critical(("Could not import %s!\n" % module) +
                         e.message if six.PY2 else str(e))
                return
    if sorter:
        if hasattr(Project, identifier):
            raise ValueError(
                "Project class already has a %s attribute" % identifier)
        Project._register_plotter(
            identifier, module, plotter_name, plotter_cls)
    if plot_func:
        if hasattr(ProjectPlotter, identifier):
            raise ValueError(
                "Project class already has a %s attribute" % identifier)
        ProjectPlotter._register_plotter(
            identifier, module, plotter_name, plotter_cls, **kwargs)
        DatasetPlotter._register_plotter(
            identifier, module, plotter_name, plotter_cls, **kwargs)
        DataArrayPlotter._register_plotter(
            identifier, module, plotter_name, plotter_cls, **kwargs)
    if identifier not in registered_plotters:
        kwargs.update(dict(
            module=module, plotter_name=plotter_name, sorter=sorter,
            plot_func=plot_func, import_plotter=import_plotter))
        registered_plotters[identifier] = kwargs
    return


def unregister_plotter(identifier, sorter=True, plot_func=True):
    """
    Unregister a :class:`psyplot.plotter.Plotter` for the projects

    Parameters
    ----------
    identifier: str
        Name of the attribute that is used to filter for the instances
        belonging to this plotter or to create plots with this plotter
    sorter: bool
        If True, the identifier will be unregistered from the :class:`Project`
        class
    plot_func: bool
        If True, the identifier will be unregistered from the
        :class:`ProjectPlotter` class
    """
    d = registered_plotters.get(identifier, {})
    if sorter and hasattr(Project, identifier):
        delattr(Project, identifier)
        d['sorter'] = False
    if plot_func and hasattr(ProjectPlotter, identifier):
        for cls in [ProjectPlotter, DatasetPlotter, DataArrayPlotter]:
            delattr(cls, identifier)
        try:
            delattr(plot, '_' + identifier)
        except AttributeError:
            pass
        d['plot_func'] = False
    if sorter and plot_func:
        registered_plotters.pop(identifier, None)


registered_plotters = {}

for _identifier, _plotter_settings in rcParams['project.plotters'].items():
    register_plotter(_identifier, **_plotter_settings)


def get_project_nums():
    """Returns the project numbers of the open projects"""
    return [p.num for p in _open_projects]

#: :class:`ProjectPlotter` of the current project. See the class documentation
#: for available plotting methods
plot = ProjectPlotter()

#: The project class that is used for creating new projects
PROJECT_CLS = Project

psyplot._project_imported = True
