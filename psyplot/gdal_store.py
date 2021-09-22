# -*- coding: utf-8 -*-
"""Gdal Store for reading GeoTIFF files into an :class:`xarray.Dataset`

This module contains the definition of the :class:`GdalStore` class that can
be used to read in a GeoTIFF file into an :class:`xarray.Dataset`.
It requires that you have the python gdal module installed.

Examples
--------
to open a GeoTIFF file named ``'my_tiff.tiff'`` you can do::

    >>> from psyplot.gdal_store import GdalStore
    >>> from xarray import open_dataset
    >>> ds = open_dataset(GdalStore('my_tiff'))

Or you use the `engine` of the :func:`psyplot.open_dataset` function:

    >>> ds = open_dataset('my_tiff.tiff', engine='gdal')
"""

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

import six
from numpy import arange, nan, dtype
from xarray import Variable
from collections import OrderedDict
try:
    from xarray.core.utils import FrozenOrderedDict
except ImportError:
    FrozenOrderedDict = dict
from xarray.backends.common import AbstractDataStore
from psyplot.compat.pycompat import range
from psyplot.warning import warn
import psyplot.data as psyd
try:
    import gdal
    from osgeo import gdal_array
except ImportError as e:
    gdal = psyd._MissingModule(e)
try:
    from dask.array import Array
    with_dask = True
except ImportError:
    with_dask = False


class GdalStore(AbstractDataStore):
    """Datastore to read raster files suitable for the gdal package

    We recommend to use the :func:`psyplot.open_dataset` function to open
    a geotiff file::

        >>> ds = psyplot.open_dataset('my_geotiff.tiff', engine='gdal')

    Notes
    -----
    The :class:`GdalStore` object is not as elaborate as, for example, the
    `gdal_translate` command. Many attributes, e.g. variable names or netCDF
    dimensions will not be interpreted. We only support two
    dimensional arrays and each band is saved into one variable named like
    ``'Band1', 'Band2', ...``. If you want a more elaborate translation of your
    GDAL Raster, convert the file to a netCDF file using ``gdal_translate`` or
    the ``gdal.GetDriverByName('netCDF').CreateCopy`` method. However this
    class does not create an extra file on your hard disk as it is done by
    GDAL."""

    def __init__(self, filename_or_obj):
        """
        Parameters
        ----------
        filename_or_obj: str
            The path to the GeoTIFF file or a gdal dataset"""
        if isinstance(psyd.safe_list(filename_or_obj)[0], six.string_types):
            self.ds = gdal.Open(filename_or_obj)
            self._filename = filename_or_obj
        else:
            self.ds = filename_or_obj
            fnames = self.ds.GetFileList()
            self._filename = fnames[0] if len(fnames) == 1 else fnames

    def get_variables(self):
        def load(band):
            band = ds.GetRasterBand(band)
            a = band.ReadAsArray()
            no_data = band.GetNoDataValue()
            if no_data is not None:
                try:
                    a[a == no_data] = a.dtype.type(nan)
                except ValueError:
                    pass
            return a
        ds = self.ds
        dims = ['lat', 'lon']
        chunks = ((ds.RasterYSize,), (ds.RasterXSize,))
        shape = (ds.RasterYSize, ds.RasterXSize)
        variables = OrderedDict()
        for iband in range(1, ds.RasterCount+1):
            band = ds.GetRasterBand(iband)
            dt = dtype(gdal_array.codes[band.DataType])
            if with_dask:
                dsk = {('x', 0, 0): (load, iband)}
                arr = Array(dsk, 'x', chunks, shape=shape, dtype=dt)
            else:
                arr = load(iband)
            attrs = band.GetMetadata_Dict()
            try:
                dt.type(nan)
                attrs['_FillValue'] = nan
            except ValueError:
                no_data = band.GetNoDataValue()
                attrs.update({'_FillValue': no_data} if no_data else {})
            variables['Band%i' % iband] = Variable(dims, arr, attrs)
        variables['lat'], variables['lon'] = self._load_GeoTransform()
        return FrozenOrderedDict(variables)

    def _load_GeoTransform(self):
        """Calculate latitude and longitude variable calculated from the
        gdal.Open.GetGeoTransform method"""
        def load_lon():
            return arange(ds.RasterXSize)*b[1]+b[0]

        def load_lat():
            return arange(ds.RasterYSize)*b[5]+b[3]
        ds = self.ds
        b = self.ds.GetGeoTransform()  # bbox, interval
        if with_dask:
            lat = Array(
                {('lat', 0): (load_lat,)}, 'lat', (self.ds.RasterYSize,),
                shape=(self.ds.RasterYSize,), dtype=float)
            lon = Array(
                {('lon', 0): (load_lon,)}, 'lon', (self.ds.RasterXSize,),
                shape=(self.ds.RasterXSize,), dtype=float)
        else:
            lat = load_lat()
            lon = load_lon()
        return Variable(('lat',), lat), Variable(('lon',), lon)

    def get_attrs(self):
        from osr import SpatialReference
        attrs = self.ds.GetMetadata()
        try:
            sp = SpatialReference(wkt=self.ds.GetProjection())
            proj4 = sp.ExportToProj4()
        except:
            warn('Could not identify projection')
        else:
            attrs['proj4'] = proj4
        return FrozenOrderedDict(attrs)
