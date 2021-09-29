"""Module to test the :mod:`psyplot.gdal_store` module."""

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

import unittest
import _base_testing as bt
import pandas as pd
import psyplot.data as psyd
try:
    import gdal
except ImportError:
    gdal = False


class TestGdalStore(unittest.TestCase):
    """Class to test the :class:`psyplot.gdal_store.GdalStore` class"""

    @unittest.skipIf(not gdal, "GDAL module not installed")
    def test_open_geotiff(self):
        """Test to open a GeoTiff file"""
        ds_ref = psyd.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        ds_tiff = psyd.open_dataset(bt.get_file(
            'test-t2m-1979-01-31T18-00-00.tif'), engine='gdal')
        self.assertListEqual(
            ds_tiff.Band1.values.tolist(),
            ds_ref.isel(time=0, lev=0).t2m.values.tolist())

    @unittest.skipIf(not gdal, "GDAL module not installed")
    def test_open_mf_geotiff(self):
        """Test to open multiple GeoTiff files and extract the time from the
        file name"""
        ds_ref = psyd.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        ds_tiff = psyd.open_mfdataset(bt.get_file('test-t2m-*.tif'),
                                      engine='gdal',
                                      t_format='test-t2m-%Y-%m-%dT%H-%M-%S')
        self.assertListEqual(
            ds_ref.isel(time=[0, 1], lev=0).t2m.values.tolist(),
            ds_tiff.Band1.values.tolist())
        self.assertListEqual(
            pd.to_datetime(ds_tiff.time.values).tolist(),
            pd.to_datetime(ds_ref.time[:2].values).tolist())
