"""Module to test the :mod:`psyplot.gdal_store` module"""
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
