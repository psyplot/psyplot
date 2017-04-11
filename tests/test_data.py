"""Test module of the :mod:`psyplot.data` module"""
import os
import os.path as osp
import six
import unittest
import pandas as pd
import xarray as xr
from psyplot.compat.pycompat import range
import psyplot.data as psyd
import _base_testing as bt
import numpy as np
from collections import OrderedDict

try:
    import PyNio
    with_nio = True
except ImportError as e:
    PyNio = psyd._MissingModule(e)
    with_nio = False

try:
    import netCDF4 as nc
    with_netcdf4 = True
except ImportError as e:
    nc = psyd._MissingModule(e)
    with_netcdf4 = False

try:
    import scipy
    with_scipy = True
except ImportError as e:
    scipy = psyd._MissingModule(e)
    with_scipy = False


class AlmostArrayEqualMixin(object):

    def assertAlmostArrayEqual(self, actual, desired, rtol=1e-07, atol=0,
                               msg=None, **kwargs):
        """Asserts that the two given arrays are almost the same

        This method uses the :func:`numpy.testing.assert_allclose` function
        to compare the two given arrays.

        Parameters
        ----------
        actual : array_like
            Array obtained.
        desired : array_like
            Array desired.
        rtol : float, optional
            Relative tolerance.
        atol : float, optional
            Absolute tolerance.
        equal_nan : bool, optional.
            If True, NaNs will compare equal.
        err_msg : str, optional
            The error message to be printed in case of failure.
        verbose : bool, optional
            If True, the conflicting values are appended to the error message.
        """
        try:
            np.testing.assert_allclose(actual, desired, rtol=rtol, atol=atol,
                                       err_msg=msg or '', **kwargs)
        except AssertionError as e:
            self.fail(e if six.PY3 else e.message)


class DecoderTest(unittest.TestCase, AlmostArrayEqualMixin):
    """Test the :class:`psyplot.data.CFDecoder` class"""

    def test_1D_cf_bounds(self):
        """Test whether the CF Conventions for 1D bounaries are correct"""
        final_bounds = np.arange(-180, 181, 30)
        lon = xr.Variable(('lon', ), np.arange(-165, 166, 30),
                          {'bounds': 'lon_bounds'})
        cf_bounds = xr.Variable(('lon', 'bnds'), np.zeros((len(lon), 2)))
        for i in range(len(lon)):
            cf_bounds[i, :] = final_bounds[i:i+2]
        ds = xr.Dataset(coords={'lon': lon, 'lon_bounds': cf_bounds})
        decoder = psyd.CFDecoder(ds)
        self.assertEqual(list(final_bounds),
                         list(decoder.get_plotbounds(lon)))

    def test_1D_bounds_calculation(self):
        """Test whether the 1D cell boundaries are calculated correctly"""
        final_bounds = np.arange(-180, 181, 30)
        lon = xr.Variable(('lon', ), np.arange(-165, 166, 30))
        ds = xr.Dataset(coords={'lon': lon})
        decoder = psyd.CFDecoder(ds)
        self.assertEqual(list(final_bounds),
                         list(decoder.get_plotbounds(lon)))

    def _test_dimname(self, func_name, name, uname=None, name2d=False,
                      circ_name=None):
        def check_ds(name):
            self.assertEqual(getattr(d, func_name)(ds.t2m), name)
            self.assertEqual(getattr(d, func_name)(ds.t2m,
                             coords=ds.t2m.coords), name)
            if name2d:
                self.assertEqual(getattr(d, func_name)(ds.t2m_2d), name)
            else:
                self.assertIsNone(getattr(d, func_name)(ds.t2m_2d))
            if six.PY3:
                # Test whether the warning is raised if the decoder finds
                # multiple dimensions
                with self.assertWarnsRegex(RuntimeWarning,
                                           'multiple matches'):
                    coords = 'time lat lon lev x y latitude longitude'.split()
                    ds.t2m.attrs.pop('coordinates', None)
                    for dim in 'xytz':
                        getattr(d, dim).update(coords)
                    for coord in set(coords).intersection(ds.coords):
                        ds.coords[coord].attrs.pop('axis', None)
                    getattr(d, func_name)(ds.t2m)
        uname = uname or name
        circ_name = circ_name or name
        ds = psyd.open_dataset(os.path.join(bt.test_dir, 'test-t2m-u-v.nc'))
        d = psyd.CFDecoder(ds)
        check_ds(name)
        ds.close()
        ds = psyd.open_dataset(os.path.join(bt.test_dir, 'icon_test.nc'))
        d = psyd.CFDecoder(ds)
        check_ds(uname)
        ds.close()
        ds = psyd.open_dataset(
            os.path.join(bt.test_dir, 'circumpolar_test.nc'))
        d = psyd.CFDecoder(ds)
        check_ds(circ_name)
        ds.close()

    def _test_coord(self, func_name, name, uname=None, name2d=False,
                    circ_name=None):
        def check_ds(name):
            self.assertEqual(getattr(d, func_name)(ds.t2m).name, name)
            if name2d:
                self.assertEqual(getattr(d, func_name)(ds.t2m_2d).name, name)
            else:
                self.assertIsNone(getattr(d, func_name)(ds.t2m_2d))
            if six.PY3:
                # Test whether the warning is raised if the decoder finds
                # multiple dimensions
                with self.assertWarnsRegex(RuntimeWarning,
                                           'multiple matches'):
                    coords = 'time lat lon lev x y latitude longitude'.split()
                    ds.t2m.attrs.pop('coordinates', None)
                    for dim in 'xytz':
                        getattr(d, dim).update(coords)
                    for coord in set(coords).intersection(ds.coords):
                        ds.coords[coord].attrs.pop('axis', None)
                    getattr(d, func_name)(ds.t2m)
        uname = uname or name
        circ_name = circ_name or name
        ds = psyd.open_dataset(os.path.join(bt.test_dir, 'test-t2m-u-v.nc'))
        d = psyd.CFDecoder(ds)
        check_ds(name)
        ds.close()
        ds = psyd.open_dataset(os.path.join(bt.test_dir, 'icon_test.nc'))
        d = psyd.CFDecoder(ds)
        check_ds(uname)
        ds.close()
        ds = psyd.open_dataset(
            os.path.join(bt.test_dir, 'circumpolar_test.nc'))
        d = psyd.CFDecoder(ds)
        check_ds(circ_name)
        ds.close()

    def test_tname(self):
        """Test CFDecoder.get_tname method"""
        self._test_dimname('get_tname', 'time')

    def test_zname(self):
        """Test CFDecoder.get_zname method"""
        self._test_dimname('get_zname', 'lev')

    def test_xname(self):
        """Test CFDecoder.get_xname method"""
        self._test_dimname('get_xname', 'lon', 'ncells', True,
                           circ_name='x')

    def test_yname(self):
        """Test CFDecoder.get_yname method"""
        self._test_dimname('get_yname', 'lat', 'ncells', True,
                           circ_name='y')

    def test_t(self):
        """Test CFDecoder.get_t method"""
        self._test_coord('get_t', 'time')

    def test_z(self):
        """Test CFDecoder.get_z method"""
        self._test_coord('get_z', 'lev')

    def test_x(self):
        """Test CFDecorder.get_x method"""
        self._test_coord('get_x', 'lon', 'clon', True,
                         circ_name='longitude')

    def test_y(self):
        """Test CFDecoder.get_y method"""
        self._test_coord('get_y', 'lat', 'clat', True,
                         circ_name='latitude')

    def test_standardization(self):
        """Test the :meth:`psyplot.data.CFDecoder.standardize_dims` method"""
        ds = psyd.open_dataset(os.path.join(bt.test_dir, 'test-t2m-u-v.nc'))
        decoder = psyd.CFDecoder(ds)
        dims = {'time': 1, 'lat': 2, 'lon': 3, 'lev': 4}
        replaced = decoder.standardize_dims(ds.t2m, dims)
        for dim, rep in [('time', 't'), ('lat', 'y'), ('lon', 'x'),
                         ('lev', 'z')]:
            self.assertIn(rep, replaced)
            self.assertEqual(replaced[rep], dims[dim],
                             msg="Wrong value for %s (%s-) dimension" % (
                                 dim, rep))

    def test_idims(self):
        """Test the extraction of the slicers of the dimensions"""
        ds = psyd.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        arr = ds.t2m[1:, 1]
        arr.psy.init_accessor(base=ds)
        dims = arr.psy.idims
        for dim in ['time', 'lev', 'lat', 'lon']:
            self.assertEqual(
                psyd.safe_list(ds[dim][dims[dim]]),
                psyd.safe_list(arr.coords[dim]),
                msg="Slice %s for dimension %s is wrong!" % (dims[dim], dim))
        # test with unknown dimensions
        if xr.__version__ >= '0.9':
            ds = ds.drop('time')
            arr = ds.t2m[1:, 1]
            arr.psy.init_accessor(base=ds)
            if not six.PY2:
                with self.assertWarnsRegex(UserWarning, 'time'):
                    dims = arr.psy.idims
            l = psyd.ArrayList.from_dataset(
                ds, name='t2m', time=slice(1, None), lev=85000., method='sel')
            arr = l[0]
            dims = arr.psy.idims
            for dim in ['time', 'lev', 'lat', 'lon']:
                if dim == 'time':
                    self.assertEqual(dims[dim], slice(1, 5, 1))
                else:
                    self.assertEqual(
                        psyd.safe_list(ds[dim][dims[dim]]),
                        psyd.safe_list(arr.coords[dim]),
                        msg="Slice %s for dimension %s is wrong!" % (dims[dim],
                                                                     dim))

    def test_triangles(self):
        """Test the creation of triangles"""
        ds = psyd.open_dataset(os.path.join(bt.test_dir, 'icon_test.nc'))
        decoder = psyd.CFDecoder(ds)
        var = ds.t2m[0, 0]
        var.attrs.pop('grid_type', None)
        self.assertTrue(decoder.is_triangular(var))
        self.assertTrue(decoder.is_unstructured(var))
        triangles = decoder.get_triangles(var)
        self.assertEqual(len(triangles.triangles), var.size)

        # Test for correct falsification
        ds = psyd.open_dataset(os.path.join(bt.test_dir, 'test-t2m-u-v.nc'))
        decoder = psyd.CFDecoder(ds)
        self.assertFalse(decoder.is_triangular(ds.t2m[0, 0]))
        self.assertFalse(decoder.is_unstructured(ds.t2m[0, 0]))

    def test_is_circumpolar(self):
        """Test whether the is_circumpolar method works"""
        ds = psyd.open_dataset(os.path.join(bt.test_dir,
                                            'circumpolar_test.nc'))
        decoder = psyd.CFDecoder(ds)
        self.assertTrue(decoder.is_circumpolar(ds.t2m))

        # test for correct falsification
        ds = psyd.open_dataset(os.path.join(bt.test_dir, 'icon_test.nc'))
        decoder = psyd.CFDecoder(ds)
        self.assertFalse(decoder.is_circumpolar(ds.t2m))

    def test_get_variable_by_axis(self):
        """Test the :meth:`CFDecoder.get_variable_by_axis` method"""
        ds = psyd.open_dataset(os.path.join(bt.test_dir,
                                            'circumpolar_test.nc'))
        decoder = psyd.CFDecoder(ds)
        arr = ds.t2m
        arr.attrs.pop('coordinates', None)
        for c in ds.coords.values():
            c.attrs.pop('axis', None)
        for dim in ['x', 'y', 'z', 't']:
            self.assertIsNone(decoder.get_variable_by_axis(arr, dim),
                              msg="Accidently found coordinate %s" % dim)

        # test coordinates attribute
        arr.attrs['coordinates'] = 'latitude longitude'
        self.assertEqual(decoder.get_variable_by_axis(arr, 'x').name,
                         'longitude')
        self.assertEqual(decoder.get_variable_by_axis(arr, 'y').name,
                         'latitude')
        self.assertIsNone(decoder.get_variable_by_axis(arr, 'z'))

        # test coordinates attribute but without specifying axis or matching
        # latitude or longitude
        axes = {'lev': 'z', 'time': 't', 'x': 'x', 'y': 'y'}
        arr.attrs['coordinates'] = 'time lev y x'
        for name, axis in axes.items():
            self.assertEqual(
                decoder.get_variable_by_axis(arr, axis).name, name)

        # test with specified axis attribute
        arr.attrs['coordinates'] = 'time lev longitude latitude'
        axes = {'lev': 'Z', 'time': 'T', 'latitude': 'X', 'longitude': 'Y'}
        for name, axis in axes.items():
            ds.coords[name].attrs['axis'] = axis
        for name, axis in axes.items():
            self.assertEqual(
                decoder.get_variable_by_axis(arr, axis.lower()).name, name)

        # close the dataset
        ds.close()

    def test_plot_bounds_1d(self):
        """Test to get 2d-interval breaks"""
        x = xr.Variable(('x', ), np.arange(1, 5))
        d = psyd.CFDecoder()
        bounds = d.get_plotbounds(x)
        self.assertAlmostArrayEqual(bounds, np.arange(0.5, 4.51, 1.0))

    def test_plot_bounds_2d(self):
        x = np.arange(1, 5)
        y = np.arange(5, 10)
        x2d, y2d = np.meshgrid(x, y)
        x_bnds = np.arange(0.5, 4.51, 1.0)
        y_bnds = np.arange(4.5, 9.51, 1.0)
        # the borders are not modified
        x_bnds[0] = 1.0
        x_bnds[-1] = 4.0
        y_bnds[0] = 5.0
        y_bnds[-1] = 9.0
        x2d_bnds, y2d_bnds = np.meshgrid(x_bnds, y_bnds)
        d = psyd.CFDecoder()
        # test x bounds
        bounds = d.get_plotbounds(xr.Variable(('y', 'x'), x2d))
        self.assertAlmostArrayEqual(bounds, x2d_bnds)

        # test y bounds
        bounds = d.get_plotbounds(xr.Variable(('y', 'x'), y2d))
        self.assertAlmostArrayEqual(bounds, y2d_bnds)


class UGridDecoderTest(unittest.TestCase, AlmostArrayEqualMixin):
    """Test the :class:`psyplot.data.UGridDecoder` class"""

    def test_get_decoder(self):
        """Test to get the right decoder"""
        ds = psyd.open_dataset(bt.get_file('simple_triangular_grid_si0.nc'))
        d = psyd.CFDecoder.get_decoder(ds, ds.Mesh2_fcvar)
        self.assertIsInstance(d, psyd.UGridDecoder)
        return ds, d

    def test_x(self):
        """Test the get_x method"""
        ds, d = self.test_get_decoder()
        x = d.get_x(ds.Mesh2_fcvar)
        self.assertIn('standard_name', x.attrs)
        self.assertEqual(x.attrs['standard_name'], 'longitude')
        self.assertAlmostArrayEqual(x.values, [0.3, 0.56666667])

    def test_y(self):
        """Test the get_y method"""
        ds, d = self.test_get_decoder()
        y = d.get_y(ds.Mesh2_fcvar)
        self.assertIn('standard_name', y.attrs)
        self.assertEqual(y.attrs['standard_name'], 'latitude')
        self.assertAlmostArrayEqual(y.values, [0.4, 0.76666668])


class TestInteractiveArray(unittest.TestCase):
    """Test the :class:`psyplot.data.InteractiveArray` class"""

    def test_auto_update(self):
        """Test the :attr:`psyplot.plotter.Plotter.no_auto_update` attribute"""
        ds = psyd.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        arr = ds.psy.t2m.psy[0, 0, 0]
        arr.psy.init_accessor(auto_update=False)

        arr.psy.update(time=1)
        self.assertEqual(arr.time, ds.time[0])
        arr.psy.start_update()
        self.assertEqual(arr.time, ds.time[1])

        arr.psy.no_auto_update = False
        arr.psy.update(time=2)
        self.assertEqual(arr.time, ds.time[2])

    def test_update_01_isel(self):
        """test the update of a single array through the isel method"""
        ds = psyd.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        arr = ds.psy.t2m.psy[0, 0, 0]
        arr.attrs['test'] = 4
        self.assertNotIn('test', ds.t2m.attrs)
        self.assertIs(arr.psy.base, ds)
        self.assertEqual(dict(arr.psy.idims), {'time': 0, 'lev': 0, 'lat': 0,
                                               'lon': slice(None)})
        # update to next time step
        arr.psy.update(time=1)
        self.assertEqual(arr.time, ds.time[1])
        self.assertEqual(arr.values.tolist(),
                         ds.t2m[1, 0, 0, :].values.tolist())
        self.assertEqual(dict(arr.psy.idims), {'time': 1, 'lev': 0, 'lat': 0,
                                               'lon': slice(None)})
        self.assertNotIn('test', ds.t2m.attrs)
        self.assertIn('test', arr.attrs)
        self.assertEqual(arr.test, 4)

    def test_update_02_sel(self):
        """test the update of a single array through the sel method"""
        ds = psyd.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        arr = ds.psy.t2m.psy[0, 0, 0]
        arr.attrs['test'] = 4
        self.assertNotIn('test', ds.t2m.attrs)
        self.assertIs(arr.psy.base, ds)
        self.assertEqual(dict(arr.psy.idims), {'time': 0, 'lev': 0, 'lat': 0,
                                               'lon': slice(None)})
        # update to next time step
        arr.psy.update(time='1979-02-28T18:00', method='nearest')
        self.assertEqual(arr.time, ds.time[1])
        self.assertEqual(arr.values.tolist(),
                         ds.t2m[1, 0, 0, :].values.tolist())
        self.assertEqual(dict(arr.psy.idims), {'time': 1, 'lev': 0, 'lat': 0,
                                               'lon': slice(None)})
        self.assertNotIn('test', ds.t2m.attrs)
        self.assertIn('test', arr.attrs)
        self.assertEqual(arr.test, 4)

    def test_update_03_isel_concat(self):
        """test the update of a concatenated array through the isel method"""
        ds = psyd.open_dataset(bt.get_file('test-t2m-u-v.nc'))[['t2m', 'u']]
        arr = ds.psy.to_array().psy.isel(time=0, lev=0, lat=0)
        arr.attrs['test'] = 4
        self.assertNotIn('test', ds.t2m.attrs)
        arr.name = 'something'
        self.assertIs(arr.psy.base, ds)
        self.assertEqual(dict(arr.psy.idims), {'time': 0, 'lev': 0, 'lat': 0,
                                               'lon': slice(None)})
        self.assertEqual(arr.coords['variable'].values.tolist(), ['t2m', 'u'])
        # update to next time step
        arr.psy.update(time=1)
        self.assertEqual(arr.time, ds.time[1])
        self.assertEqual(arr.coords['variable'].values.tolist(), ['t2m', 'u'])
        self.assertEqual(arr.values.tolist(),
                         ds[['t2m', 'u']].to_array()[
                             :, 1, 0, 0, :].values.tolist())
        self.assertEqual(dict(arr.psy.idims), {'time': 1, 'lev': 0, 'lat': 0,
                                               'lon': slice(None)})
        self.assertNotIn('test', ds.t2m.attrs)
        self.assertIn('test', arr.attrs)
        self.assertEqual(arr.test, 4)
        self.assertEqual(arr.name, 'something')

    def test_update_04_sel_concat(self):
        """test the update of a concatenated array through the isel method"""
        ds = psyd.open_dataset(bt.get_file('test-t2m-u-v.nc'))[['t2m', 'u']]
        arr = ds.psy.to_array().psy.isel(time=0, lev=0, lat=0)
        arr.attrs['test'] = 4
        self.assertNotIn('test', ds.t2m.attrs)
        self.assertIs(arr.psy.base, ds)
        self.assertEqual(dict(arr.psy.idims), {'time': 0, 'lev': 0, 'lat': 0,
                                               'lon': slice(None)})
        self.assertEqual(arr.coords['variable'].values.tolist(), ['t2m', 'u'])
        # update to next time step
        arr.psy.update(time='1979-02-28T18:00', method='nearest')
        self.assertEqual(arr.time, ds.time[1])
        self.assertEqual(arr.coords['variable'].values.tolist(), ['t2m', 'u'])
        self.assertEqual(arr.values.tolist(),
                         ds[['t2m', 'u']].to_array()[
                             :, 1, 0, 0, :].values.tolist())
        self.assertEqual(dict(arr.psy.idims), {'time': 1, 'lev': 0, 'lat': 0,
                                               'lon': slice(None)})
        self.assertNotIn('test', ds.t2m.attrs)
        self.assertIn('test', arr.attrs)
        self.assertEqual(arr.test, 4)

    def test_update_05_1variable(self):
        """Test to change the variable"""
        ds = psyd.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        arr = ds.psy.t2m.psy[0, 0, 0]
        arr.attrs['test'] = 4
        self.assertNotIn('test', ds.t2m.attrs)
        self.assertIs(arr.psy.base, ds)
        self.assertEqual(dict(arr.psy.idims), {'time': 0, 'lev': 0, 'lat': 0,
                                               'lon': slice(None)})
        # update to next time step
        arr.psy.update(name='u', time=1)
        self.assertEqual(arr.time, ds.time[1])
        self.assertEqual(arr.name, 'u')
        self.assertEqual(arr.values.tolist(),
                         ds.u[1, 0, 0, :].values.tolist())
        self.assertEqual(dict(arr.psy.idims), {'time': 1, 'lev': 0, 'lat': 0,
                                               'lon': slice(None)})
        self.assertNotIn('test', ds.t2m.attrs)
        self.assertIn('test', arr.attrs)
        self.assertEqual(arr.test, 4)

    def test_update_06_2variables(self):
        """test the change of the variable of a concatenated array"""
        ds = psyd.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        arr = ds[['t2m', 'u']].to_array().isel(time=0, lev=0, lat=0)
        arr.attrs['test'] = 4
        self.assertNotIn('test', ds.t2m.attrs)
        arr.name = 'something'
        arr.psy.base = ds
        self.assertEqual(dict(arr.psy.idims), {'time': 0, 'lev': 0, 'lat': 0,
                                               'lon': slice(None)})
        self.assertEqual(arr.coords['variable'].values.tolist(), ['t2m', 'u'])
        # update to next time step
        arr.psy.update(time=1, name=['u', 'v'])
        self.assertEqual(arr.time, ds.time[1])
        self.assertEqual(arr.coords['variable'].values.tolist(), ['u', 'v'])
        self.assertEqual(arr.values.tolist(),
                         ds[['u', 'v']].to_array()[
                             :, 1, 0, 0, :].values.tolist())
        self.assertEqual(dict(arr.psy.idims), {'time': 1, 'lev': 0, 'lat': 0,
                                               'lon': slice(None)})
        self.assertNotIn('test', ds.t2m.attrs)
        self.assertIn('test', arr.attrs)
        self.assertEqual(arr.test, 4)
        self.assertEqual(arr.name, 'something')


class TestArrayList(unittest.TestCase):
    """Test the :class:`psyplot.data.ArrayList` class"""

    list_class = psyd.ArrayList

    def test_setup_coords(self):
        """Set the :func:`psyplot.data.setup_coords` function"""
        coords = {'first': [1, 2]}
        self.assertEqual(psyd.setup_coords(second=3, **coords),
                         {'arr0': {'first': 1, 'second': 3},
                          'arr1': {'first': 2, 'second': 3}})
        self.assertEqual(psyd.setup_coords(dims=coords, second=3),
                         {'arr0': {'first': 1, 'second': 3},
                          'arr1': {'first': 2, 'second': 3}})
        coords['third'] = [1, 2, 3]
        # test sorting
        ret = psyd.setup_coords(arr_names='test{}', second=3,
                                sort=['third', 'first'], **coords)
        self.assertEqual(ret, {
            'test0': {'third': 1, 'first': 1, 'second': 3},
            'test1': {'third': 1, 'first': 2, 'second': 3},
            'test2': {'third': 2, 'first': 1, 'second': 3},
            'test3': {'third': 2, 'first': 2, 'second': 3},
            'test4': {'third': 3, 'first': 1, 'second': 3},
            'test5': {'third': 3, 'first': 2, 'second': 3}})

    @property
    def _filter_test_ds(self):
        return xr.Dataset(
            {'v0': xr.Variable(('ydim', 'xdim'), np.zeros((4, 4)),
                               attrs={'test': 1, 'test2': 1}),
             'v1': xr.Variable(('xdim', ), np.zeros(4), attrs={'test': 2,
                                                               'test2': 2}),
             'v2': xr.Variable(('xdim', ), np.zeros(4), attrs={'test': 3,
                                                               'test2': 3})},
            {'ydim': xr.Variable(('ydim', ), np.arange(1, 5)),
             'xdim': xr.Variable(('xdim', ), np.arange(4))})

    def test_filter_1_name(self):
        """Test the filtering of the ArrayList"""
        ds = self._filter_test_ds
        l = self.list_class.from_dataset(ds, ydim=0)
        l.extend(self.list_class.from_dataset(ds, ydim=1, name='v0'),
                 new_name=True)
        # filter by name
        self.assertEqual([arr.name for arr in l(name='v1')],
                         ['v1'])
        self.assertEqual([arr.name for arr in l(name=['v1', 'v2'])],
                         ['v1', 'v2'])
        self.assertEqual(
            [arr.psy.arr_name for arr in l(
                 arr_name=lambda name: name == 'arr1')], ['arr1'])

    def test_filter_2_arr_name(self):
        """Test the filtering of the ArrayList"""
        ds = self._filter_test_ds
        l = self.list_class.from_dataset(ds, ydim=0)
        l.extend(self.list_class.from_dataset(ds, ydim=1, name='v0'),
                 new_name=True)
        # fillter by array name
        self.assertEqual([arr.psy.arr_name for arr in l(arr_name='arr1')],
                         ['arr1'])
        self.assertEqual([arr.psy.arr_name for arr in l(arr_name=['arr1',
                                                                  'arr2'])],
                         ['arr1', 'arr2'])
        self.assertEqual(
            [arr.psy.arr_name for arr in l(
                 name=lambda name: name == 'v1')], ['arr1'])

    def test_filter_3_attribute(self):
        """Test the filtering of the ArrayList"""
        ds = self._filter_test_ds
        l = self.list_class.from_dataset(ds, ydim=0)
        l.extend(self.list_class.from_dataset(ds, ydim=1, name='v0'),
                 new_name=True)
        # filter by attribute
        self.assertEqual([arr.name for arr in l(test=2)], ['v1'])
        self.assertEqual([arr.name for arr in l(test=[2, 3])],
                         ['v1', 'v2'])
        self.assertEqual([arr.name for arr in l(test=[1, 2], test2=2)],
                         ['v1'])
        self.assertEqual(
            [arr.psy.arr_name for arr in l(test=lambda val: val == 2)],
            ['arr1'])

    def test_filter_4_coord(self):
        """Test the filtering of the ArrayList"""
        ds = self._filter_test_ds
        l = self.list_class.from_dataset(ds, ydim=0)
        l.extend(self.list_class.from_dataset(ds, ydim=1, name='v0'),
                 new_name=True)
        # filter by coordinate
        self.assertEqual([arr.psy.arr_name for arr in l(y=0)], ['arr0'])
        self.assertEqual([arr.psy.arr_name for arr in l(y=1)], ['arr3'])
        self.assertEqual([arr.psy.arr_name for arr in l(y=1, method='sel')],
                         ['arr0'])
        self.assertEqual(
            [arr.psy.arr_name for arr in l(y=lambda val: val == 0)], ['arr0'])

    def test_filter_5_mixed(self):
        """Test the filtering of the ArrayList"""
        ds = self._filter_test_ds
        l = self.list_class.from_dataset(ds, ydim=0)
        l.extend(self.list_class.from_dataset(ds, ydim=1, name='v0'),
                 new_name=True)
        # mix criteria
        self.assertEqual(
            [arr.psy.arr_name for arr in l(arr_name=['arr0', 'arr1'], test=1)],
            ['arr0'])

    def test_list_filter_1_name(self):
        """Test the filtering of InteractiveList by the variable name"""
        ds = self._filter_test_ds
        l = self.list_class.from_dataset(ds, name='v1', ydim=[0, 1],
                                         prefer_list=True)
        l.extend(self.list_class.from_dataset(ds, name='v2', xdim=[0, 1],
                                              prefer_list=True), new_name=True)
        self.assertEqual([arr.psy.arr_name for arr in l(name='v1')],
                         ['arr0'])
        self.assertEqual([arr.psy.arr_name for arr in l(name='v2')],
                         ['arr1'])
        self.assertEqual(
            [arr.psy.arr_name for arr in l(name=lambda n: n == 'v1')],
            ['arr0'])

    def test_list_filter_2_arr_name(self):
        """Test the filtering of InteractiveList by the array name"""
        ds = self._filter_test_ds
        l = self.list_class.from_dataset(ds, name='v1', ydim=[0, 1],
                                         prefer_list=True)
        l.extend(self.list_class.from_dataset(ds, name='v2', xdim=[0, 1],
                                              prefer_list=True), new_name=True)
        self.assertEqual([arr.psy.arr_name for arr in l(arr_name='arr0')],
                         ['arr0'])
        self.assertEqual([arr.psy.arr_name for arr in l(arr_name='arr1')],
                         ['arr1'])
        self.assertEqual(
            [arr.psy.arr_name for arr in l(arr_name=lambda an: an == 'arr0')],
            ['arr0'])

    def test_list_filter_3_attribute(self):
        """Test the filtering of InteractiveList by attribute"""
        ds = self._filter_test_ds
        l = self.list_class.from_dataset(ds, name='v1', ydim=[0, 1],
                                         prefer_list=True)
        l.extend(self.list_class.from_dataset(ds, name='v2', xdim=[0, 1],
                                              prefer_list=True), new_name=True)
        self.assertEqual([arr.psy.arr_name for arr in l(test=2)],
                         ['arr0'])
        self.assertEqual([arr.psy.arr_name for arr in l(test=3)],
                         ['arr1'])
        self.assertEqual(
            [arr.psy.arr_name for arr in l(test=lambda i: i == 2)],
            ['arr0'])

    def test_list_filter_4_coord(self):
        """Test the filtering of InteractiveList by the coordinate"""
        ds = self._filter_test_ds
        l = self.list_class.from_dataset(ds, name=['v1', 'v2'], xdim=0,
                                         prefer_list=True)
        l.extend(
            self.list_class.from_dataset(ds, name=['v1', 'v2'], xdim=1,
                                         prefer_list=True), new_name=True)
        self.assertEqual([arr.psy.arr_name for arr in l(xdim=0)],
                         ['arr0'])
        self.assertEqual([arr.psy.arr_name for arr in l(xdim=1)],
                         ['arr1'])
        self.assertEqual([arr.psy.arr_name for arr in l(xdim=1, method='sel')],
                         ['arr1'])
        self.assertEqual(
            [arr.psy.arr_name for arr in l(xdim=lambda i: i == 0)],
            ['arr0'])
        self.assertEqual(
            [arr.psy.arr_name for arr in l(xdim=lambda i: i == 1,
                                           method='sel')],
            ['arr1'])

    def test_list_filter_5_coord_list(self):
        """Test the filtering of InteractiveList by the coordinate with a list
        """
        ds = self._filter_test_ds
        l = self.list_class.from_dataset(ds, name='v0', ydim=[0, 1],
                                         prefer_list=True)
        l.extend(
            self.list_class.from_dataset(ds, name='v0', ydim=[2, 3],
                                         prefer_list=True), new_name=True)
        self.assertEqual([arr.psy.arr_name for arr in l(ydim=[0, 1])],
                         ['arr0'])
        self.assertEqual([arr.psy.arr_name for arr in l(ydim=[2, 3])],
                         ['arr1'])
        self.assertEqual([arr.psy.arr_name for arr in l(ydim=[1, 2],
                                                        method='sel')],
                         ['arr0'])
        self.assertEqual([arr.psy.arr_name for arr in l(ydim=[3, 4],
                                                        method='sel')],
                         ['arr1'])

    def test_list_filter_6_mixed(self):
        """Test the filtering of InteractiveList by attribute"""
        ds = self._filter_test_ds
        l = self.list_class.from_dataset(ds, name='v0', ydim=[0, 1],
                                         prefer_list=True)
        l.extend(self.list_class.from_dataset(ds, name='v0', ydim=[2, 3],
                                              prefer_list=True), new_name=True)
        self.assertEqual(
            [arr.psy.arr_name for arr in l(name='v0', ydim=[2, 3])],
            ['arr1'])

    @property
    def _from_dataset_test_variables(self):
        """The variables and coords needed for the from_dataset tests"""
        variables = {
             # 3d-variable
             'v0': xr.Variable(('time', 'ydim', 'xdim'), np.zeros((4, 4, 4))),
             # 2d-variable with time and x
             'v1': xr.Variable(('time', 'xdim', ), np.zeros((4, 4))),
             # 2d-variable with y and x
             'v2': xr.Variable(('ydim', 'xdim', ), np.zeros((4, 4))),
             # 1d-variable
             'v3': xr.Variable(('xdim', ), np.zeros(4))}
        coords = {
            'ydim': xr.Variable(('ydim', ), np.arange(1, 5)),
            'xdim': xr.Variable(('xdim', ), np.arange(4)),
            'time': xr.Variable(
                ('time', ),
                pd.date_range('1999-01-01', '1999-05-01', freq='M').values)}
        return variables, coords

    def test_from_dataset_01_basic(self):
        """test creation without any additional information"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        l = self.list_class.from_dataset(ds)
        self.assertEqual(len(l), 4)
        self.assertEqual(set(l.names), set(variables))
        for arr in l:
            self.assertEqual(arr.dims, variables[arr.name].dims,
                             msg="Wrong dimensions for variable " + arr.name)
            self.assertEqual(arr.shape, variables[arr.name].shape,
                             msg="Wrong shape for variable " + arr.name)

    def test_from_dataset_02_name(self):
        """Test the from_dataset creation method with selected names"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        l = self.list_class.from_dataset(ds, name="v2")
        self.assertEqual(len(l), 1)
        self.assertEqual(set(l.names), {"v2"})
        for arr in l:
            self.assertEqual(arr.dims, variables[arr.name].dims,
                             msg="Wrong dimensions for variable " + arr.name)
            self.assertEqual(arr.shape, variables[arr.name].shape,
                             msg="Wrong shape for variable " + arr.name)

    def test_from_dataset_03_simple_selection(self):
        """Test the from_dataset creation method with x- and t-selection"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        l = self.list_class.from_dataset(ds, x=0, t=0)
        self.assertEqual(len(l), 4)
        self.assertEqual(set(l.names), set(variables))
        for arr in l:
            self.assertEqual(arr.xdim.ndim, 0,
                             msg="Wrong x dimension for " + arr.name)
            if 'time' in arr.dims:
                self.assertEqual(arr.time, coords['time'],
                                 msg="Wrong time dimension for " + arr.name)

    def test_from_dataset_04_exact_selection(self):
        """Test the from_dataset creation method with selected names"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        l = self.list_class.from_dataset(ds, ydim=2, method=None,
                                         name=['v0', 'v2'])
        self.assertEqual(len(l), 2)
        self.assertEqual(set(l.names), {'v0', 'v2'})
        for arr in l:
            self.assertEqual(arr.ydim, 2,
                             msg="Wrong ydim slice for " + arr.name)

    def test_from_dataset_05_exact_array_selection(self):
        """Test the from_dataset creation method with selected names"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        l = self.list_class.from_dataset(ds, ydim=[[2, 3]], method=None,
                                         name=['v0', 'v2'])
        self.assertEqual(len(l), 2)
        self.assertEqual(set(l.names), {'v0', 'v2'})
        for arr in l:
            self.assertEqual(arr.ydim.values.tolist(), [2, 3],
                             msg="Wrong ydim slice for " + arr.name)

    def test_from_dataset_06_nearest_selection(self):
        """Test the from_dataset creation method with selected names"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        l = self.list_class.from_dataset(ds, ydim=1.7, method='nearest',
                                         name=['v0', 'v2'])
        self.assertEqual(len(l), 2)
        self.assertEqual(set(l.names), {'v0', 'v2'})
        for arr in l:
            self.assertEqual(arr.ydim, 2,
                             msg="Wrong ydim slice for " + arr.name)

    def test_from_dataset_07_time_selection(self):
        """Test the from_dataset creation method with selected names"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        l = self.list_class.from_dataset(ds, t='1999-02-28', method=None,
                                         name=['v0', 'v1'])
        self.assertEqual(len(l), 2)
        self.assertEqual(set(l.names), {'v0', 'v1'})
        for arr in l:
            self.assertEqual(arr.time, coords['time'][1],
                             msg="Wrong time slice for " + arr.name)

    def test_from_dataset_08_time_array_selection(self):
        """Test the from_dataset creation method with selected names"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        # test with array of time
        l = self.list_class.from_dataset(ds, t=[coords['time'][1:3]],
                                         method=None, name=['v0', 'v1'])
        self.assertEqual(len(l), 2)
        self.assertEqual(set(l.names), {'v0', 'v1'})
        for arr in l:
            self.assertEqual(arr.time.values.tolist(),
                             coords['time'][1:3].values.tolist(),
                             msg="Wrong time slice for " + arr.name)

    def test_from_dataset_09_nearest_time_selection(self):
        """Test the from_dataset creation method with selected names"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        l = self.list_class.from_dataset(ds, t='1999-02-20', method='nearest',
                                         name=['v0', 'v1'])
        self.assertEqual(len(l), 2)
        self.assertEqual(set(l.names), {'v0', 'v1'})
        for arr in l:
            self.assertEqual(arr.time, coords['time'][1],
                             msg="Wrong time slice for " + arr.name)

    def test_from_dataset_10_2_vars(self):
        """Test the creation of arrays out of two variables"""
        variables, coords = self._from_dataset_test_variables
        variables['v4'] = variables['v3'].copy()
        ds = xr.Dataset(variables, coords)
        l = self.list_class.from_dataset(ds, name=[['v3', 'v4'], 'v2'],
                                         xdim=[[2]], squeeze=False)
        self.assertEqual(len(l), 2)
        self.assertIn('variable', l[0].dims)
        self.assertEqual(l[0].coords['variable'].values.tolist(), ['v3', 'v4'])
        self.assertEqual(l[0].ndim, 2)

        self.assertEqual(l[1].name, 'v2')
        self.assertEqual(l[1].ndim, variables['v2'].ndim)

    def test_from_dataset_11_list(self):
        """Test the creation of a list of InteractiveLists"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        # Create two lists, each containing two arrays of variables v1 and v2.
        # In the first list, the xdim dimensions are 0 and 1.
        # In the second, the xdim dimensions are both 2
        l = self.list_class.from_dataset(
            ds, name=[['v1', 'v2']], xdim=[[0, 1], 2], prefer_list=True)

        self.assertEqual(len(l), 2)
        self.assertIsInstance(l[0], psyd.InteractiveList)
        self.assertIsInstance(l[1], psyd.InteractiveList)
        self.assertEqual(len(l[0]), 2)
        self.assertEqual(len(l[1]), 2)
        self.assertEqual(l[0][0].xdim, 0)
        self.assertEqual(l[0][1].xdim, 1)
        self.assertEqual(l[1][0].xdim, 2)
        self.assertEqual(l[1][1].xdim, 2)

    def test_from_dataset_12_list_and_2_vars(self):
        """Test the creation of a list of Interactive lists with one array out
        of 2 variables"""
        variables, coords = self._from_dataset_test_variables
        variables['v4'] = variables['v3'].copy()
        ds = xr.Dataset(variables, coords)
        l = ds.psy.create_list(
            ds, name=[['v1', ['v3', 'v4']], ['v1', 'v2']], prefer_list=True)

        self.assertEqual(len(l), 2)
        self.assertIsInstance(l[0], psyd.InteractiveList)
        self.assertIsInstance(l[1], psyd.InteractiveList)
        self.assertEqual(len(l[0]), 2)
        self.assertEqual(len(l[1]), 2)

    def test_array_info(self):
        variables, coords = self._from_dataset_test_variables
        variables['v4'] = variables['v3'].copy()
        ds = xr.Dataset(variables, coords)
        fname = osp.relpath(bt.get_file('test-t2m-u-v.nc'), '.')
        ds2 = xr.open_dataset(fname)
        l = ds.psy.create_list(
            name=[['v1', ['v3', 'v4']], ['v1', 'v2']], prefer_list=True)
        l.extend(ds2.psy.create_list(name=['t2m'], x=0, t=1),
                 new_name=True)
        self.assertEqual(l.array_info(engine='netCDF4'), OrderedDict([
            # first list contating an array with two variables
            ('arr0', OrderedDict([
                ('arr0', {'dims': {'t': slice(None), 'x': slice(None)},
                          'attrs': OrderedDict(), 'store': (None, None),
                          'name': 'v1', 'fname': None}),
                ('arr1', {'dims': {'y': slice(None)},
                          'attrs': OrderedDict(), 'store': (None, None),
                          'name': [['v3', 'v4']], 'fname': None}),
                ('attrs', OrderedDict())])),
            # second list with two arrays containing each one variable
            ('arr1', OrderedDict([
                ('arr0', {'dims': {'t': slice(None), 'x': slice(None)},
                          'attrs': OrderedDict(), 'store': (None, None),
                          'name': 'v1', 'fname': None}),
                ('arr1', {'dims': {'y': slice(None), 'x': slice(None)},
                          'attrs': OrderedDict(), 'store': (None, None),
                          'name': 'v2', 'fname': None}),
                ('attrs', OrderedDict())])),
            # last array from real dataset
            ('arr2', {'dims': {'z': slice(None), 'y': slice(None),
                               't': 1, 'x': 0},
                      'attrs': ds2.t2m.attrs,
                      'store': ('xarray.backends.netCDF4_',
                                'NetCDF4DataStore'),
                      'name': 't2m', 'fname': fname}),
            ('attrs', OrderedDict())]))
        return l

    def test_from_dict(self):
        """Test the creation from a dictionary"""
        l = self.test_array_info()
        d = l.array_info(engine='netCDF4')
        self.assertEqual(self.list_class.from_dict(d).array_info(),
                         l[-1:].array_info())
        d = l.array_info(ds_description={'ds'})
        self.assertEqual(self.list_class.from_dict(d).array_info(),
                         l.array_info())

    def test_logger(self):
        """Test whether one can access the logger"""
        import logging
        l = self.test_array_info()
        self.assertIsInstance(l.logger, logging.Logger)


class TestInteractiveList(TestArrayList):
    """Test case for the :class:`psyplot.data.InteractiveList` class"""

    list_class = psyd.InteractiveList

    def test_to_dataframe(self):
        variables, coords = self._from_dataset_test_variables
        variables['v1'][:] = np.arange(variables['v1'].size).reshape(
            variables['v1'].shape)
        ds = xr.Dataset(variables, coords)
        l = psyd.InteractiveList.from_dataset(ds, name='v1', t=[0, 1])
        l.extend(psyd.InteractiveList.from_dataset(ds, name='v1', t=2,
                                                   x=slice(1, 3)),
                 new_name=True)
        self.assertEqual(len(l), 3)
        self.assertTrue(all(arr.ndim == 1 for arr in l), msg=l)
        df = l.to_dataframe()
        self.assertEqual(df.shape, (ds.xdim.size, 3))
        self.assertEqual(df.index.values.tolist(), ds.xdim.values.tolist())
        self.assertEqual(df[l[0].psy.arr_name].values.tolist(),
                         ds.v1[0].values.tolist())
        self.assertEqual(df[l[1].psy.arr_name].values.tolist(),
                         ds.v1[1].values.tolist())
        self.assertEqual(df[l[2].psy.arr_name].notnull().sum(), 2)
        self.assertEqual(
            df[l[2].psy.arr_name].values[
                df[l[2].psy.arr_name].notnull().values].tolist(),
            ds.v1[2, 1:3].values.tolist())


class AbsoluteTimeTest(unittest.TestCase, AlmostArrayEqualMixin):
    """TestCase for loading and storing absolute times"""

    @property
    def _test_ds(self):
        import xarray as xr
        import pandas as pd
        time = xr.Coordinate('time', pd.to_datetime(
            ['1979-01-01T12:00:00', '1979-01-01T18:00:00',
             '1979-01-01T18:30:00']),
            encoding={'units': 'day as %Y%m%d.%f'})
        var = xr.Variable(('time', 'x'), np.zeros((len(time), 5)))
        return xr.Dataset({'test': var}, {'time': time})

    def test_to_netcdf(self):
        """Test whether the data is stored correctly"""
        import netCDF4 as nc
        import tempfile
        ds = self._test_ds
        fname = tempfile.NamedTemporaryFile().name
        psyd.to_netcdf(ds, fname)
        with nc.Dataset(fname) as nco:
            self.assertAlmostArrayEqual(
                nco.variables['time'][:], [19790101.5, 19790101.75,
                                           19790101.75 + 30.0 / (24.0 * 60.)],
                rtol=0, atol=1e-5)
            self.assertEqual(nco.variables['time'].units, 'day as %Y%m%d.%f')
        return fname

    def test_open_dataset(self):
        fname = self.test_to_netcdf()
        ref_ds = self._test_ds
        ds = psyd.open_dataset(fname)
        self.assertEqual(
            pd.to_datetime(ds.time.values).tolist(),
            pd.to_datetime(ref_ds.time.values).tolist())


class FilenamesTest(unittest.TestCase):
    """Test whether the filenames can be extracted correctly"""

    @property
    def fname(self):
        return osp.join(osp.dirname(__file__), 'test-t2m-u-v.nc')

    def _test_engine(self, engine):
        from importlib import import_module
        fname = self.fname
        ds = psyd.open_dataset(fname, engine=engine).load()
        self.assertEqual(ds.psy.filename, fname)
        store_mod, store = ds.psy.data_store
        # try to load the dataset
        mod = import_module(store_mod)
        ds2 = psyd.open_dataset(getattr(mod, store)(fname))
        ds.close()
        ds2.close()
        ds.psy.filename = None
        dumped_fname, dumped_store_mod, dumped_store = psyd.get_filename_ds(
            ds, dump=True, engine=engine, paths=True)
        self.assertTrue(dumped_fname)
        self.assertTrue(osp.exists(dumped_fname),
                        msg='Missing %s' % fname)
        self.assertEqual(dumped_store_mod, store_mod)
        self.assertEqual(dumped_store, store)
        ds.close()
        ds.psy.filename = None
        os.remove(dumped_fname)

        dumped_fname, dumped_store_mod, dumped_store = psyd.get_filename_ds(
            ds, dump=True, engine=engine, paths=dumped_fname)
        self.assertTrue(dumped_fname)
        self.assertTrue(osp.exists(dumped_fname),
                        msg='Missing %s' % fname)
        self.assertEqual(dumped_store_mod, store_mod)
        self.assertEqual(dumped_store, store)
        ds.close()
        os.remove(dumped_fname)

    @unittest.skipIf(not with_nio, 'Nio module not installed')
    def test_nio(self):
        self._test_engine('pynio')

    @unittest.skipIf(not with_netcdf4, 'netCDF4 module not installed')
    def test_netcdf4(self):
        self._test_engine('netcdf4')

    @unittest.skipIf(not with_scipy, 'scipy module not installed')
    def test_scipy(self):
        self._test_engine('scipy')


if __name__ == '__main__':
    unittest.main()
