"""Test module of the :mod:`psyplot.data` module"""

# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht

# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: LGPL-3.0-only

import os
import os.path as osp
import tempfile
import unittest

import _base_testing as bt
import numpy as np
import pandas as pd
import six
import xarray as xr

import psyplot.data as psyd

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

try:
    from cdo import Cdo

    Cdo()
except Exception:
    with_cdo = False
else:
    with_cdo = True


xr_version = tuple(map(float, xr.__version__.split(".")[:3]))


class AlmostArrayEqualMixin(object):
    def assertAlmostArrayEqual(
        self, actual, desired, rtol=1e-07, atol=0, msg=None, **kwargs
    ):
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
            np.testing.assert_allclose(
                actual,
                desired,
                rtol=rtol,
                atol=atol,
                err_msg=msg or "",
                **kwargs,
            )
        except AssertionError as e:
            self.fail(e if six.PY3 else e.message)


class DecoderTest(unittest.TestCase, AlmostArrayEqualMixin):
    """Test the :class:`psyplot.data.CFDecoder` class"""

    def test_decode_grid_mapping(self):
        ds = xr.Dataset()
        ds["var"] = (("x", "y"), np.zeros((5, 4)), {"grid_mapping": "crs"})
        ds["crs"] = ((), 1)

        self.assertNotIn("crs", ds.coords)
        ds = psyd.CFDecoder.decode_coords(ds)
        self.assertIn("crs", ds.coords)

    def test_1D_cf_bounds(self):
        """Test whether the CF Conventions for 1D bounaries are correct"""
        final_bounds = np.arange(-180, 181, 30)
        lon = xr.Variable(
            ("lon",), np.arange(-165, 166, 30), {"bounds": "lon_bounds"}
        )
        cf_bounds = xr.Variable(("lon", "bnds"), np.zeros((len(lon), 2)))
        for i in range(len(lon)):
            cf_bounds[i, :] = final_bounds[i : i + 2]
        ds = xr.Dataset(coords={"lon": lon, "lon_bounds": cf_bounds})
        decoder = psyd.CFDecoder(ds)
        self.assertEqual(list(final_bounds), list(decoder.get_plotbounds(lon)))

    def test_1D_bounds_calculation(self):
        """Test whether the 1D cell boundaries are calculated correctly"""
        final_bounds = np.arange(-180, 181, 30)
        lon = xr.Variable(("lon",), np.arange(-165, 166, 30))
        ds = xr.Dataset(coords={"lon": lon})
        decoder = psyd.CFDecoder(ds)
        self.assertEqual(list(final_bounds), list(decoder.get_plotbounds(lon)))

    def _test_dimname(
        self, func_name, name, uname=None, name2d=False, circ_name=None
    ):
        def check_ds(name):
            self.assertEqual(getattr(d, func_name)(ds.t2m), name)
            self.assertEqual(
                getattr(d, func_name)(ds.t2m, coords=ds.t2m.coords), name
            )
            if name2d:
                self.assertEqual(getattr(d, func_name)(ds.t2m_2d), name)
            else:
                self.assertIsNone(getattr(d, func_name)(ds.t2m_2d))
            if six.PY3:
                # Test whether the warning is raised if the decoder finds
                # multiple dimensions
                with self.assertWarnsRegex(RuntimeWarning, "multiple matches"):
                    coords = "time lat lon lev x y latitude longitude".split()
                    ds.t2m.attrs.pop("coordinates", None)
                    for dim in "xytz":
                        getattr(d, dim).update(coords)
                    for coord in set(coords).intersection(ds.coords):
                        ds.coords[coord].attrs.pop("axis", None)
                    getattr(d, func_name)(ds.t2m)

        uname = uname or name
        circ_name = circ_name or name
        ds = psyd.open_dataset(os.path.join(bt.test_dir, "test-t2m-u-v.nc"))
        d = psyd.CFDecoder(ds)
        check_ds(name)
        ds.close()
        ds = psyd.open_dataset(os.path.join(bt.test_dir, "icon_test.nc"))
        d = psyd.CFDecoder(ds)
        check_ds(uname)
        ds.close()
        ds = psyd.open_dataset(
            os.path.join(bt.test_dir, "circumpolar_test.nc")
        )
        d = psyd.CFDecoder(ds)
        check_ds(circ_name)
        ds.close()

    def test_xname_no_dims(self):
        """Test the get_xname method for a variable without dimensions"""
        da = xr.DataArray(1)
        self.assertIsNone(da.psy.get_dim("x"))

    def test_yname_no_dims(self):
        """Test the get_yname method for a variable without dimensions"""
        da = xr.DataArray(1)
        self.assertIsNone(da.psy.get_dim("y"))

    def test_zname_no_dims(self):
        """Test the get_zname method for a variable without dimensions"""
        da = xr.DataArray(1)
        self.assertIsNone(da.psy.get_dim("z"))

    def test_tname_no_dims(self):
        """Test the get_tname method for a variable without dimensions"""
        da = xr.DataArray(1)
        self.assertIsNone(da.psy.get_dim("t"))

    def test_xcoord_no_dims(self):
        """Test the get_x method for a variable without dimensions"""
        da = xr.DataArray(1)
        self.assertIsNone(da.psy.get_coord("x"))

    def test_ycoord_no_dims(self):
        """Test the get_y method for a variable without dimensions"""
        da = xr.DataArray(1)
        self.assertIsNone(da.psy.get_coord("y"))

    def test_zcoord_no_dims(self):
        """Test the get_z method for a variable without dimensions"""
        da = xr.DataArray(1)
        self.assertIsNone(da.psy.get_coord("z"))

    def test_tcoord_no_dims(self):
        """Test the get_t method for a variable without dimensions"""
        da = xr.DataArray(1)
        self.assertIsNone(da.psy.get_coord("t"))

    def _test_coord(
        self, func_name, name, uname=None, name2d=False, circ_name=None
    ):
        def check_ds(name):
            self.assertEqual(getattr(d, func_name)(ds.t2m).name, name)
            if name2d:
                self.assertEqual(getattr(d, func_name)(ds.t2m_2d).name, name)
            else:
                self.assertIsNone(getattr(d, func_name)(ds.t2m_2d))
            if six.PY3:
                # Test whether the warning is raised if the decoder finds
                # multiple dimensions
                with self.assertWarnsRegex(RuntimeWarning, "multiple matches"):
                    coords = "time lat lon lev x y latitude longitude".split()
                    ds.t2m.attrs.pop("coordinates", None)
                    for dim in "xytz":
                        getattr(d, dim).update(coords)
                    for coord in set(coords).intersection(ds.coords):
                        ds.coords[coord].attrs.pop("axis", None)
                    getattr(d, func_name)(ds.t2m)

        uname = uname or name
        circ_name = circ_name or name
        ds = psyd.open_dataset(os.path.join(bt.test_dir, "test-t2m-u-v.nc"))
        d = psyd.CFDecoder(ds)
        check_ds(name)
        ds.close()
        ds = psyd.open_dataset(os.path.join(bt.test_dir, "icon_test.nc"))
        d = psyd.CFDecoder(ds)
        check_ds(uname)
        ds.close()
        ds = psyd.open_dataset(
            os.path.join(bt.test_dir, "circumpolar_test.nc")
        )
        d = psyd.CFDecoder(ds)
        check_ds(circ_name)
        ds.close()

    def test_tname(self):
        """Test CFDecoder.get_tname method"""
        self._test_dimname("get_tname", "time")

    def test_zname(self):
        """Test CFDecoder.get_zname method"""
        self._test_dimname("get_zname", "lev")

    def test_xname(self):
        """Test CFDecoder.get_xname method"""
        self._test_dimname("get_xname", "lon", "ncells", True, circ_name="x")

    def test_yname(self):
        """Test CFDecoder.get_yname method"""
        self._test_dimname("get_yname", "lat", "ncells", True, circ_name="y")

    def test_t(self):
        """Test CFDecoder.get_t method"""
        self._test_coord("get_t", "time")

    def test_z(self):
        """Test CFDecoder.get_z method"""
        self._test_coord("get_z", "lev")

    def test_x(self):
        """Test CFDecorder.get_x method"""
        self._test_coord("get_x", "lon", "clon", True, circ_name="longitude")

    def test_y(self):
        """Test CFDecoder.get_y method"""
        self._test_coord("get_y", "lat", "clat", True, circ_name="latitude")

    def test_standardization(self):
        """Test the :meth:`psyplot.data.CFDecoder.standardize_dims` method"""
        ds = psyd.open_dataset(os.path.join(bt.test_dir, "test-t2m-u-v.nc"))
        decoder = psyd.CFDecoder(ds)
        dims = {"time": 1, "lat": 2, "lon": 3, "lev": 4}
        replaced = decoder.standardize_dims(ds.t2m, dims)
        for dim, rep in [
            ("time", "t"),
            ("lat", "y"),
            ("lon", "x"),
            ("lev", "z"),
        ]:
            self.assertIn(rep, replaced)
            self.assertEqual(
                replaced[rep],
                dims[dim],
                msg="Wrong value for %s (%s-) dimension" % (dim, rep),
            )

    def test_idims(self):
        """Test the extraction of the slicers of the dimensions"""
        ds = psyd.open_dataset(bt.get_file("test-t2m-u-v.nc"))
        arr = ds.t2m[1:, 1]
        arr.psy.init_accessor(base=ds)
        dims = arr.psy.idims
        for dim in ["time", "lev", "lat", "lon"]:
            self.assertEqual(
                psyd.safe_list(ds[dim][dims[dim]]),
                psyd.safe_list(arr.coords[dim]),
                msg="Slice %s for dimension %s is wrong!" % (dims[dim], dim),
            )
        # test with unknown dimensions
        if xr_version[:2] >= (0, 9):
            try:
                ds = ds.drop_vars("time")
            except AttributeError:  # xarray <=0.13
                ds = ds.drop("time")
            arr = ds.t2m[1:, 1]
            arr.psy.init_accessor(base=ds)
            if not six.PY2:
                with self.assertWarnsRegex(RuntimeWarning, "time"):
                    dims = arr.psy.idims
            arrays = psyd.ArrayList.from_dataset(
                ds, name="t2m", time=slice(1, None), lev=85000.0, method="sel"
            )
            arr = arrays[0]
            dims = arr.psy.idims
            for dim in ["time", "lev", "lat", "lon"]:
                if dim == "time":
                    self.assertEqual(dims[dim], slice(1, 5, 1))
                else:
                    self.assertEqual(
                        psyd.safe_list(ds[dim][dims[dim]]),
                        psyd.safe_list(arr.coords[dim]),
                        msg="Slice %s for dimension %s is wrong!"
                        % (dims[dim], dim),
                    )

    def test_unstructured_bounds(self):
        """Test the extraction of unstructured bounds"""
        ds = psyd.open_dataset(os.path.join(bt.test_dir, "icon_test.nc"))
        decoder = psyd.CFDecoder(ds)
        var = ds.t2m[0, 0]
        var.attrs.pop("grid_type", None)
        self.assertTrue(decoder.is_unstructured(var))
        # x bounds
        xbounds = decoder.get_cell_node_coord(var, axis="x")
        self.assertIsNotNone(xbounds)
        self.assertEqual(xbounds.shape, ds.clon_bnds.shape)
        # y bounds
        ybounds = decoder.get_cell_node_coord(var, axis="y")
        self.assertIsNotNone(ybounds)
        self.assertEqual(ybounds.shape, ds.clon_bnds.shape)

        # Test for correct falsification
        ds = psyd.open_dataset(os.path.join(bt.test_dir, "test-t2m-u-v.nc"))
        decoder = psyd.CFDecoder(ds)
        var = ds.t2m[0, 0]
        self.assertFalse(decoder.is_unstructured(var))
        xbounds = decoder.get_cell_node_coord(var, axis="x")
        self.assertEqual(xbounds.shape, (np.prod(var.shape), 4))

    def test_is_unstructured_2D_bounds(self):
        """Test that 3D bounds are not interpreted as unstructured"""
        with psyd.open_dataset(
            os.path.join(bt.test_dir, "rotated-pole-test.nc")
        ) as ds:
            decoder = psyd.CFDecoder(ds)
            self.assertFalse(decoder.is_unstructured(ds.psy["HSURF"]))

    def test_is_circumpolar(self):
        """Test whether the is_circumpolar method works"""
        ds = psyd.open_dataset(
            os.path.join(bt.test_dir, "circumpolar_test.nc")
        )
        decoder = psyd.CFDecoder(ds)
        self.assertTrue(decoder.is_circumpolar(ds.t2m))

        # test for correct falsification
        ds = psyd.open_dataset(os.path.join(bt.test_dir, "icon_test.nc"))
        decoder = psyd.CFDecoder(ds)
        self.assertFalse(decoder.is_circumpolar(ds.t2m))

    def test_get_variable_by_axis(self):
        """Test the :meth:`CFDecoder.get_variable_by_axis` method"""
        ds = psyd.open_dataset(
            os.path.join(bt.test_dir, "circumpolar_test.nc")
        )
        decoder = psyd.CFDecoder(ds)
        arr = ds.t2m
        arr.attrs.pop("coordinates", None)
        arr.encoding.pop("coordinates", None)
        for c in ds.coords.values():
            c.attrs.pop("axis", None)
        for dim in ["x", "y", "z", "t"]:
            self.assertIsNone(
                decoder.get_variable_by_axis(arr, dim),
                msg="Accidently found coordinate %s" % dim,
            )

        # test coordinates attribute
        arr.attrs["coordinates"] = "latitude longitude"
        self.assertEqual(
            decoder.get_variable_by_axis(arr, "x").name, "longitude"
        )
        self.assertEqual(
            decoder.get_variable_by_axis(arr, "y").name, "latitude"
        )
        self.assertIsNone(decoder.get_variable_by_axis(arr, "z"))

        # test coordinates attribute but without specifying axis or matching
        # latitude or longitude
        axes = {"lev": "z", "time": "t", "x": "x", "y": "y"}
        arr.attrs["coordinates"] = "time lev y x"
        for name, axis in axes.items():
            self.assertEqual(
                decoder.get_variable_by_axis(arr, axis).name, name
            )

        # test with specified axis attribute
        arr.attrs["coordinates"] = "time lev longitude latitude"
        axes = {"lev": "Z", "time": "T", "latitude": "X", "longitude": "Y"}
        for name, axis in axes.items():
            ds.coords[name].attrs["axis"] = axis
        for name, axis in axes.items():
            self.assertEqual(
                decoder.get_variable_by_axis(arr, axis.lower()).name, name
            )

        # close the dataset
        ds.close()

    def test_get_variable_by_axis_02(self):
        """Test the :meth:`CFDecoder.get_variable_by_axis` method with missing
        coordinates, see https://codebase.helmholtz.cloud/psyplot/psyplot/pull/19
        """
        fname = os.path.join(bt.test_dir, "icon_test.nc")
        with psyd.open_dataset(fname) as ds:
            ds["ncells"] = ("ncells", np.arange(ds.dims["ncells"]))
            decoder = psyd.CFDecoder(ds)
            arr = ds.psy["t2m"].psy.isel(ncells=slice(3, 10))
            del arr["clon"]
            xcoord = decoder.get_variable_by_axis(arr, "x", arr.coords)
            self.assertEqual(xcoord.name, "clon")
            self.assertEqual(list(xcoord.ncells), list(arr.ncells))

    def test_plot_bounds_1d(self):
        """Test to get 2d-interval breaks"""
        x = xr.Variable(("x",), np.arange(1, 5))
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
        bounds = d.get_plotbounds(xr.Variable(("y", "x"), x2d))
        self.assertAlmostArrayEqual(bounds, x2d_bnds)

        # test y bounds
        bounds = d.get_plotbounds(xr.Variable(("y", "x"), y2d))
        self.assertAlmostArrayEqual(bounds, y2d_bnds)


class UGridDecoderTest(unittest.TestCase, AlmostArrayEqualMixin):
    """Test the :class:`psyplot.data.UGridDecoder` class"""

    def test_get_decoder(self):
        """Test to get the right decoder"""
        ds = psyd.open_dataset(bt.get_file("simple_triangular_grid_si0.nc"))
        d = psyd.CFDecoder.get_decoder(ds, ds.Mesh2_fcvar)
        self.assertIsInstance(d, psyd.UGridDecoder)
        return ds, d

    def test_x(self):
        """Test the get_x method"""
        ds, d = self.test_get_decoder()
        x = d.get_x(ds.Mesh2_fcvar)
        self.assertIn("standard_name", x.attrs)
        self.assertEqual(x.attrs["standard_name"], "longitude")
        self.assertAlmostArrayEqual(x.values, [0.3, 0.56666667])

    def test_y(self):
        """Test the get_y method"""
        ds, d = self.test_get_decoder()
        y = d.get_y(ds.Mesh2_fcvar)
        self.assertIn("standard_name", y.attrs)
        self.assertEqual(y.attrs["standard_name"], "latitude")
        self.assertAlmostArrayEqual(y.values, [0.4, 0.76666668])


class TestInteractiveArray(unittest.TestCase, AlmostArrayEqualMixin):
    """Test the :class:`psyplot.data.InteractiveArray` class"""

    def tearDown(self):
        psyd.rcParams.update_from_defaultParams(plotters=False)

    def test_auto_update(self):
        """Test the :attr:`psyplot.plotter.Plotter.no_auto_update` attribute"""
        ds = psyd.open_dataset(bt.get_file("test-t2m-u-v.nc"))
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
        ds = psyd.open_dataset(bt.get_file("test-t2m-u-v.nc"))
        arr = ds.psy.t2m.psy[0, 0, 0]
        arr.attrs["test"] = 4
        self.assertNotIn("test", ds.t2m.attrs)
        self.assertIs(arr.psy.base, ds)
        self.assertEqual(
            dict(arr.psy.idims),
            {"time": 0, "lev": 0, "lat": 0, "lon": slice(None)},
        )
        # update to next time step
        arr.psy.update(time=1)
        self.assertEqual(arr.time, ds.time[1])
        self.assertEqual(
            arr.values.tolist(), ds.t2m[1, 0, 0, :].values.tolist()
        )
        self.assertEqual(
            dict(arr.psy.idims),
            {"time": 1, "lev": 0, "lat": 0, "lon": slice(None)},
        )
        self.assertNotIn("test", ds.t2m.attrs)
        self.assertIn("test", arr.attrs)
        self.assertEqual(arr.test, 4)

    @unittest.skipIf(xr_version[:2] < (0, 10), "Not implemented for xr<0.10")
    def test_shiftlon(self):
        ds = psyd.open_dataset(bt.get_file("test-t2m-u-v.nc"))
        da = ds.t2m
        nlon = da.lon.size

        # shift to the mean (this should not change anything)
        shifted = da.psy.shiftlon(ds.lon.values.mean())
        self.assertAlmostArrayEqual(shifted.lon, da.lon)
        self.assertAlmostArrayEqual(shifted, da)

        # shift to left
        shifted = da.psy.shiftlon(da.lon.min())
        self.assertEqual(shifted.lon[nlon // 2 - 1], da.lon[0])
        self.assertEqual(shifted.lon[-1], da.lon[nlon // 2])
        self.assertAlmostArrayEqual(shifted[..., nlon // 2 - 1], da[..., 0])
        self.assertAlmostArrayEqual(shifted[..., -1], da[..., nlon // 2])

        # shift 25% to left
        shifted = da.psy.shiftlon(da.lon[nlon // 4])
        self.assertEqual(shifted.lon[0], da.lon[-nlon // 4 + 1] - 360)
        self.assertAlmostArrayEqual(
            shifted[..., nlon // 2 - 1], da[..., nlon // 4]
        )
        self.assertAlmostArrayEqual(shifted[..., 0], da[..., -nlon // 4 + 1])

    def test_update_02_sel(self):
        """test the update of a single array through the sel method"""
        ds = psyd.open_dataset(bt.get_file("test-t2m-u-v.nc"))
        arr = ds.psy.t2m.psy[0, 0, 0]
        arr.attrs["test"] = 4
        self.assertNotIn("test", ds.t2m.attrs)
        self.assertIs(arr.psy.base, ds)
        self.assertEqual(
            dict(arr.psy.idims),
            {"time": 0, "lev": 0, "lat": 0, "lon": slice(None)},
        )
        # update to next time step
        arr.psy.update(time="1979-02-28T18:00", method="nearest")
        self.assertEqual(arr.time, ds.time[1])
        self.assertEqual(
            arr.values.tolist(), ds.t2m[1, 0, 0, :].values.tolist()
        )
        self.assertEqual(
            dict(arr.psy.idims),
            {"time": 1, "lev": 0, "lat": 0, "lon": slice(None)},
        )
        self.assertNotIn("test", ds.t2m.attrs)
        self.assertIn("test", arr.attrs)
        self.assertEqual(arr.test, 4)

    def test_update_03_isel_concat(self):
        """test the update of a concatenated array through the isel method"""
        ds = psyd.open_dataset(bt.get_file("test-t2m-u-v.nc"))[["t2m", "u"]]
        arr = ds.psy.to_array().psy.isel(time=0, lev=0, lat=0)
        arr.attrs["test"] = 4
        self.assertNotIn("test", ds.t2m.attrs)
        arr.name = "something"
        self.assertIs(arr.psy.base, ds)
        self.assertEqual(
            dict(arr.psy.idims),
            {"time": 0, "lev": 0, "lat": 0, "lon": slice(None)},
        )
        self.assertEqual(arr.coords["variable"].values.tolist(), ["t2m", "u"])
        # update to next time step
        arr.psy.update(time=1)
        self.assertEqual(arr.time, ds.time[1])
        self.assertEqual(arr.coords["variable"].values.tolist(), ["t2m", "u"])
        self.assertEqual(
            arr.values.tolist(),
            ds[["t2m", "u"]].to_array()[:, 1, 0, 0, :].values.tolist(),
        )
        self.assertEqual(
            dict(arr.psy.idims),
            {"time": 1, "lev": 0, "lat": 0, "lon": slice(None)},
        )
        self.assertNotIn("test", ds.t2m.attrs)
        self.assertIn("test", arr.attrs)
        self.assertEqual(arr.test, 4)
        self.assertEqual(arr.name, "something")

    def test_update_04_sel_concat(self):
        """test the update of a concatenated array through the isel method"""
        ds = psyd.open_dataset(bt.get_file("test-t2m-u-v.nc"))[["t2m", "u"]]
        arr = ds.psy.to_array().psy.isel(time=0, lev=0, lat=0)
        arr.attrs["test"] = 4
        self.assertNotIn("test", ds.t2m.attrs)
        self.assertIs(arr.psy.base, ds)
        self.assertEqual(
            dict(arr.psy.idims),
            {"time": 0, "lev": 0, "lat": 0, "lon": slice(None)},
        )
        self.assertEqual(arr.coords["variable"].values.tolist(), ["t2m", "u"])
        # update to next time step
        arr.psy.update(time="1979-02-28T18:00", method="nearest")
        self.assertEqual(arr.time, ds.time[1])
        self.assertEqual(arr.coords["variable"].values.tolist(), ["t2m", "u"])
        self.assertEqual(
            arr.values.tolist(),
            ds[["t2m", "u"]].to_array()[:, 1, 0, 0, :].values.tolist(),
        )
        self.assertEqual(
            dict(arr.psy.idims),
            {"time": 1, "lev": 0, "lat": 0, "lon": slice(None)},
        )
        self.assertNotIn("test", ds.t2m.attrs)
        self.assertIn("test", arr.attrs)
        self.assertEqual(arr.test, 4)

    def test_update_05_1variable(self):
        """Test to change the variable"""
        ds = psyd.open_dataset(bt.get_file("test-t2m-u-v.nc"))
        arr = ds.psy.t2m.psy[0, 0, 0]
        arr.attrs["test"] = 4
        self.assertNotIn("test", ds.t2m.attrs)
        self.assertIs(arr.psy.base, ds)
        self.assertEqual(
            dict(arr.psy.idims),
            {"time": 0, "lev": 0, "lat": 0, "lon": slice(None)},
        )
        # update to next time step
        arr.psy.update(name="u", time=1)
        self.assertEqual(arr.time, ds.time[1])
        self.assertEqual(arr.name, "u")
        self.assertEqual(arr.values.tolist(), ds.u[1, 0, 0, :].values.tolist())
        self.assertEqual(
            dict(arr.psy.idims),
            {"time": 1, "lev": 0, "lat": 0, "lon": slice(None)},
        )
        self.assertNotIn("test", ds.t2m.attrs)
        self.assertIn("test", arr.attrs)
        self.assertEqual(arr.test, 4)

    def test_update_06_2variables(self):
        """test the change of the variable of a concatenated array"""
        ds = psyd.open_dataset(bt.get_file("test-t2m-u-v.nc"))
        arr = ds[["t2m", "u"]].to_array().isel(time=0, lev=0, lat=0)
        arr.attrs["test"] = 4
        self.assertNotIn("test", ds.t2m.attrs)
        arr.name = "something"
        arr.psy.base = ds
        self.assertEqual(
            dict(arr.psy.idims),
            {"time": 0, "lev": 0, "lat": 0, "lon": slice(None)},
        )
        self.assertEqual(arr.coords["variable"].values.tolist(), ["t2m", "u"])
        # update to next time step
        arr.psy.update(time=1, name=["u", "v"])
        self.assertEqual(arr.time, ds.time[1])
        self.assertEqual(arr.coords["variable"].values.tolist(), ["u", "v"])
        self.assertEqual(
            arr.values.tolist(),
            ds[["u", "v"]].to_array()[:, 1, 0, 0, :].values.tolist(),
        )
        self.assertEqual(
            dict(arr.psy.idims),
            {"time": 1, "lev": 0, "lat": 0, "lon": slice(None)},
        )
        self.assertNotIn("test", ds.t2m.attrs)
        self.assertIn("test", arr.attrs)
        self.assertEqual(arr.test, 4)
        self.assertEqual(arr.name, "something")

    def test_update_07_variable_with_new_dims(self):
        ds = xr.Dataset()
        ds["test1"] = (tuple("ab"), np.zeros((5, 4)))
        ds["test2"] = (tuple("abc"), np.zeros((5, 4, 3)))
        ds["a"] = ("a", np.arange(5))
        ds["b"] = ("b", np.arange(4))
        ds["c"] = ("c", np.arange(3))

        da = ds.psy["test1"].psy.isel(a=slice(1, 3))
        self.assertEqual(da.name, "test1")
        self.assertEqual(da.shape, (2, 4))
        self.assertEqual(da.psy.idims, {"a": slice(1, 3, 1), "b": slice(None)})

        # update to test2
        da.psy.update(name="test2")
        self.assertEqual(da.name, "test2")
        self.assertEqual(da.shape, (2, 4, 3))
        self.assertEqual(
            da.psy.idims,
            {"a": slice(1, 3, 1), "b": slice(None), "c": slice(None)},
        )

        # update back to test1
        da.psy.update(name="test1")
        self.assertEqual(da.name, "test1")
        self.assertEqual(da.shape, (2, 4))
        self.assertEqual(da.psy.idims, {"a": slice(1, 3, 1), "b": slice(None)})

        # update to test2 but this time with specifying a dimension for c
        # does not yet work with c=1
        da.psy.update(name="test2", dims=dict(c=1))
        self.assertEqual(da.name, "test2")
        self.assertEqual(da.shape, (2, 4))
        self.assertEqual(
            da.psy.idims, {"a": slice(1, 3, 1), "b": slice(None), "c": 1}
        )
        self.assertEqual(da["c"], 1)

    def test_update_08_2variables_with_new_dims(self):
        ds = xr.Dataset()
        ds["test1"] = (tuple("ab"), np.zeros((5, 4)))
        ds["test11"] = (tuple("ab"), np.zeros((5, 4)))
        ds["test2"] = (tuple("abc"), np.zeros((5, 4, 3)))
        ds["test22"] = (tuple("abc"), np.zeros((5, 4, 3)))
        ds["a"] = ("a", np.arange(5))
        ds["b"] = ("b", np.arange(4))
        ds["c"] = ("c", np.arange(3))

        da = ds.psy.create_list(
            name=[["test1", "test11"]], prefer_list=False, a=slice(1, 3, 1)
        )[0]
        self.assertEqual(da.shape, (2, 2, 4))
        self.assertEqual(list(da["variable"]), ["test1", "test11"])
        self.assertEqual(da.psy.idims, {"a": slice(1, 3, 1), "b": slice(None)})

        # update to test2
        da.psy.update(name=["test2", "test22"])
        self.assertEqual(da.shape, (2, 2, 4, 3))
        self.assertEqual(list(da["variable"]), ["test2", "test22"])
        self.assertEqual(
            da.psy.idims,
            {"a": slice(1, 3, 1), "b": slice(None), "c": slice(None)},
        )

        # update back to test1
        da.psy.update(name=["test1", "test11"])
        self.assertEqual(da.shape, (2, 2, 4))
        self.assertEqual(list(da["variable"]), ["test1", "test11"])
        self.assertEqual(da.psy.idims, {"a": slice(1, 3, 1), "b": slice(None)})

        # update to test2 but this time with specifying a dimension for c
        # does not yet work with c=1
        da.psy.update(name=["test2", "test22"], dims=dict(c=1))
        self.assertEqual(list(da["variable"]), ["test2", "test22"])
        self.assertEqual(da.shape, (2, 2, 4))
        self.assertEqual(
            da.psy.idims, {"a": slice(1, 3, 1), "b": slice(None), "c": 1}
        )
        self.assertEqual(da["c"], 1)

    @unittest.skipIf(not with_cdo, "CDOs are not installed")
    def test_gridweights_01_lola(self):
        fname = bt.get_file("test-t2m-u-v.nc")
        ds = psyd.open_dataset(fname)
        weights = ds.psy.t2m.psy.gridweights()
        ds.close()
        ref = Cdo().gridweights(input=fname, returnArray="cell_weights")
        self.assertAlmostArrayEqual(weights, ref, atol=1e-7)

    @unittest.skipIf(not with_cdo, "CDOs are not installed")
    def test_gridweights_02_icon(self):
        fname = bt.get_file("icon_test.nc")
        ds = psyd.open_dataset(fname)
        weights = ds.psy.t2m.psy.gridweights()
        ds.close()
        ref = Cdo().gridweights(input=fname, returnArray="cell_weights")
        self.assertAlmostArrayEqual(weights, ref)

    @unittest.skipIf(not with_cdo, "CDOs are not installed")
    @unittest.skipIf(xr_version[:2] < (0, 9), "xarray version too low")
    def test_fldmean_01_lola(self):
        from psyplot.project import Cdo

        fname = bt.get_file("test-t2m-u-v.nc")
        ds = psyd.open_dataset(fname)
        psyd.rcParams["gridweights.use_cdo"] = True
        means = ds.psy.t2m.psy.fldmean().values
        ref = Cdo().fldmean(input=fname, name="t2m")[0]
        self.assertAlmostArrayEqual(means, ref)
        # try it with the self defined gridweights
        psyd.rcParams["gridweights.use_cdo"] = False
        means = ds.psy.t2m.psy.fldmean().values
        self.assertAlmostArrayEqual(means, ref, rtol=1e-5)
        ds.close()

    @unittest.skipIf(not with_cdo, "CDOs are not installed")
    @unittest.skipIf(xr_version[:2] < (0, 9), "xarray version too low")
    def test_fldmean_02_icon(self):
        from psyplot.project import Cdo

        fname = bt.get_file("icon_test.nc")
        ds = psyd.open_dataset(fname)
        psyd.rcParams["gridweights.use_cdo"] = True
        means = ds.psy.t2m.psy.fldmean().values
        ref = Cdo().fldmean(input=fname, name="t2m")[0]
        self.assertAlmostArrayEqual(means, ref)
        ds.close()

    @unittest.skipIf(not with_cdo, "CDOs are not installed")
    @unittest.skipIf(xr_version[:2] < (0, 9), "xarray version too low")
    def test_fldstd_01_lola(self):
        from psyplot.project import Cdo

        fname = bt.get_file("test-t2m-u-v.nc")
        ds = psyd.open_dataset(fname)
        psyd.rcParams["gridweights.use_cdo"] = True
        std = ds.psy.t2m.psy.fldstd(keepdims=True).values
        ref = Cdo().fldstd(input=fname, returnArray="t2m")
        self.assertAlmostArrayEqual(std, ref)
        # try it with the self defined gridweights
        psyd.rcParams["gridweights.use_cdo"] = False
        std = ds.psy.t2m.psy.fldstd(keepdims=True).values
        self.assertAlmostArrayEqual(std, ref, rtol=1e-3)
        ds.close()

    @unittest.skipIf(not with_cdo, "CDOs are not installed")
    @unittest.skipIf(xr_version[:2] < (0, 9), "xarray version too low")
    def test_fldstd_02_icon(self):
        from psyplot.project import Cdo

        fname = bt.get_file("icon_test.nc")
        ds = psyd.open_dataset(fname)
        psyd.rcParams["gridweights.use_cdo"] = True
        std = ds.psy.t2m.psy.fldstd().values
        ds.close()
        ref = Cdo().fldstd(input=fname, name="t2m")[0]
        self.assertAlmostArrayEqual(std, ref)

    @unittest.skipIf(not with_cdo, "CDOs are not installed")
    @unittest.skipIf(xr_version[:2] < (0, 9), "xarray version too low")
    def test_fldpctl_01_lola(self):
        fname = bt.get_file("test-t2m-u-v.nc")
        ds = psyd.open_dataset(fname)
        pctl = ds.psy.t2m.psy.fldpctl(5).values
        self.assertEqual(pctl.shape, ds.t2m.shape[:-2])

        pctl = ds.psy.t2m.psy.fldpctl([5, 95]).values
        self.assertEqual(pctl.shape, (2,) + ds.t2m.shape[:-2])
        self.assertTrue(
            (pctl[1] >= pctl[0]).all(),
            msg=(
                "95th percentile should always be greater or "
                "equal than the 5th percentile! %s %s"
            )
            % (pctl[0], pctl[1]),
        )
        ds.close()

    @unittest.skipIf(not with_cdo, "CDOs are not installed")
    @unittest.skipIf(xr_version[:2] < (0, 9), "xarray version too low")
    def test_fldpctl_02_icon(self):
        fname = bt.get_file("icon_test.nc")
        ds = psyd.open_dataset(fname)
        pctl = ds.psy.t2m.psy.fldpctl(5).values
        self.assertEqual(pctl.shape, ds.t2m.shape[:-1])

        pctl = ds.psy.t2m.psy.fldpctl([5, 95]).values
        self.assertEqual(pctl.shape, (2,) + ds.t2m.shape[:-1])
        self.assertTrue(
            (pctl[1] >= pctl[0]).all(),
            msg=(
                "95th percentile should always be greater or "
                "equal than the 5th percentile! %s %s"
            )
            % (pctl[0], pctl[1]),
        )
        ds.close()


class TestArrayList(unittest.TestCase):
    """Test the :class:`psyplot.data.ArrayList` class"""

    _created_files = set()

    def setUp(self):
        self._created_files = set()

    def tearDown(self):
        for f in self._created_files:
            try:
                os.remove(f)
            except Exception:
                pass
        self._created_files.clear()

    list_class = psyd.ArrayList

    def test_setup_coords(self):
        """Set the :func:`psyplot.data.setup_coords` function"""
        coords = {"first": [1, 2]}
        self.assertEqual(
            psyd.setup_coords(second=3, **coords),
            {
                "arr0": {"first": 1, "second": 3},
                "arr1": {"first": 2, "second": 3},
            },
        )
        self.assertEqual(
            psyd.setup_coords(dims=coords, second=3),
            {
                "arr0": {"first": 1, "second": 3},
                "arr1": {"first": 2, "second": 3},
            },
        )
        coords["third"] = [1, 2, 3]
        # test sorting
        ret = psyd.setup_coords(
            arr_names="test{}", second=3, sort=["third", "first"], **coords
        )
        self.assertEqual(
            ret,
            {
                "test0": {"third": 1, "first": 1, "second": 3},
                "test1": {"third": 1, "first": 2, "second": 3},
                "test2": {"third": 2, "first": 1, "second": 3},
                "test3": {"third": 2, "first": 2, "second": 3},
                "test4": {"third": 3, "first": 1, "second": 3},
                "test5": {"third": 3, "first": 2, "second": 3},
            },
        )

    @property
    def _filter_test_ds(self):
        return xr.Dataset(
            {
                "v0": xr.Variable(
                    ("ydim", "xdim"),
                    np.zeros((4, 4)),
                    attrs={"test": 1, "test2": 1},
                ),
                "v1": xr.Variable(
                    ("xdim",), np.zeros(4), attrs={"test": 2, "test2": 2}
                ),
                "v2": xr.Variable(
                    ("xdim",), np.zeros(4), attrs={"test": 3, "test2": 3}
                ),
            },
            {
                "ydim": xr.Variable(("ydim",), np.arange(1, 5)),
                "xdim": xr.Variable(("xdim",), np.arange(4)),
            },
        )

    def test_filter_1_name(self):
        """Test the filtering of the ArrayList"""
        ds = self._filter_test_ds
        arrays = self.list_class.from_dataset(ds, ydim=0)
        arrays.extend(
            self.list_class.from_dataset(ds, ydim=1, name="v0"), new_name=True
        )
        # filter by name
        self.assertEqual([arr.name for arr in arrays(name="v1")], ["v1"])
        self.assertEqual(
            [arr.name for arr in arrays(name=["v1", "v2"])], ["v1", "v2"]
        )
        self.assertEqual(
            [
                arr.psy.arr_name
                for arr in arrays(arr_name=lambda name: name == "arr1")
            ],
            ["arr1"],
        )

    def test_filter_2_arr_name(self):
        """Test the filtering of the ArrayList"""
        ds = self._filter_test_ds
        arrays = self.list_class.from_dataset(ds, ydim=0)
        arrays.extend(
            self.list_class.from_dataset(ds, ydim=1, name="v0"), new_name=True
        )
        # fillter by array name
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(arr_name="arr1")], ["arr1"]
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(arr_name=["arr1", "arr2"])],
            ["arr1", "arr2"],
        )
        self.assertEqual(
            [
                arr.psy.arr_name
                for arr in arrays(name=lambda name: name == "v1")
            ],
            ["arr1"],
        )

    def test_filter_3_attribute(self):
        """Test the filtering of the ArrayList"""
        ds = self._filter_test_ds
        arrays = self.list_class.from_dataset(ds, ydim=0)
        arrays.extend(
            self.list_class.from_dataset(ds, ydim=1, name="v0"), new_name=True
        )
        # filter by attribute
        self.assertEqual([arr.name for arr in arrays(test=2)], ["v1"])
        self.assertEqual(
            [arr.name for arr in arrays(test=[2, 3])], ["v1", "v2"]
        )
        self.assertEqual(
            [arr.name for arr in arrays(test=[1, 2], test2=2)], ["v1"]
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(test=lambda val: val == 2)],
            ["arr1"],
        )

    def test_filter_4_coord(self):
        """Test the filtering of the ArrayList"""
        ds = self._filter_test_ds
        arrays = self.list_class.from_dataset(ds, ydim=0)
        arrays.extend(
            self.list_class.from_dataset(ds, ydim=1, name="v0"), new_name=True
        )
        # filter by coordinate
        self.assertEqual([arr.psy.arr_name for arr in arrays(y=0)], ["arr0"])
        self.assertEqual([arr.psy.arr_name for arr in arrays(y=1)], ["arr3"])
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(y=1, method="sel")], ["arr0"]
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(y=lambda val: val == 0)],
            ["arr0"],
        )

    def test_filter_5_mixed(self):
        """Test the filtering of the ArrayList"""
        ds = self._filter_test_ds
        arrays = self.list_class.from_dataset(ds, ydim=0)
        arrays.extend(
            self.list_class.from_dataset(ds, ydim=1, name="v0"), new_name=True
        )
        # mix criteria
        self.assertEqual(
            [
                arr.psy.arr_name
                for arr in arrays(arr_name=["arr0", "arr1"], test=1)
            ],
            ["arr0"],
        )

    def test_filter_6_ax(self):
        """Test the filtering of the ArrayList"""
        import matplotlib.pyplot as plt

        from psyplot.plotter import Plotter

        ds = self._filter_test_ds
        arrays = self.list_class.from_dataset(ds, ydim=[0, 1], name="v0")
        axes = plt.subplots(1, 2)[1]
        for i, arr in enumerate(arrays):
            Plotter(arr, ax=axes[i])
        # mix criteria
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(ax=axes[0])],
            [arrays[0].psy.arr_name],
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(ax=axes[1])],
            [arrays[1].psy.arr_name],
        )

    def test_filter_7_fig(self):
        """Test the filtering of the ArrayList"""
        import matplotlib.pyplot as plt

        from psyplot.plotter import Plotter

        ds = self._filter_test_ds
        arrays = self.list_class.from_dataset(ds, ydim=[0, 1], name="v0")
        figs = [0, 0]
        axes = [0, 0]
        figs[0], axes[0] = plt.subplots()
        figs[1], axes[1] = plt.subplots()
        for i, arr in enumerate(arrays):
            Plotter(arr, ax=axes[i])
        # mix criteria
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(fig=figs[0])],
            [arrays[0].psy.arr_name],
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(fig=figs[1])],
            [arrays[1].psy.arr_name],
        )

    def test_filter_8_fmts(self):
        from test_plotter import SimpleFmt, TestPlotter

        ds = self._filter_test_ds
        arrays = self.list_class.from_dataset(ds, ydim=[0, 1], name="v0")

        class TestPlotter2(TestPlotter):
            fmt_test = SimpleFmt("fmt_test")

        TestPlotter(arrays[0])
        TestPlotter2(arrays[1])

        self.assertEqual(arrays(fmts=["fmt1"]).arr_names, arrays.arr_names)
        self.assertEqual(
            arrays(fmts=["fmt_test"]).arr_names, [arrays[1].psy.arr_name]
        )

    def test_list_filter_1_name(self):
        """Test the filtering of InteractiveList by the variable name"""
        ds = self._filter_test_ds
        arrays = self.list_class.from_dataset(
            ds, name="v1", ydim=[0, 1], prefer_list=True
        )
        arrays.extend(
            self.list_class.from_dataset(
                ds, name="v2", xdim=[0, 1], prefer_list=True
            ),
            new_name=True,
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(name="v1")], ["arr0"]
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(name="v2")], ["arr1"]
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(name=lambda n: n == "v1")],
            ["arr0"],
        )

    def test_list_filter_2_arr_name(self):
        """Test the filtering of InteractiveList by the array name"""
        ds = self._filter_test_ds
        arrays = self.list_class.from_dataset(
            ds, name="v1", ydim=[0, 1], prefer_list=True
        )
        arrays.extend(
            self.list_class.from_dataset(
                ds, name="v2", xdim=[0, 1], prefer_list=True
            ),
            new_name=True,
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(arr_name="arr0")], ["arr0"]
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(arr_name="arr1")], ["arr1"]
        )
        self.assertEqual(
            [
                arr.psy.arr_name
                for arr in arrays(arr_name=lambda an: an == "arr0")
            ],
            ["arr0"],
        )

    def test_list_filter_3_attribute(self):
        """Test the filtering of InteractiveList by attribute"""
        ds = self._filter_test_ds
        arrays = self.list_class.from_dataset(
            ds, name="v1", ydim=[0, 1], prefer_list=True
        )
        arrays.extend(
            self.list_class.from_dataset(
                ds, name="v2", xdim=[0, 1], prefer_list=True
            ),
            new_name=True,
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(test=2)], ["arr0"]
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(test=3)], ["arr1"]
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(test=lambda i: i == 2)],
            ["arr0"],
        )

    def test_list_filter_4_coord(self):
        """Test the filtering of InteractiveList by the coordinate"""
        ds = self._filter_test_ds
        arrays = self.list_class.from_dataset(
            ds, name=["v1", "v2"], xdim=0, prefer_list=True
        )
        arrays.extend(
            self.list_class.from_dataset(
                ds, name=["v1", "v2"], xdim=1, prefer_list=True
            ),
            new_name=True,
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(xdim=0)], ["arr0"]
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(xdim=1)], ["arr1"]
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(xdim=1, method="sel")],
            ["arr1"],
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(xdim=lambda i: i == 0)],
            ["arr0"],
        )
        self.assertEqual(
            [
                arr.psy.arr_name
                for arr in arrays(xdim=lambda i: i == 1, method="sel")
            ],
            ["arr1"],
        )

    def test_list_filter_5_coord_list(self):
        """Test the filtering of InteractiveList by the coordinate with a list"""
        ds = self._filter_test_ds
        arrays = self.list_class.from_dataset(
            ds, name="v0", ydim=[0, 1], prefer_list=True
        )
        arrays.extend(
            self.list_class.from_dataset(
                ds, name="v0", ydim=[2, 3], prefer_list=True
            ),
            new_name=True,
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(ydim=[0, 1])], ["arr0"]
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(ydim=[2, 3])], ["arr1"]
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(ydim=[1, 2], method="sel")],
            ["arr0"],
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(ydim=[3, 4], method="sel")],
            ["arr1"],
        )

    def test_list_filter_6_mixed(self):
        """Test the filtering of InteractiveList by attribute"""
        ds = self._filter_test_ds
        arrays = self.list_class.from_dataset(
            ds, name="v0", ydim=[0, 1], prefer_list=True
        )
        arrays.extend(
            self.list_class.from_dataset(
                ds, name="v0", ydim=[2, 3], prefer_list=True
            ),
            new_name=True,
        )
        self.assertEqual(
            [arr.psy.arr_name for arr in arrays(name="v0", ydim=[2, 3])],
            ["arr1"],
        )

    @property
    def _from_dataset_test_variables(self):
        """The variables and coords needed for the from_dataset tests"""
        variables = {
            # 3d-variable
            "v0": xr.Variable(("time", "ydim", "xdim"), np.zeros((4, 4, 4))),
            # 2d-variable with time and x
            "v1": xr.Variable(
                (
                    "time",
                    "xdim",
                ),
                np.zeros((4, 4)),
            ),
            # 2d-variable with y and x
            "v2": xr.Variable(
                (
                    "ydim",
                    "xdim",
                ),
                np.zeros((4, 4)),
            ),
            # 1d-variable
            "v3": xr.Variable(("xdim",), np.zeros(4)),
        }
        coords = {
            "ydim": xr.Variable(("ydim",), np.arange(1, 5)),
            "xdim": xr.Variable(("xdim",), np.arange(4)),
            "time": xr.Variable(
                ("time",),
                pd.date_range("1999-01-01", "1999-05-01", freq="M").values,
            ),
        }
        return variables, coords

    def test_from_dataset_01_basic(self):
        """test creation without any additional information"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        arrays = self.list_class.from_dataset(ds)
        self.assertEqual(len(arrays), 4)
        self.assertEqual(set(arrays.names), set(variables))
        for arr in arrays:
            self.assertEqual(
                arr.dims,
                variables[arr.name].dims,
                msg="Wrong dimensions for variable " + arr.name,
            )
            self.assertEqual(
                arr.shape,
                variables[arr.name].shape,
                msg="Wrong shape for variable " + arr.name,
            )

    def test_from_dataset_02_name(self):
        """Test the from_dataset creation method with selected names"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        arrays = self.list_class.from_dataset(ds, name="v2")
        self.assertEqual(len(arrays), 1)
        self.assertEqual(set(arrays.names), {"v2"})
        for arr in arrays:
            self.assertEqual(
                arr.dims,
                variables[arr.name].dims,
                msg="Wrong dimensions for variable " + arr.name,
            )
            self.assertEqual(
                arr.shape,
                variables[arr.name].shape,
                msg="Wrong shape for variable " + arr.name,
            )

    def test_from_dataset_03_simple_selection(self):
        """Test the from_dataset creation method with x- and t-selection"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        arrays = self.list_class.from_dataset(ds, x=0, t=0)
        self.assertEqual(len(arrays), 4)
        self.assertEqual(set(arrays.names), set(variables))
        for arr in arrays:
            self.assertEqual(
                arr.xdim.ndim, 0, msg="Wrong x dimension for " + arr.name
            )
            if "time" in arr.dims:
                self.assertEqual(
                    arr.time,
                    coords["time"],
                    msg="Wrong time dimension for " + arr.name,
                )

    def test_from_dataset_04_exact_selection(self):
        """Test the from_dataset creation method with selected names"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        arrays = self.list_class.from_dataset(
            ds, ydim=2, method=None, name=["v0", "v2"]
        )
        self.assertEqual(len(arrays), 2)
        self.assertEqual(set(arrays.names), {"v0", "v2"})
        for arr in arrays:
            self.assertEqual(
                arr.ydim, 2, msg="Wrong ydim slice for " + arr.name
            )

    def test_from_dataset_05_exact_array_selection(self):
        """Test the from_dataset creation method with selected names"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        arrays = self.list_class.from_dataset(
            ds, ydim=[[2, 3]], method=None, name=["v0", "v2"]
        )
        self.assertEqual(len(arrays), 2)
        self.assertEqual(set(arrays.names), {"v0", "v2"})
        for arr in arrays:
            self.assertEqual(
                arr.ydim.values.tolist(),
                [2, 3],
                msg="Wrong ydim slice for " + arr.name,
            )

    def test_from_dataset_06_nearest_selection(self):
        """Test the from_dataset creation method with selected names"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        arrays = self.list_class.from_dataset(
            ds, ydim=1.7, method="nearest", name=["v0", "v2"]
        )
        self.assertEqual(len(arrays), 2)
        self.assertEqual(set(arrays.names), {"v0", "v2"})
        for arr in arrays:
            self.assertEqual(
                arr.ydim, 2, msg="Wrong ydim slice for " + arr.name
            )

    def test_from_dataset_07_time_selection(self):
        """Test the from_dataset creation method with selected names"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        arrays = self.list_class.from_dataset(
            ds, t="1999-02-28", method=None, name=["v0", "v1"]
        )
        self.assertEqual(len(arrays), 2)
        self.assertEqual(set(arrays.names), {"v0", "v1"})
        for arr in arrays:
            self.assertEqual(
                arr.time,
                coords["time"][1],
                msg="Wrong time slice for " + arr.name,
            )

    def test_from_dataset_08_time_array_selection(self):
        """Test the from_dataset creation method with selected names"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        # test with array of time
        arrays = self.list_class.from_dataset(
            ds, t=[coords["time"][1:3]], method=None, name=["v0", "v1"]
        )
        self.assertEqual(len(arrays), 2)
        self.assertEqual(set(arrays.names), {"v0", "v1"})
        for arr in arrays:
            self.assertEqual(
                arr.time.values.tolist(),
                coords["time"][1:3].values.tolist(),
                msg="Wrong time slice for " + arr.name,
            )

    def test_from_dataset_09_nearest_time_selection(self):
        """Test the from_dataset creation method with selected names"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        arrays = self.list_class.from_dataset(
            ds, t="1999-02-20", method="nearest", name=["v0", "v1"]
        )
        self.assertEqual(len(arrays), 2)
        self.assertEqual(set(arrays.names), {"v0", "v1"})
        for arr in arrays:
            self.assertEqual(
                arr.time,
                coords["time"][1],
                msg="Wrong time slice for " + arr.name,
            )

    def test_from_dataset_10_2_vars(self):
        """Test the creation of arrays out of two variables"""
        variables, coords = self._from_dataset_test_variables
        variables["v4"] = variables["v3"].copy()
        ds = xr.Dataset(variables, coords)
        arrays = self.list_class.from_dataset(
            ds, name=[["v3", "v4"], "v2"], xdim=[[2]], squeeze=False
        )
        self.assertEqual(len(arrays), 2)
        self.assertIn("variable", arrays[0].dims)
        self.assertEqual(
            arrays[0].coords["variable"].values.tolist(), ["v3", "v4"]
        )
        self.assertEqual(arrays[0].ndim, 2)

        self.assertEqual(arrays[1].name, "v2")
        self.assertEqual(arrays[1].ndim, variables["v2"].ndim)

    def test_from_dataset_11_list(self):
        """Test the creation of a list of InteractiveLists"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        # Create two lists, each containing two arrays of variables v1 and v2.
        # In the first list, the xdim dimensions are 0 and 1.
        # In the second, the xdim dimensions are both 2
        arrays = self.list_class.from_dataset(
            ds, name=[["v1", "v2"]], xdim=[[0, 1], 2], prefer_list=True
        )

        self.assertEqual(len(arrays), 2)
        self.assertIsInstance(arrays[0], psyd.InteractiveList)
        self.assertIsInstance(arrays[1], psyd.InteractiveList)
        self.assertEqual(len(arrays[0]), 2)
        self.assertEqual(len(arrays[1]), 2)
        self.assertEqual(arrays[0][0].xdim, 0)
        self.assertEqual(arrays[0][1].xdim, 1)
        self.assertEqual(arrays[1][0].xdim, 2)
        self.assertEqual(arrays[1][1].xdim, 2)

    def test_from_dataset_12_list_and_2_vars(self):
        """Test the creation of a list of Interactive lists with one array out
        of 2 variables"""
        variables, coords = self._from_dataset_test_variables
        variables["v4"] = variables["v3"].copy()
        ds = xr.Dataset(variables, coords)
        arrays = ds.psy.create_list(
            ds, name=[["v1", ["v3", "v4"]], ["v1", "v2"]], prefer_list=True
        )

        self.assertEqual(len(arrays), 2)
        self.assertIsInstance(arrays[0], psyd.InteractiveList)
        self.assertIsInstance(arrays[1], psyd.InteractiveList)
        self.assertEqual(len(arrays[0]), 2)
        self.assertEqual(len(arrays[1]), 2)

    def test_from_dataset_13_decoder_class(self):
        ds = xr.Dataset(*self._from_dataset_test_variables)

        class MyDecoder(psyd.CFDecoder):
            pass

        arrays = self.list_class.from_dataset(ds, name="v2", decoder=MyDecoder)
        self.assertIsInstance(arrays[0].psy.decoder, MyDecoder)

    def test_from_dataset_14_decoder_instance(self):
        ds = xr.Dataset(*self._from_dataset_test_variables)

        class MyDecoder(psyd.CFDecoder):
            pass

        decoder = MyDecoder(ds)

        arrays = self.list_class.from_dataset(ds, name="v2", decoder=decoder)
        self.assertIs(arrays[0].psy.decoder, decoder)

    def test_from_dataset_15_decoder_kws(self):
        ds = xr.Dataset(*self._from_dataset_test_variables)

        arrays = self.list_class.from_dataset(
            ds, name="v2", decoder=dict(x={"myx"})
        )
        self.assertEqual(arrays[0].psy.decoder.x, {"myx"})

    def test_from_dataset_16_default_slice(self):
        """Test selection with default_slice=0"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        arrays = self.list_class.from_dataset(
            ds, ydim=2, default_slice=0, method=None, name=["v0", "v2"]
        )
        self.assertEqual(len(arrays), 2)
        self.assertEqual(set(arrays.names), {"v0", "v2"})
        for arr in arrays:
            self.assertEqual(
                arr.ydim, 2, msg="Wrong ydim slice for " + arr.name
            )

    def test_array_info(self):
        variables, coords = self._from_dataset_test_variables
        variables["v4"] = variables["v3"].copy()
        ds = xr.Dataset(variables, coords)
        fname = osp.relpath(bt.get_file("test-t2m-u-v.nc"), ".")
        ds2 = xr.open_dataset(fname)
        arrays = ds.psy.create_list(
            name=[["v1", ["v3", "v4"]], ["v1", "v2"]], prefer_list=True
        )
        arrays.extend(
            ds2.psy.create_list(name=["t2m"], x=0, t=1), new_name=True
        )
        if xr_version < (0, 17):
            nc_store = ("xarray.backends.netCDF4_", "NetCDF4DataStore")
        else:
            nc_store = (None, None)
        self.assertEqual(
            arrays.array_info(engine="netCDF4"),
            dict(
                [
                    # first list contating an array with two variables
                    (
                        "arr0",
                        dict(
                            [
                                (
                                    "arr0",
                                    {
                                        "dims": {
                                            "t": slice(None),
                                            "x": slice(None),
                                        },
                                        "attrs": dict(),
                                        "store": (None, None),
                                        "name": "v1",
                                        "fname": None,
                                    },
                                ),
                                (
                                    "arr1",
                                    {
                                        "dims": {"y": slice(None)},
                                        "attrs": dict(),
                                        "store": (None, None),
                                        "name": [["v3", "v4"]],
                                        "fname": None,
                                    },
                                ),
                                ("attrs", dict()),
                            ]
                        ),
                    ),
                    # second list with two arrays containing each one variable
                    (
                        "arr1",
                        dict(
                            [
                                (
                                    "arr0",
                                    {
                                        "dims": {
                                            "t": slice(None),
                                            "x": slice(None),
                                        },
                                        "attrs": dict(),
                                        "store": (None, None),
                                        "name": "v1",
                                        "fname": None,
                                    },
                                ),
                                (
                                    "arr1",
                                    {
                                        "dims": {
                                            "y": slice(None),
                                            "x": slice(None),
                                        },
                                        "attrs": dict(),
                                        "store": (None, None),
                                        "name": "v2",
                                        "fname": None,
                                    },
                                ),
                                ("attrs", dict()),
                            ]
                        ),
                    ),
                    # last array from real dataset
                    (
                        "arr2",
                        {
                            "dims": {
                                "z": slice(None),
                                "y": slice(None),
                                "t": 1,
                                "x": 0,
                            },
                            "attrs": ds2.t2m.attrs,
                            "store": nc_store,
                            "name": "t2m",
                            "fname": fname,
                        },
                    ),
                    ("attrs", dict()),
                ]
            ),
        )
        return arrays

    def test_from_dict_01(self):
        """Test the creation from a dictionary"""
        arrays = self.test_array_info()
        d = arrays.array_info(engine="netCDF4")
        self.assertEqual(
            self.list_class.from_dict(d).array_info(), arrays[-1:].array_info()
        )
        d = arrays.array_info(ds_description={"ds"})
        self.assertEqual(
            self.list_class.from_dict(d).array_info(), arrays.array_info()
        )

    def test_from_dict_02_only(self):
        """Test the only keyword"""
        arrays = self.test_array_info()
        d = arrays.array_info(ds_description={"ds"})
        # test to use only the first 2
        self.assertEqual(
            self.list_class.from_dict(
                d, only=arrays.arr_names[1:]
            ).array_info(),
            arrays[1:].array_info(),
        )
        # test to a pattern
        self.assertEqual(
            self.list_class.from_dict(
                d, only="|".join(arrays.arr_names[1:])
            ).array_info(),
            arrays[1:].array_info(),
        )
        # test to a function
        self.assertEqual(
            self.list_class.from_dict(
                d,
                only=lambda n, info: (
                    n in arrays.arr_names[1:] and "name" not in "info"
                ),
            ).array_info(),
            arrays[1:].array_info(),
        )

    def test_from_dict_03_mfdataset(self):
        """Test opening a multifile dataset"""
        ds = xr.Dataset(*self._from_dataset_test_variables)
        ds1 = ds.isel(time=slice(0, 2))
        ds2 = ds.isel(time=slice(2, None))
        fname1 = tempfile.NamedTemporaryFile(
            suffix=".nc", prefix="tmp_psyplot_"
        ).name
        ds1.to_netcdf(fname1)
        self._created_files.add(fname1)
        fname2 = tempfile.NamedTemporaryFile(
            suffix=".nc", prefix="tmp_psyplot_"
        ).name
        ds2.to_netcdf(fname2)
        self._created_files.add(fname2)

        # now open the mfdataset
        ds = psyd.open_mfdataset([fname1, fname2])
        arrays = self.list_class.from_dataset(ds, name=["v0"], time=[0, 3])
        if xr_version >= (0, 18):
            ds.psy.filename = [fname1, fname2]
        self.assertEqual(
            self.list_class.from_dict(arrays.array_info()).array_info(),
            arrays.array_info(),
        )
        ds.close()

    def test_from_dict_04_concat_dim(self):
        """Test opening a multifile dataset that requires a ``concat_dim``"""
        ds = xr.Dataset(*self._from_dataset_test_variables)
        ds1 = ds.isel(time=0)
        ds2 = ds.isel(time=1)
        fname1 = tempfile.NamedTemporaryFile(
            suffix=".nc", prefix="tmp_psyplot_"
        ).name
        ds1.to_netcdf(fname1)
        self._created_files.add(fname1)
        fname2 = tempfile.NamedTemporaryFile(
            suffix=".nc", prefix="tmp_psyplot_"
        ).name
        ds2.to_netcdf(fname2)
        self._created_files.add(fname2)

        # now open the mfdataset
        ds = psyd.open_mfdataset(
            [fname1, fname2], concat_dim="time", combine="nested"
        )
        arrays = self.list_class.from_dataset(ds, name=["v0"], time=[0, 1])
        self.assertEqual(
            self.list_class.from_dict(arrays.array_info()).array_info(),
            arrays.array_info(),
        )

    def test_logger(self):
        """Test whether one can access the logger"""
        import logging

        arrays = self.test_array_info()
        self.assertIsInstance(arrays.logger, logging.Logger)


class TestInteractiveList(TestArrayList):
    """Test case for the :class:`psyplot.data.InteractiveList` class"""

    list_class = psyd.InteractiveList

    def test_to_dataframe(self):
        variables, coords = self._from_dataset_test_variables
        variables["v1"][:] = np.arange(variables["v1"].size).reshape(
            variables["v1"].shape
        )
        ds = xr.Dataset(variables, coords)
        arrays = psyd.InteractiveList.from_dataset(ds, name="v1", t=[0, 1])
        arrays.extend(
            psyd.InteractiveList.from_dataset(
                ds, name="v1", t=2, x=slice(1, 3)
            ),
            new_name=True,
        )
        self.assertEqual(len(arrays), 3)
        self.assertTrue(all(arr.ndim == 1 for arr in arrays), msg=arrays)
        df = arrays.to_dataframe()
        self.assertEqual(df.shape, (ds.xdim.size, 3))
        self.assertEqual(df.index.values.tolist(), ds.xdim.values.tolist())
        self.assertEqual(
            df[arrays[0].psy.arr_name].values.tolist(),
            ds.v1[0].values.tolist(),
        )
        self.assertEqual(
            df[arrays[1].psy.arr_name].values.tolist(),
            ds.v1[1].values.tolist(),
        )
        self.assertEqual(df[arrays[2].psy.arr_name].notnull().sum(), 2)
        self.assertEqual(
            df[arrays[2].psy.arr_name]
            .values[df[arrays[2].psy.arr_name].notnull().values]
            .tolist(),
            ds.v1[2, 1:3].values.tolist(),
        )


class AbsoluteTimeTest(unittest.TestCase, AlmostArrayEqualMixin):
    """TestCase for loading and storing absolute times"""

    _created_files = set()

    def setUp(self):
        self._created_files = set()

    def tearDown(self):
        for f in self._created_files:
            try:
                os.remove(f)
            except Exception:
                pass
        self._created_files.clear()

    @property
    def _test_ds(self):
        import pandas as pd
        import xarray as xr

        time = xr.Variable(
            "time",
            pd.to_datetime(
                [
                    "1979-01-01T12:00:00",
                    "1979-01-01T18:00:00",
                    "1979-01-01T18:30:00",
                ]
            ),
            encoding={"units": "day as %Y%m%d.%f"},
        )
        var = xr.Variable(("time", "x"), np.zeros((len(time), 5)))
        return xr.Dataset({"test": var}, {"time": time})

    def test_to_netcdf(self):
        """Test whether the data is stored correctly"""
        import netCDF4 as nc

        ds = self._test_ds
        fname = tempfile.NamedTemporaryFile(
            suffix=".nc", prefix="tmp_psyplot_"
        ).name
        self._created_files.add(fname)
        psyd.to_netcdf(ds, fname)
        with nc.Dataset(fname) as nco:
            self.assertAlmostArrayEqual(
                nco.variables["time"][:],
                [19790101.5, 19790101.75, 19790101.75 + 30.0 / (24.0 * 60.0)],
                rtol=0,
                atol=1e-5,
            )
            self.assertEqual(nco.variables["time"].units, "day as %Y%m%d.%f")
        return fname

    def test_open_dataset(self):
        fname = self.test_to_netcdf()
        ref_ds = self._test_ds
        ds = psyd.open_dataset(fname)
        self.assertEqual(
            pd.to_datetime(ds.time.values).tolist(),
            pd.to_datetime(ref_ds.time.values).tolist(),
        )


class FilenamesTest(unittest.TestCase):
    """Test whether the filenames can be extracted correctly"""

    @property
    def fname(self):
        return osp.join(osp.dirname(__file__), "test-t2m-u-v.nc")

    def _test_engine(self, engine):
        from importlib import import_module

        fname = self.fname
        ds = psyd.open_dataset(fname, engine=engine).load()
        self.assertEqual(ds.psy.filename, fname)
        store_mod, store = ds.psy.data_store
        # try to load the dataset
        mod = import_module(store_mod)
        try:
            ds2 = psyd.open_dataset(getattr(mod, store).open(fname))
        except AttributeError:
            ds2 = psyd.open_dataset(getattr(mod, store)(fname))
        ds.close()
        ds2.close()
        ds.psy.filename = None
        dumped_fname, dumped_store_mod, dumped_store = psyd.get_filename_ds(
            ds, dump=True, engine=engine, paths=True
        )
        self.assertTrue(dumped_fname)
        self.assertTrue(osp.exists(dumped_fname), msg="Missing %s" % fname)
        self.assertEqual(dumped_store_mod, store_mod)
        self.assertEqual(dumped_store, store)
        ds.close()
        ds.psy.filename = None
        os.remove(dumped_fname)

        dumped_fname, dumped_store_mod, dumped_store = psyd.get_filename_ds(
            ds, dump=True, engine=engine, paths=dumped_fname
        )
        self.assertTrue(dumped_fname)
        self.assertTrue(osp.exists(dumped_fname), msg="Missing %s" % fname)
        self.assertEqual(dumped_store_mod, store_mod)
        self.assertEqual(dumped_store, store)
        ds.close()
        os.remove(dumped_fname)

    @unittest.skipIf(xr_version >= (0, 17), "Not supported for xarray>=0.18")
    @unittest.skipIf(not with_nio, "Nio module not installed")
    def test_nio(self):
        self._test_engine("pynio")

    @unittest.skipIf(xr_version >= (0, 17), "Not supported for xarray>=0.18")
    @unittest.skipIf(not with_netcdf4, "netCDF4 module not installed")
    def test_netcdf4(self):
        self._test_engine("netcdf4")

    @unittest.skipIf(xr_version >= (0, 17), "Not supported for xarray>=0.18")
    @unittest.skipIf(not with_scipy, "scipy module not installed")
    def test_scipy(self):
        self._test_engine("scipy")


if __name__ == "__main__":
    unittest.main()
