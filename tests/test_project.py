"""Test module of the :mod:`psyplot.project` module"""
import os
import os.path as osp
import shutil
import six
import unittest
from itertools import chain
import _base_testing as bt
import test_data as td
import test_plotter as tp
import xarray as xr
import psyplot.data as psyd
import psyplot.plotter as psyp
import psyplot.project as psy
import matplotlib.pyplot as plt

remove_temp_files = True


class TestProject(td.TestArrayList):
    """Testclass for the :class:`psyplot.project.Project` class"""

    _created_files = set()

    def setUp(self):
        for identifier in list(psy.registered_plotters):
            psy.unregister_plotter(identifier)
        psy.close('all')
        plt.close('all')
        self._created_files = set()

    def tearDown(self):
        for identifier in list(psy.registered_plotters):
            psy.unregister_plotter(identifier)
        psy.close('all')
        plt.close('all')
        tp.results.clear()
        if remove_temp_files:
            for f in self._created_files:
                if osp.exists(f) and osp.isdir(f):
                    shutil.rmtree(f)
                elif osp.exists(f):
                    os.remove(f)
            self._created_files.clear()

    def test_save_and_load_01_simple(self):
        """Test the saving and loading of a Project"""
        psy.register_plotter('test_plotter', import_plotter=True,
                             module='test_plotter', plotter_name='TestPlotter')
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        plt.close('all')
        sp = psy.plot.test_plotter(ds, name=['t2m', 'u'], x=0, y=4,
                                   ax=(2, 2, 1), fmt1='test')
        self.assertEqual(len(sp), 2)
        self.assertEqual(sp[0].psy.ax.get_figure().number, 1)
        self.assertEqual(sp[0].psy.ax.rowNum, 0)
        self.assertEqual(sp[0].psy.ax.colNum, 0)
        self.assertEqual(sp[0].psy.ax.numCols, 2)
        self.assertEqual(sp[0].psy.ax.numRows, 2)
        self.assertEqual(sp[1].psy.ax.get_figure().number, 2)
        self.assertEqual(sp[1].psy.ax.rowNum, 0)
        self.assertEqual(sp[1].psy.ax.colNum, 0)
        self.assertEqual(sp[1].psy.ax.numCols, 2)
        self.assertEqual(sp[1].psy.ax.numRows, 2)
        arr_names = sp.arr_names
        self.assertEqual(tp.results[arr_names[0] + '.fmt1'], 'test')
        self.assertEqual(tp.results[arr_names[1] + '.fmt1'], 'test')
        fname = 'test.pkl'
        self._created_files.add(fname)
        sp.save_project(fname)
        psy.close()
        tp.results.clear()
        sp = psy.Project.load_project(fname)
        self.assertEqual(len(sp), 2)
        self.assertEqual(sp[0].psy.ax.get_figure().number, 1)
        self.assertEqual(sp[0].psy.ax.rowNum, 0)
        self.assertEqual(sp[0].psy.ax.colNum, 0)
        self.assertEqual(sp[0].psy.ax.numCols, 2)
        self.assertEqual(sp[0].psy.ax.numRows, 2)
        self.assertEqual(sp[1].psy.ax.get_figure().number, 2)
        self.assertEqual(sp[1].psy.ax.rowNum, 0)
        self.assertEqual(sp[1].psy.ax.colNum, 0)
        self.assertEqual(sp[1].psy.ax.numCols, 2)
        self.assertEqual(sp[1].psy.ax.numRows, 2)

    def test_save_and_load_02_alternative_axes(self):
        """Test the saving and loading of a Project providing alternative axes
        """
        psy.register_plotter('test_plotter', import_plotter=True,
                             module='test_plotter', plotter_name='TestPlotter')
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        plt.close('all')
        sp = psy.plot.test_plotter(ds, name=['t2m', 'u'], x=0, y=4,
                                   ax=(2, 2, 1), fmt1='test')
        self.assertEqual(len(sp), 2)
        self.assertEqual(sp[0].psy.ax.get_figure().number, 1)
        self.assertEqual(sp[0].psy.ax.rowNum, 0)
        self.assertEqual(sp[0].psy.ax.colNum, 0)
        self.assertEqual(sp[0].psy.ax.numCols, 2)
        self.assertEqual(sp[0].psy.ax.numRows, 2)
        self.assertEqual(sp[1].psy.ax.get_figure().number, 2)
        self.assertEqual(sp[1].psy.ax.rowNum, 0)
        self.assertEqual(sp[1].psy.ax.colNum, 0)
        self.assertEqual(sp[1].psy.ax.numCols, 2)
        self.assertEqual(sp[1].psy.ax.numRows, 2)
        arr_names = sp.arr_names
        self.assertEqual(tp.results[arr_names[0] + '.fmt1'], 'test')
        self.assertEqual(tp.results[arr_names[1] + '.fmt1'], 'test')
        fname = 'test.pkl'
        self._created_files.add(fname)
        sp.save_project(fname)
        psy.close()
        tp.results.clear()
        fig, axes = plt.subplots(1, 2)
        sp = psy.Project.load_project(fname, alternative_axes=axes.ravel())
        self.assertEqual(len(sp), 2)
        self.assertEqual(sp[0].psy.ax.get_figure().number, 1)
        self.assertEqual(sp[0].psy.ax.rowNum, 0)
        self.assertEqual(sp[0].psy.ax.colNum, 0)
        self.assertEqual(sp[0].psy.ax.numCols, 2)
        self.assertEqual(sp[0].psy.ax.numRows, 1)
        self.assertEqual(sp[1].psy.ax.get_figure().number, 1)
        self.assertEqual(sp[1].psy.ax.rowNum, 0)
        self.assertEqual(sp[1].psy.ax.colNum, 1)
        self.assertEqual(sp[1].psy.ax.numCols, 2)
        self.assertEqual(sp[1].psy.ax.numRows, 1)

    def test_save_and_load_03_alternative_ds(self):
        """Test the saving and loading of a Project providing alternative axes
        """
        psy.register_plotter('test_plotter', import_plotter=True,
                             module='test_plotter', plotter_name='TestPlotter')
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        plt.close('all')
        sp = psy.plot.test_plotter(ds, name=['t2m', 'u'], x=0, y=4,
                                   ax=(2, 2, 1), fmt1='test')
        self.assertEqual(len(sp), 2)
        self.assertEqual(sp[0].psy.ax.get_figure().number, 1)
        self.assertEqual(sp[0].psy.ax.rowNum, 0)
        self.assertEqual(sp[0].psy.ax.colNum, 0)
        self.assertEqual(sp[0].psy.ax.numCols, 2)
        self.assertEqual(sp[0].psy.ax.numRows, 2)
        self.assertEqual(sp[1].psy.ax.get_figure().number, 2)
        self.assertEqual(sp[1].psy.ax.rowNum, 0)
        self.assertEqual(sp[1].psy.ax.colNum, 0)
        self.assertEqual(sp[1].psy.ax.numCols, 2)
        self.assertEqual(sp[1].psy.ax.numRows, 2)
        arr_names = sp.arr_names
        self.assertEqual(tp.results[arr_names[0] + '.fmt1'], 'test')
        self.assertEqual(tp.results[arr_names[1] + '.fmt1'], 'test')
        fname = 'test.pkl'
        self._created_files.add(fname)
        sp.save_project(fname)
        psy.close()
        tp.results.clear()
        fig, axes = plt.subplots(1, 2)
        ds = psy.open_dataset(bt.get_file('circumpolar_test.nc'))
        sp = psy.Project.load_project(fname, datasets=[ds])
        self.assertEqual(len(sp), 2)
        self.assertEqual(sp[0].psy.ax.get_figure().number, 1)
        self.assertEqual(sp[0].psy.ax.rowNum, 0)
        self.assertEqual(sp[0].psy.ax.colNum, 0)
        self.assertEqual(sp[0].psy.ax.numCols, 2)
        self.assertEqual(sp[0].psy.ax.numRows, 2)
        self.assertEqual(sp[1].psy.ax.get_figure().number, 2)
        self.assertEqual(sp[1].psy.ax.rowNum, 0)
        self.assertEqual(sp[1].psy.ax.colNum, 0)
        self.assertEqual(sp[1].psy.ax.numCols, 2)
        self.assertEqual(sp[1].psy.ax.numRows, 2)
        self.assertIs(sp[0].psy.base, ds)
        self.assertIs(sp[1].psy.base, ds)

    def test_save_and_load_04_alternative_fname(self):
        """Test the saving and loading of a Project providing alternative axes
        """
        psy.register_plotter('test_plotter', import_plotter=True,
                             module='test_plotter', plotter_name='TestPlotter')
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        plt.close('all')
        sp = psy.plot.test_plotter(ds, name=['t2m', 'u'], x=0, y=4,
                                   ax=(2, 2, 1), fmt1='test')
        self.assertEqual(len(sp), 2)
        self.assertEqual(sp[0].psy.ax.get_figure().number, 1)
        self.assertEqual(sp[0].psy.ax.rowNum, 0)
        self.assertEqual(sp[0].psy.ax.colNum, 0)
        self.assertEqual(sp[0].psy.ax.numCols, 2)
        self.assertEqual(sp[0].psy.ax.numRows, 2)
        self.assertEqual(sp[1].psy.ax.get_figure().number, 2)
        self.assertEqual(sp[1].psy.ax.rowNum, 0)
        self.assertEqual(sp[1].psy.ax.colNum, 0)
        self.assertEqual(sp[1].psy.ax.numCols, 2)
        self.assertEqual(sp[1].psy.ax.numRows, 2)
        arr_names = sp.arr_names
        self.assertEqual(tp.results[arr_names[0] + '.fmt1'], 'test')
        self.assertEqual(tp.results[arr_names[1] + '.fmt1'], 'test')
        fname = 'test.pkl'
        self._created_files.add(fname)
        sp.save_project(fname)
        psy.close()
        tp.results.clear()
        fig, axes = plt.subplots(1, 2)
        sp = psy.Project.load_project(
            fname, alternative_paths=[bt.get_file('circumpolar_test.nc')])
        self.assertEqual(len(sp), 2)
        self.assertEqual(sp[0].psy.ax.get_figure().number, 1)
        self.assertEqual(sp[0].psy.ax.rowNum, 0)
        self.assertEqual(sp[0].psy.ax.colNum, 0)
        self.assertEqual(sp[0].psy.ax.numCols, 2)
        self.assertEqual(sp[0].psy.ax.numRows, 2)
        self.assertEqual(sp[1].psy.ax.get_figure().number, 2)
        self.assertEqual(sp[1].psy.ax.rowNum, 0)
        self.assertEqual(sp[1].psy.ax.colNum, 0)
        self.assertEqual(sp[1].psy.ax.numCols, 2)
        self.assertEqual(sp[1].psy.ax.numRows, 2)
        self.assertEqual(psyd.get_filename_ds(sp[0].psy.base)[0],
                         bt.get_file('circumpolar_test.nc'))
        self.assertEqual(psyd.get_filename_ds(sp[1].psy.base)[0],
                         bt.get_file('circumpolar_test.nc'))

    def test_save_and_load_05_pack(self):
        import tempfile
        psy.register_plotter('test_plotter', import_plotter=True,
                             module='test_plotter', plotter_name='TestPlotter')
        tempdir1 = tempfile.mkdtemp(prefix='psyplot_test_')
        tempdir2 = tempfile.mkdtemp(prefix='psyplot_test_')
        tempdir3 = tempfile.mkdtemp(prefix='psyplot_test_')
        outdir = tempfile.mkdtemp(prefix='psyplot_test_')
        self._created_files.update([tempdir1, tempdir2, tempdir3, outdir])
        # first test file
        shutil.copyfile(bt.get_file('test-t2m-u-v.nc'),
                        osp.join(tempdir1, 'test-t2m-u-v.nc'))
        psy.plot.test_plotter(osp.join(tempdir1, 'test-t2m-u-v.nc'),
                              name='t2m', t=[1, 2])
        # second test file
        shutil.copyfile(bt.get_file('test-t2m-u-v.nc'),
                        osp.join(tempdir2, 'test-t2m-u-v.nc'))
        psy.plot.test_plotter(osp.join(tempdir2, 'test-t2m-u-v.nc'),
                              name='t2m', t=[3, 4])
        # third test file
        shutil.copyfile(bt.get_file('test-t2m-u-v.nc'),
                        osp.join(tempdir3, 'test-t2m-u-v.nc'))
        psy.plot.test_plotter(osp.join(tempdir3, 'test-t2m-u-v.nc'),
                              name='t2m', t=[3, 4])
        # fourth test file with different name
        psy.plot.test_plotter(bt.get_file('circumpolar_test.nc'), name='t2m',
                              t=[0, 1])
        mp = psy.gcp(True)

        mp.save_project(osp.join(outdir, 'test.pkl'), pack=True)
        files = {'test-t2m-u-v.nc', 'test-t2m-u-v-1.nc',
                 'test-t2m-u-v-2.nc', 'test.pkl', 'circumpolar_test.nc'}
        self.assertEqual(set(os.listdir(outdir)), files)

        psy.close(mp)

        # move the directory to check whether it is still working
        outdir2 = tempfile.mkdtemp(prefix='psyplot_test_')
        self._created_files.add(outdir2)
        for f in files:
            shutil.move(osp.join(outdir, f), osp.join(outdir2, f))
        mp = psy.Project.load_project(osp.join(outdir2, 'test.pkl'), main=True,
                                      )

        self.assertEqual(len(mp), 8, msg=mp)

        paths = {osp.join(outdir2, 'test-t2m-u-v.nc'),
                 osp.join(outdir2, 'test-t2m-u-v-1.nc'),
                 osp.join(outdir2, 'test-t2m-u-v-2.nc')}
        found = set()

        for i in range(6):
            found.add(psyd.get_filename_ds(mp[i].psy.base)[0])
        self.assertFalse(paths - found,
                         msg='expected %s\n%s\nfound %s' % (paths, '-' * 80,
                                                            found))
        self.assertEqual(psyd.get_filename_ds(mp[6].psy.base)[0],
                         osp.join(outdir2, 'circumpolar_test.nc'))
        self.assertEqual(psyd.get_filename_ds(mp[7].psy.base)[0],
                         osp.join(outdir2, 'circumpolar_test.nc'))
        
    def test_save_and_load_06_post_fmt(self):
        """Test whether the :attr:`psyplot.plotter.Plotter.post` fmt works"""
        psy.register_plotter('test_plotter', import_plotter=True,
                             module='test_plotter', plotter_name='TestPlotter')
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        plt.close('all')
        sp = psy.plot.test_plotter(ds, name=['t2m', 'u'], x=0, y=4,
                                   ax=(2, 2, 1), fmt1='test',
                                   post='self.ax.set_title("test")')
        self.assertEqual(sp.plotters[0].ax.get_title(), 'test')
        fname = 'test.pkl'
        self._created_files.add(fname)
        sp.save_project(fname)
        psy.close('all')
        # test without enabled post
        sp = psy.Project.load_project(fname)
        self.assertEqual(sp.plotters[0].ax.get_title(), '')
        psy.close('all')
        # test with enabled post
        sp = psy.Project.load_project(fname, enable_post=True)
        self.assertEqual(sp.plotters[0].ax.get_title(), 'test')
        

    def test_versions_and_patch(self):
        import warnings
        try:
            import psyplot_test.plugin as test_plugin
        except ImportError:
            self.skipTest("Could not import the psyplot_test package")
            return
        rc = psyd.rcParams
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            rc.load_plugins()
        psy._versions.clear()
        psy.register_plotter('test_plotter',
                             **rc['project.plotters']['test_plotter'])
        psy.register_plotter('test_plotter2', import_plotter=True,
                             module='test_plotter', plotter_name='TestPlotter')

        psy.plot.test_plotter(bt.get_file('test-t2m-u-v.nc'), name='t2m',
                              t=[1, 2])
        psy.plot.test_plotter2(bt.get_file('test-t2m-u-v.nc'), name='t2m',
                               t=[1, 2])
        mp = psy.gcp(True)
        self.assertEqual(len(mp), 4, msg=mp)
        d = mp.save_project()
        self.assertIn('versions', d)
        self.assertEqual(len(d['versions']), 2, msg=d['versions'])
        self.assertIn('psyplot', d['versions'])
        self.assertIn('psyplot_test.plugin', d['versions'])
        self.assertEqual(d['versions']['psyplot_test.plugin']['version'],
                         '1.0.0')

        # test the patch
        self.assertEqual(test_plugin.patch_check, [])
        test_plugin.checking_patch = True
        try:
            mp.close(True, True, True)
            mp = psy.Project.load_project(d)
            self.assertEqual(len(test_plugin.patch_check), 2)
            self.assertIs(test_plugin.patch_check[0]['plotter'],
                          d['arrays']['arr0']['plotter'])
            self.assertIs(test_plugin.patch_check[1]['plotter'],
                          d['arrays']['arr1']['plotter'])
            self.assertIs(test_plugin.patch_check[0]['versions'],
                          d['versions'])
            self.assertIs(test_plugin.patch_check[1]['versions'],
                          d['versions'])
        finally:
            test_plugin.checking_patch = False

    def test_keys(self):
        """Test the :meth:`psyplot.project.Project.keys` method"""
        import test_plotter as tp
        import psyplot.plotter as psyp
        psy.register_plotter('test_plotter', import_plotter=True,
                             module='test_plotter', plotter_name='TestPlotter')

        class TestPlotter2(tp.TestPlotter):
            fmt2 = None

        psy.register_plotter('test_plotter2', module='something',
                             plotter_name='anyway', plotter_cls=TestPlotter2)
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        sp1 = psy.plot.test_plotter(ds, name='v0')
        # add a second project without a fmt2 formatoption
        sp2 = psy.plot.test_plotter2(ds, name='v1')
        mp = sp1 + sp2
        self.assertEqual(sp1.keys(['fmt1', 'fmt2', 'fmt3'], func=str),
                         '+------+------+------+\n'
                         '| fmt1 | fmt2 | fmt3 |\n'
                         '+------+------+------+')
        self.assertEqual(mp.keys(['fmt1', 'fmt2', 'fmt3'], func=str),
                         '+------+------+\n'
                         '| fmt1 | fmt3 |\n'
                         '+------+------+')
        title = psyp.groups['labels']
        self.assertEqual(sp1.keys(['fmt1', 'fmt2', 'fmt3'], func=str, 
                                  grouped=True),
                         '*' * len(title) + '\n' +
                         title + '\n' +
                         '*' * len(title) + '\n'
                         '+------+------+\n'
                         '| fmt1 | fmt2 |\n'
                         '+------+------+\n'
                         '\n'
                         '*********\n'
                         'something\n'
                         '*********\n'
                         '+------+\n'
                         '| fmt3 |\n'
                         '+------+')
        self.assertEqual(mp.keys(['fmt1', 'fmt2', 'fmt3'], func=str, 
                                 grouped=True),
                         '*' * len(title) + '\n' +
                         title + '\n' +
                         '*' * len(title) + '\n'
                         '+------+\n'
                         '| fmt1 |\n'
                         '+------+\n'
                         '\n'
                         '*********\n'
                         'something\n'
                         '*********\n'
                         '+------+\n'
                         '| fmt3 |\n'
                         '+------+')
        self.assertEqual(sp1.keys(['fmt1', 'something'], func=str),
                         '+------+------+\n'
                         '| fmt1 | fmt3 |\n'
                         '+------+------+')
        if six.PY3:
            with self.assertWarnsRegex(UserWarning,
                                       '(?i)unknown formatoption keyword'):
                self.assertEqual(
                    sp1.keys(['fmt1', 'wrong', 'something'], func=str),
                    '+------+------+\n'
                    '| fmt1 | fmt3 |\n'
                    '+------+------+')

    def test_docs(self):
        """Test the :meth:`psyplot.project.Project.docs` method"""
        import test_plotter as tp
        import psyplot.plotter as psyp
        psy.register_plotter('test_plotter', import_plotter=True,
                             module='test_plotter', plotter_name='TestPlotter')

        class TestPlotter2(tp.TestPlotter):
            fmt2 = None

        psy.register_plotter('test_plotter2', module='something',
                             plotter_name='anyway', plotter_cls=TestPlotter2)
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        sp1 = psy.plot.test_plotter(ds, name='v0')
        # add a second project without a fmt2 formatoption
        sp2 = psy.plot.test_plotter2(ds, name='v1')
        mp = sp1 + sp2
        self.assertEqual(sp1.docs(func=str), '\n'.join([
            'fmt1', '====', tp.SimpleFmt.__doc__, '',
            'fmt2', '====', tp.SimpleFmt2.__doc__, '',
            'fmt3', '====', tp.SimpleFmt3.__doc__, '',
            'post', '====', psyp.PostProcessing.__doc__, '',
            'post_timing', '===========', psyp.PostTiming.__doc__, '']))
        # test summed project
        self.assertEqual(mp.docs(func=str), '\n'.join([
            'fmt1', '====', tp.SimpleFmt.__doc__, '',
            'fmt3', '====', tp.SimpleFmt3.__doc__, '',
            'post', '====', psyp.PostProcessing.__doc__, '',
            'post_timing', '===========', psyp.PostTiming.__doc__, '']))
        title = psyp.groups['labels']
        self.assertEqual(
            sp1.docs(['fmt1', 'fmt2', 'fmt3'], func=str, grouped=True), 
            '\n'.join([
                '*' * len(title),
                title,
                '*' * len(title),
                'fmt1', '====', tp.SimpleFmt.__doc__, '',
                'fmt2', '====', tp.SimpleFmt2.__doc__, '', '',
                '*********',
                'something',
                '*********',
                'fmt3', '====', tp.SimpleFmt3.__doc__]))
        # test summed project
        self.assertEqual(
            mp.docs(['fmt1', 'fmt3'], func=str, grouped=True), 
            '\n'.join([
                '*' * len(title),
                title,
                '*' * len(title),
                'fmt1', '====', tp.SimpleFmt.__doc__, '', '',
                '*********',
                'something',
                '*********',
                'fmt3', '====', tp.SimpleFmt3.__doc__]))

    def test_summaries(self):
        """Test the :meth:`psyplot.project.Project.summaries` method"""
        import test_plotter as tp
        import psyplot.plotter as psyp
        psy.register_plotter('test_plotter', import_plotter=True,
                             module='test_plotter', plotter_name='TestPlotter')

        class TestPlotter2(tp.TestPlotter):
            fmt2 = None

        psy.register_plotter('test_plotter2', module='something',
                             plotter_name='anyway', plotter_cls=TestPlotter2)
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        sp1 = psy.plot.test_plotter(ds, name='v0')
        # add a second project without a fmt2 formatoption
        sp2 = psy.plot.test_plotter2(ds, name='v1')
        mp = sp1 + sp2
        self.assertEqual(sp1.summaries(func=str), '\n'.join([
            'fmt1', tp.indent(tp.SimpleFmt.__doc__.splitlines()[0], '    '),
            'fmt2', tp.indent(tp.SimpleFmt2.__doc__.splitlines()[0], '    '),
            'fmt3', tp.indent(tp.SimpleFmt3.__doc__.splitlines()[0], '    '),
            'post', tp.indent(psyp.PostProcessing.__doc__.splitlines()[0], 
                              '    '),
            'post_timing', tp.indent(psyp.PostTiming.__doc__.splitlines()[0], 
                                     '    ')]))
        # test summed project
        self.assertEqual(mp.summaries(func=str), '\n'.join([
            'fmt1', tp.indent(tp.SimpleFmt.__doc__.splitlines()[0], '    '),
            'fmt3', tp.indent(tp.SimpleFmt3.__doc__.splitlines()[0], '    '),
            'post', tp.indent(psyp.PostProcessing.__doc__.splitlines()[0], 
                              '    '),
            'post_timing', tp.indent(psyp.PostTiming.__doc__.splitlines()[0], 
                                     '    ')]))
        title = psyp.groups['labels']
        self.assertEqual(
            sp1.summaries(['fmt1', 'fmt2', 'fmt3'], func=str, grouped=True), 
            '\n'.join([
                '*' * len(title),
                title,
                '*' * len(title),
                'fmt1', tp.indent(tp.SimpleFmt.__doc__.splitlines()[0], '    '),
                'fmt2', tp.indent(tp.SimpleFmt2.__doc__.splitlines()[0], '    '),
                '',
                '*********',
                'something',
                '*********',
                'fmt3', tp.indent(tp.SimpleFmt3.__doc__.splitlines()[0], '    ')]
            ))
        # test summed project
        self.assertEqual(
            mp.summaries(['fmt1', 'fmt3'], func=str, grouped=True), 
            '\n'.join([
                '*' * len(title),
                title,
                '*' * len(title),
                'fmt1', tp.indent(tp.SimpleFmt.__doc__.splitlines()[0], 
                                  '    '),
                '',
                '*********',
                'something',
                '*********',
                'fmt3', tp.indent(tp.SimpleFmt3.__doc__.splitlines()[0], 
                                  '    ')]
            ))

    def test_figs(self):
        """Test the :attr:`psyplot.project.Project.figs` attribute"""
        psy.register_plotter('test_plotter', import_plotter=True,
                             module='test_plotter', plotter_name='TestPlotter')
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        sp = psy.plot.test_plotter(ds, name='t2m', time=[1, 2])
        self.assertEqual(sp[0].psy.ax.figure.number, 1)
        self.assertEqual(sp[1].psy.ax.figure.number, 2)
        figs = sp.figs
        self.assertIn(sp[0].psy.ax.figure, figs)
        self.assertIs(figs[sp[0].psy.ax.figure][0], sp[0])
        self.assertIn(sp[1].psy.ax.figure, figs)
        self.assertIs(figs[sp[1].psy.ax.figure][0], sp[1])

    def test_axes(self):
        """Test the :attr:`psyplot.project.Project.axes` attribute"""
        psy.register_plotter('test_plotter', import_plotter=True,
                             module='test_plotter', plotter_name='TestPlotter')
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        sp = psy.plot.test_plotter(ds, name='t2m', time=[1, 2])
        self.assertIsNot(sp[0].psy.ax, sp[1].psy.ax)
        axes = sp.axes
        self.assertIn(sp[0].psy.ax, axes)
        self.assertIs(axes[sp[0].psy.ax][0], sp[0])
        self.assertIn(sp[1].psy.ax, axes)
        self.assertIs(axes[sp[1].psy.ax][0], sp[1])

    def test_close(self):
        """Test the :meth:`psyplot.project.Project.close` method"""
        psy.register_plotter('test_plotter', module='test_plotter',
                             plotter_name='TestPlotter')
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        sp1 = psy.plot.test_plotter(ds, name='t2m', time=[1, 2])
        sp2 = psy.plot.test_plotter(ds, name='t2m', time=[3, 4])
        mp = psy.gcp(True)
        names1 = sp1.arr_names
        names2 = sp2.arr_names
        # some checks in the beginning
        self.assertIs(sp1.main, mp)
        self.assertIs(sp2.main, mp)
        self.assertEqual(mp.arr_names, names1 + names2)
        self.assertEqual(mp.with_plotter.arr_names, names1 + names2)
        # close sp1
        sp1.close()
        self.assertEqual(mp.arr_names, names1 + names2)
        self.assertEqual(mp.with_plotter.arr_names, names2)
        # remove the data
        sp1.close(True, True)
        self.assertEqual(mp.arr_names, names2)
        self.assertEqual(mp.with_plotter.arr_names, names2)
        self.assertEqual(sp1, [])
        self.assertEqual(len(mp), 2)
        # close the dataset in sp2
        sp2.close(True, True, True)
        self.assertEqual(sp2, [])
        self.assertEqual(mp, [])
        if not six.PY2:
            with self.assertRaises((RuntimeError, AssertionError)):
                ds.t2m.values

    def test_close_global(self):
        """Test the :func:`psyplot.project.close` function"""
        psy.register_plotter('test_plotter', module='test_plotter',
                             plotter_name='TestPlotter')
        with psy.open_dataset(bt.get_file('test-t2m-u-v.nc')) as ds:
            time = ds.time.values
            lev = ds.lev.values
        mp0 = psy.plot.test_plotter(bt.get_file('test-t2m-u-v.nc'), name='t2m',
                                    lev=[0, 1]).main
        mp1 = psy.project()
        psy.plot.test_plotter(bt.get_file('test-t2m-u-v.nc'), name='t2m',
                              time=[1, 2])
        mp2 = psy.project()
        sp1 = psy.plot.test_plotter(bt.get_file('test-t2m-u-v.nc'), name='t2m',
                                    time=[3, 4])
        sp2 = psy.plot.test_plotter(bt.get_file('test-t2m-u-v.nc'), name='t2m',
                                    lev=[2, 3])
        # some checks in the beginning
        self.assertEqual(len(mp0), 2)
        self.assertEqual(len(mp1), 2)
        self.assertEqual(len(mp2), 4)
        self.assertEqual(mp0[0].lev.values, lev[0])
        self.assertEqual(mp0[1].lev.values, lev[1])
        self.assertEqual(mp1[0].time.values, time[1])
        self.assertEqual(mp1[1].time.values, time[2])
        self.assertEqual(mp2[0].time.values, time[3])
        self.assertEqual(mp2[1].time.values, time[4])
        self.assertEqual(mp2[2].lev.values, lev[2])
        self.assertEqual(mp2[3].lev.values, lev[3])
        self.assertIs(psy.gcp(True), mp2)
        self.assertIs(psy.gcp(), sp2)
        # close the current subproject
        ds = mp2[2].psy.base
        psy.close()
        if not six.PY2:
            with self.assertRaises((RuntimeError, AssertionError)):
                ds.u.values
        self.assertIs(psy.gcp(True), mp2)
        self.assertEqual(psy.gcp(), [])
        self.assertEqual(sp2, [])
        self.assertEqual(len(sp1), 2)
        self.assertEqual(mp2.arr_names, sp1.arr_names)
        # close the current mainproject
        ds = mp2[0].psy.base
        ds.v.values  # check that the data can be loaded
        psy.close(mp2.num)
        self.assertIs(psy.gcp(True), mp1)
        self.assertEqual(mp2, [])
        self.assertIs(psy.gcp().main, mp1)
        self.assertEqual(psy.gcp().arr_names, mp1.arr_names)
        if not six.PY2:
            with self.assertRaises((RuntimeError, AssertionError)):
                ds.u.values
        # close all projects
        ds0 = mp0[0].psy.base
        ds0.v.values  # check that the data can be loaded
        ds1 = mp1[0].psy.base
        ds1.v.values  # check that the data can be loaded
        psy.close('all')
        self.assertEqual(mp0, [])
        self.assertEqual(mp1, [])
        self.assertEqual(psy.gcp(), [])
        self.assertIsNot(psy.gcp(True), mp0)
        self.assertIsNot(psy.gcp(True), mp1)
        if not six.PY2:
            with self.assertRaises((RuntimeError, AssertionError)):
                ds0.u.values
                ds1.u.values

    def test_oncpchange_signal(self):
        """Test whether the correct signal is fired"""
        psy.register_plotter('test_plotter', module='test_plotter',
                             plotter_name='TestPlotter')
        check_mains = []
        projects = []

        def check(p):
            check_mains.append(p.is_main)
            projects.append(p)

        psy.Project.oncpchange.connect(check)
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc')).load()
        sp = psy.plot.test_plotter(ds, name='t2m', lev=[0, 1])
        # the signal should have been fired 2 times, one times from the
        # subproject, one times from the project
        self.assertEqual(len(check_mains), 2)
        self.assertIn(False, check_mains)
        self.assertIn(True, check_mains)
        self.assertEqual(len(projects[0]), 2, msg=str(projects[0]))
        self.assertEqual(len(projects[1]), 2, msg=str(projects[1]))

        # try scp
        check_mains = []
        projects = []
        p = sp[1:]
        psy.scp(p)
        self.assertEqual(check_mains, [False],
                         msg="projects: %s" % (projects, ))
        self.assertIs(projects[0], p)

        # test appending
        check_mains = []
        projects = []
        p.append(sp[0])
        self.assertEqual(check_mains, [False],
                         msg="projects: %s" % (projects, ))
        self.assertIs(projects[0], p)
        p.pop(1)

        # close a part of the project
        check_mains = []
        projects = []
        sp[:1].close(True, True)
        self.assertEqual(check_mains, [True])
        self.assertEqual(len(projects[0]), 1, msg=str(projects[0]))

        # close the remaining part of the project
        check_mains = []
        projects = []
        psy.close()
        self.assertEqual(len(check_mains), 2,
                         msg="%s, %s" % (check_mains, projects))
        self.assertIn(False, check_mains)
        self.assertIn(True, check_mains)
        self.assertEqual(len(projects[0]), 0, msg=str(projects[0]))
        self.assertEqual(len(projects[1]), 0, msg=str(projects[1]))

        psy.Project.oncpchange.disconnect(check)

    def test_share_01_on_creation(self):
        """Test the sharing within a project when creating it"""
        psy.register_plotter('test_plotter', module='test_plotter',
                             plotter_name='TestPlotter')
        sp = psy.plot.test_plotter(bt.get_file('test-t2m-u-v.nc'), name='t2m',
                                   time=[0, 1, 2], share='something')
        self.assertEqual(len(sp), 3, msg=sp)
        self.assertEqual(sp.plotters[0].fmt3.shared,
                         {sp.plotters[1].fmt3, sp.plotters[2].fmt3})
        sp[0].psy.update(fmt3='test3')
        self.assertEqual(sp.plotters[1].fmt3.value, 'test3')
        self.assertEqual(sp.plotters[2].fmt3.value, 'test3')

    def test_share_02_method(self):
        """Test the :meth:`psyplot.project.Project.share` method"""
        psy.register_plotter('test_plotter', module='test_plotter',
                             plotter_name='TestPlotter')
        sp = psy.plot.test_plotter(bt.get_file('test-t2m-u-v.nc'), name='t2m',
                                   time=[0, 1, 2])
        # share within the project
        sp.share(keys='something')
        self.assertEqual(len(sp), 3, msg=sp)
        self.assertEqual(sp.plotters[0].fmt3.shared,
                         {sp.plotters[1].fmt3, sp.plotters[2].fmt3})
        sp[0].psy.update(fmt3='test3')
        self.assertEqual(sp.plotters[1].fmt3.value, 'test3')
        self.assertEqual(sp.plotters[2].fmt3.value, 'test3')

        sp.unshare()
        self.assertFalse(sp.plotters[0].fmt3.shared)

        # share from outside the project
        sp[::2].share(sp[1], keys='something')
        self.assertEqual(sp.plotters[1].fmt3.shared,
                         {sp.plotters[0].fmt3, sp.plotters[2].fmt3})
        sp[1].psy.update(fmt3='test3')
        self.assertEqual(sp.plotters[0].fmt3.value, 'test3')
        self.assertEqual(sp.plotters[2].fmt3.value, 'test3')

        sp.unshare()
        self.assertFalse(sp.plotters[1].fmt3.shared)

    def test_share_03_method_by(self):
        """Test the :meth:`psyplot.project.Project.share` method by axes/figure
        """
        import matplotlib.pyplot as plt
        psy.register_plotter('test_plotter', module='test_plotter',
                             plotter_name='TestPlotter')
        fig1, ax1 = plt.subplots()
        fig2, axes = plt.subplots(1, 2)
        ax2, ax3 = axes
        sp = psy.plot.test_plotter(bt.get_file('test-t2m-u-v.nc'), name='t2m',
                                   time=range(4), ax=[ax1, ax2, ax1, ax3])

        self.assertEqual(len(sp), 4, msg=sp)

        # share by axes
        sp.share(by='axes', keys='something')
        self.assertEqual(sp.plotters[0].fmt3.shared,
                         {sp.plotters[2].fmt3})
        self.assertFalse(sp.plotters[1].fmt3.shared)
        self.assertFalse(sp.plotters[3].fmt3.shared)
        sp[0].psy.update(fmt3='test3')
        self.assertEqual(sp.plotters[2].fmt3.value, 'test3')

        sp.unshare()
        self.assertFalse(sp.plotters[0].fmt3.shared)

        # share by figure
        sp.share(by='fig', keys='something')
        self.assertEqual(sp.plotters[0].fmt3.shared,
                         {sp.plotters[2].fmt3})
        self.assertEqual(sp.plotters[1].fmt3.shared,
                         {sp.plotters[3].fmt3})
        sp[0].psy.update(fmt3='test3')
        sp[1].psy.update(fmt3='test4')
        self.assertEqual(sp.plotters[2].fmt3.value, 'test3')
        self.assertEqual(sp.plotters[3].fmt3.value, 'test4')

        sp.unshare()
        self.assertFalse(sp.plotters[0].fmt3.shared)
        self.assertFalse(sp.plotters[1].fmt3.shared)

        # share with provided bases by figure
        sp[2:].share(sp[:2], keys='something', by='fig')

        self.assertEqual(sp.plotters[0].fmt3.shared,
                         {sp.plotters[2].fmt3})
        self.assertEqual(sp.plotters[1].fmt3.shared,
                         {sp.plotters[3].fmt3})
        sp[0].psy.update(fmt3='test3')
        sp[1].psy.update(fmt3='test4')
        self.assertEqual(sp.plotters[2].fmt3.value, 'test3')
        self.assertEqual(sp.plotters[3].fmt3.value, 'test4')

        sp.unshare()
        self.assertFalse(sp.plotters[0].fmt3.shared)
        self.assertFalse(sp.plotters[1].fmt3.shared)

        # share with provided bases by axes
        sp[2:].share(sp[:2], keys='something', by='axes')
        self.assertEqual(sp.plotters[0].fmt3.shared,
                         {sp.plotters[2].fmt3})
        self.assertFalse(sp.plotters[1].fmt3.shared)
        self.assertFalse(sp.plotters[3].fmt3.shared)
        sp[0].psy.update(fmt3='test3')
        self.assertEqual(sp.plotters[2].fmt3.value, 'test3')

        sp.unshare()
        self.assertFalse(sp.plotters[0].fmt3.shared)

    def _register_export_plotter(self):
        class SimplePlotFormatoption(tp.TestFormatoption):

            plot_fmt = True
            priority = psyp.BEFOREPLOTTING

            def update(self, value):
                pass

            def make_plot(self):
                self.data.plot(ax=self.ax)

        class TestPlotter(psyp.Plotter):

            fmt1 = SimplePlotFormatoption('fmt1')

        psy.register_plotter('test_plotter', module='something',
                             plotter_name='irrelevant',
                             plotter_cls=TestPlotter)

    def test_export_01_replacement(self):
        """Test exporting a project"""
        import matplotlib.pyplot as plt
        from matplotlib.testing.compare import compare_images
        import pandas as pd
        import numpy as np
        from tempfile import NamedTemporaryFile

        self._register_export_plotter()

        with psy.open_dataset(bt.get_file('test-t2m-u-v.nc')) as ds:
            time = ds.time
            time.values  # make sure the data is loaded

        ds = xr.Dataset(
            {"v0": xr.Variable(('x', 'y'), np.arange(3 * 5).reshape(3, 5)),
             "v1": xr.Variable(('time', 'y'), np.arange(5 * 5).reshape(5, 5))},
            {"x": xr.Variable(('x', ), [4, 5, 6]),
             "y": xr.Variable(('y', ), [6, 7, 8, 9, 10]),
             'time': time})
        # create reference plots
        reffiles = []
        fig, ax = plt.subplots()
        ds.v0[1].plot(ax=ax)
        reffiles.append(
            NamedTemporaryFile(prefix='psyplot_', suffix='.png').name)
        self._created_files.update(reffiles)
        fig.savefig(reffiles[-1])

        # figure with two plots
        fig, axes = plt.subplots(1, 2)
        ds.v0.plot(ax=axes[0])
        ds.v0[1:].plot(ax=axes[1])
        reffiles.append(
            NamedTemporaryFile(prefix='psyplot_', suffix='.png').name)
        self._created_files.update(reffiles)
        fig.savefig(reffiles[-1])

        plt.close('all')

        # create project
        psy.plot.test_plotter(ds, name='v0', x=1, attrs={'test': 7},
                              ax=plt.subplots()[1])
        psy.plot.test_plotter(ds, name='v0', x=[slice(None), slice(1, None)],
                              attrs={'test': 3}, ax=plt.subplots(1, 2)[1])
        mp = psy.gcp(True)
        self.assertEqual(len(mp), 3, msg=mp)

        base_name = NamedTemporaryFile(prefix='psyplot_').name
        mp.export(base_name + '%i_%(test)s.png')
        # compare reference files and exported files
        self.assertTrue(osp.exists(base_name + '1_7.png'),
                        msg="Missing " + base_name + '1_7.png')
        self._created_files.add(base_name + '1_7.png')
        self.assertTrue(osp.exists(base_name + '2_3.png'),
                        msg="Missing " + base_name + '2_3.png')
        self._created_files.add(base_name + '2_3.png')
        results = compare_images(reffiles[0], base_name + '1_7.png', 1)
        self.assertIsNone(results, msg=results)
        results = compare_images(reffiles[1], base_name + '2_3.png', 1)
        self.assertIsNone(results, msg=results)

        # check time formatting
        psy.close(mp)
        reffiles = []
        fig, ax = plt.subplots()
        ds.v1[1].plot(ax=ax)
        reffiles.append(
            NamedTemporaryFile(prefix='psyplot_', suffix='.png').name)
        self._created_files.update(reffiles)
        fig.savefig(reffiles[-1])

        fig, axes = plt.subplots(1, 2)
        ds.v1[2, :2].plot(ax=axes[0])
        ds.v1[2, 2:].plot(ax=axes[1])
        reffiles.append(
            NamedTemporaryFile(prefix='psyplot_', suffix='.png').name)
        self._created_files.update(reffiles)
        fig.savefig(reffiles[-1])

        plt.close('all')

        # create project
        psy.plot.test_plotter(ds, name='v1', time=1, attrs={'test': 3},
                              ax=plt.subplots()[1])
        psy.plot.test_plotter(ds, name='v1', time=2, attrs={'test': 5},
                              y=[slice(0, 2), slice(2, None)],
                              ax=plt.subplots(1, 2)[1])
        mp = psy.gcp(True)
        self.assertEqual(len(mp), 3, msg=mp)
        mp.export(base_name + '%%i_%m_%%(test)s.png', use_time=True)

        # compare reference files and exported files
        t1 = pd.to_datetime(time.values[1]).strftime('%m')
        t2 = pd.to_datetime(time.values[2]).strftime('%m')
        self.assertTrue(osp.exists(base_name + ('1_%s_3.png' % t1)),
                        msg="Missing " + base_name + ('1_%s_3.png' % t1))
        self._created_files.add(base_name + ('1_%s_3.png' % t1))
        self.assertTrue(osp.exists(base_name + ('2_%s_5.png' % t2)),
                        msg="Missing " + base_name + ('2_%s_5.png' % t2))
        self._created_files.add(base_name + ('2_%s_5.png' % t2))
        results = compare_images(reffiles[0], base_name + ('1_%s_3.png' % t1),
                                 1)
        self.assertIsNone(results, msg=results)
        results = compare_images(reffiles[1], base_name + ('2_%s_5.png' % t2),
                                 1)
        self.assertIsNone(results, msg=results)

        # check pdf replacement
        psy.close(mp)
        sp = psy.plot.test_plotter(ds, name='v1', time=1, attrs={'test': 3},
                                   ax=plt.subplots()[1])
        sp.export(base_name + '%m_%%(test)s.pdf', use_time=True)
        self.assertTrue(osp.exists(base_name + ('%s_3.pdf' % t1)),
                        msg="Missing " + base_name + ('%s_3.pdf' % t1))
        self._created_files.add(base_name + ('%s_3.pdf' % t1))

    def test_export_02_list(self):
        """Test whether the exporting to a list works well"""
        import tempfile
        self._register_export_plotter()
        sp = psy.plot.test_plotter(bt.get_file('test-t2m-u-v.nc'),
                                   name='t2m', time=[1, 2, 3], z=0)
        self.assertEqual(len(sp), 3, msg=sp)

        fnames = list(
            tempfile.NamedTemporaryFile(suffix='.png', prefix='psyplot_').name
            for _ in range(3))
        self._created_files.update(fnames)

        sp.export(fnames)

        for fname in fnames:
            self.assertTrue(osp.exists(fname), msg="Missing " + fname)

    def test_export_03_append(self):
        """Append to a pdf file"""
        import tempfile
        self._register_export_plotter()
        fig1, ax1 = plt.subplots(1, 2)
        fig2, ax2 = plt.subplots()
        axes = list(ax1) + [ax2]
        sp = psy.plot.test_plotter(bt.get_file('test-t2m-u-v.nc'),
                                   name='t2m', time=[1, 2, 3], z=0, y=0,
                                   ax=axes)
        self.assertEqual(len(sp), 3, msg=sp)

        fname = tempfile.NamedTemporaryFile(
            suffix='.pdf', prefix='psyplot_').name
        self._created_files.add(fname)

        pdf = sp.export(fname, close_pdf=False)

        self.assertEqual(pdf.get_pagecount(), 2)

        sp.export(pdf)

        self.assertEqual(pdf.get_pagecount(), 4)

        pdf.close()

    def test_update(self):
        """Test the update of an :class:`psyplot.data.ArrayList`"""
        variables, coords = self._from_dataset_test_variables
        ds = xr.Dataset(variables, coords)
        psy.register_plotter('test_plotter', module='something',
                             plotter_name='unimportant',
                             plotter_cls=tp.TestPlotter)
        # add 2 arrays
        psy.plot.test_plotter(ds, name=['v0', 'v1'], t=0)
        # add a list
        psy.plot.test_plotter(ds, name=['v0', 'v1'], t=0, prefer_list=True)

        mp = psy.gcp(True)

        self.assertEqual(len(mp), 3, msg=mp)
        self.assertEqual(len(mp.plotters), 3, msg=mp)

        # update the list
        mp.update(t=1, fmt2='updated')

        for i, plotter in enumerate(mp.plotters):
            self.assertEqual(plotter['fmt2'], 'updated',
                             msg='Plotter of array %i not updated! %s' % (
                                i, mp[i]))

        self.assertEqual(mp[0].time, ds.time[1])
        self.assertEqual(mp[1].time, ds.time[1])
        for data in mp[2]:
            self.assertEqual(data.time, ds.time[1])


class TestPlotterInterface(unittest.TestCase):

    list_class = psy.Project

    def setUp(self):
        for identifier in list(psy.registered_plotters):
            psy.unregister_plotter(identifier)
        psy.close('all')
        plt.close('all')

    def tearDown(self):
        for identifier in list(psy.registered_plotters):
            psy.unregister_plotter(identifier)
        psy.close('all')
        plt.close('all')
        tp.results.clear()

    def test_plotter_registration(self):
        """Test the registration of a plotter"""
        psy.register_plotter('test_plotter',
                             import_plotter=True, module='test_plotter',
                             plotter_name='TestPlotter')
        self.assertTrue(hasattr(psy.plot, 'test_plotter'))
        self.assertIs(psy.plot.test_plotter.plotter_cls, tp.TestPlotter)
        psy.plot.test_plotter.print_func = str
        self.assertEqual(psy.plot.test_plotter.fmt1, tp.SimpleFmt.__doc__)
        psy.plot.test_plotter.print_func = None
        # test the warning
        if not six.PY2:
            with self.assertWarnsRegex(UserWarning, "not_existent_module"):
                psy.register_plotter('something', "not_existent_module",
                                     'not_important', import_plotter=True)
        psy.unregister_plotter('test_plotter')
        self.assertFalse(hasattr(psy.Project, 'test_plotter'))
        self.assertFalse(hasattr(psy.plot, 'test_plotter'))

    def test_plot_creation_01_array(self):
        """Test the plot creation with a plotter that takes one array"""
        psy.register_plotter('test_plotter',
                             import_plotter=True, module='test_plotter',
                             plotter_name='TestPlotter')
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        sp = psy.plot.test_plotter(ds, name='t2m')
        self.assertEqual(len(sp), 1)
        self.assertEqual(sp[0].name, 't2m')
        self.assertEqual(sp[0].shape, ds.t2m.shape)
        self.assertEqual(sp[0].values.tolist(), ds.t2m.values.tolist())
        psy.close()
        psy.unregister_plotter('test_plotter')

    def test_plot_creation_02_array_default_dims(self):
        # add a default value for the y dimension
        psy.register_plotter('test_plotter',
                             import_plotter=True, module='test_plotter',
                             plotter_name='TestPlotter',
                             default_dims={'y': 0})
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        sp = psy.plot.test_plotter(ds, name='t2m')
        self.assertEqual(len(sp), 1)
        self.assertEqual(sp[0].name, 't2m')
        self.assertEqual(sp[0].shape, ds.t2m.isel(lat=0).shape)
        self.assertEqual(sp[0].values.tolist(),
                         ds.t2m.isel(lat=0).values.tolist())
        psy.close()
        psy.unregister_plotter('test_plotter')

    def test_plot_creation_03_2arrays(self):
        # try multiple names and dimension
        psy.register_plotter('test_plotter',
                             import_plotter=True, module='test_plotter',
                             plotter_name='TestPlotter',
                             default_dims={'y': 0})
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        sp = psy.plot.test_plotter(ds, name=['t2m', 'u'], x=slice(3, 5))
        self.assertEqual(len(sp), 2)
        self.assertEqual(sp[0].name, 't2m')
        self.assertEqual(sp[1].name, 'u')
        self.assertEqual(sp[0].shape,
                         ds.t2m.isel(lat=0, lon=slice(3, 5)).shape)
        self.assertEqual(sp[1].shape,
                         ds.u.isel(lat=0, lon=slice(3, 5)).shape)
        self.assertEqual(sp[0].values.tolist(),
                         ds.t2m.isel(lat=0, lon=slice(3, 5)).values.tolist())
        self.assertEqual(sp[1].values.tolist(),
                         ds.u.isel(lat=0, lon=slice(3, 5)).values.tolist())
        psy.close()
        psy.unregister_plotter('test_plotter')

    def test_plot_creation_04_2variables(self):
        # test with array out of 2 variables
        psy.register_plotter('test_plotter',
                             import_plotter=True, module='test_plotter',
                             plotter_name='TestPlotter',
                             default_dims={'y': 0})
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        sp = psy.plot.test_plotter(ds, name=[['u', 'v']], x=slice(3, 5))
        self.assertEqual(len(sp), 1)
        self.assertIn('variable', sp[0].dims)
        self.assertEqual(sp[0].coords['variable'].values.tolist(), ['u', 'v'])
        self.assertEqual(list(sp[0].shape),
                         [2] + list(ds.t2m.isel(lat=0, lon=slice(3, 5)).shape))
        self.assertEqual(sp[0].values.tolist(),
                         ds[['u', 'v']].to_array().isel(
                             lat=0, lon=slice(3, 5)).values.tolist())
        psy.close()
        psy.unregister_plotter('test_plotter')

    def test_plot_creation_05_array_and_2variables(self):
        # test a combination of them
        # psyplot.project.Project([
        #     arr0: 2-dim DataArray of t2m, with
        #         (time, lev)=(5, 4), lon=1.875, lat=88.5721685,
        #     arr1: 2-dim DataArray of t2m, with
        #         (time, lev)=(5, 4), lon=3.75, lat=88.5721685,
        #     arr2: 3-dim DataArray of u, v, with
        #         (variable, time, lev)=(2, 5, 4), lat=88.5721685, lon=1.875,
        #     arr3: 3-dim DataArray of u, v, with
        #         (variable, time, lev)=(2, 5, 4), lat=88.5721685, lon=3.75])
        psy.register_plotter('test_plotter',
                             import_plotter=True, module='test_plotter',
                             plotter_name='TestPlotter',
                             default_dims={'y': 0})
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        sp = psy.plot.test_plotter(ds, name=['t2m', ['u', 'v']], x=[1, 2])
        self.assertEqual(len(sp), 4, msg=str(sp))
        self.assertEqual(sp[0].shape, ds.t2m.isel(lat=0, lon=1).shape)
        self.assertEqual(sp[1].shape, ds.t2m.isel(lat=0, lon=2).shape)
        self.assertEqual(list(sp[2].shape),
                         [2] + list(ds.u.isel(lat=0, lon=1).shape))
        self.assertEqual(list(sp[2].shape),
                         [2] + list(ds.u.isel(lat=0, lon=2).shape))
        self.assertEqual(sp[0].values.tolist(),
                         ds.t2m.isel(lat=0, lon=1).values.tolist())
        self.assertEqual(sp[1].values.tolist(),
                         ds.t2m.isel(lat=0, lon=2).values.tolist())
        self.assertEqual(sp[2].values.tolist(),
                         ds[['u', 'v']].isel(
                             lat=0, lon=1).to_array().values.tolist())
        self.assertEqual(sp[3].values.tolist(),
                         ds[['u', 'v']].isel(
                             lat=0, lon=2).to_array().values.tolist())
        psy.close()
        psy.unregister_plotter('test_plotter')

    def test_plot_creation_06_list(self):
        """Test the plot creation with a plotter that takes a list of arrays"""
        psy.register_plotter('test_plotter',
                             import_plotter=True, module='test_plotter',
                             plotter_name='TestPlotter', prefer_list=True)
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        # test the creation of one list
        # psyplot.project.Project([arr4: psyplot.data.InteractiveList([
        #     arr0: 4-dim DataArray of t2m, with
        #         (time, lev, lat, lon)=(5, 4, 96, 192), ,
        #     arr1: 4-dim DataArray of u, with
        #         (time, lev, lat, lon)=(5, 4, 96, 192), ])])
        sp = psy.plot.test_plotter(ds, name=['t2m', 'u'])
        self.assertEqual(len(sp), 1)
        self.assertEqual(len(sp[0]), 2)
        self.assertEqual(sp[0][0].name, 't2m')
        self.assertEqual(sp[0][1].name, 'u')
        self.assertEqual(sp[0][0].shape, ds.t2m.shape)
        self.assertEqual(sp[0][1].shape, ds.u.shape)
        self.assertEqual(sp[0][0].values.tolist(), ds.t2m.values.tolist())
        self.assertEqual(sp[0][1].values.tolist(), ds.u.values.tolist())
        psy.close()
        psy.unregister_plotter('test_plotter')

    def test_plot_creation_07_list_and_dims(self):
        # use dimensions which should result in one list with 4 arrays,
        # t2m, t2m, u, u
        # psyplot.project.Project([arr3: psyplot.data.InteractiveList([
        #     arr0: 3-dim DataArray of t2m, with
        #         (time, lev, lat)=(5, 4, 96), lon=1.875,
        #     arr1: 3-dim DataArray of t2m, with
        #         (time, lev, lat)=(5, 4, 96), lon=3.75,
        #     arr2: 3-dim DataArray of u, with
        #         (time, lev, lat)=(5, 4, 96), lon=1.875,
        #     arr3: 3-dim DataArray of u, with
        #         (time, lev, lat)=(5, 4, 96), lon=3.75])])
        psy.register_plotter('test_plotter',
                             import_plotter=True, module='test_plotter',
                             plotter_name='TestPlotter', prefer_list=True)
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        sp = psy.plot.test_plotter(ds, name=['t2m', 'u'], x=[1, 2])
        self.assertEqual(len(sp), 1)
        self.assertEqual(len(sp[0]), 4)
        self.assertEqual(sp[0][0].name, 't2m')
        self.assertEqual(sp[0][1].name, 't2m')
        self.assertEqual(sp[0][2].name, 'u')
        self.assertEqual(sp[0][3].name, 'u')
        self.assertEqual(sp[0][0].shape, ds.t2m.isel(lon=1).shape)
        self.assertEqual(sp[0][1].shape, ds.t2m.isel(lon=2).shape)
        self.assertEqual(sp[0][2].shape, ds.u.isel(lon=1).shape)
        self.assertEqual(sp[0][3].shape, ds.u.isel(lon=2).shape)
        self.assertEqual(sp[0][0].values.tolist(),
                         ds.t2m.isel(lon=1).values.tolist())
        self.assertEqual(sp[0][1].values.tolist(),
                         ds.t2m.isel(lon=2).values.tolist())
        self.assertEqual(sp[0][2].values.tolist(),
                         ds.u.isel(lon=1).values.tolist())
        self.assertEqual(sp[0][3].values.tolist(),
                         ds.u.isel(lon=2).values.tolist())
        psy.close()
        psy.unregister_plotter('test_plotter')

    def test_plot_creation_08_list_and_2variables(self):
        # test with arrays out of 2 variables. Should result in a list of
        # two arrays, both should have the two variables 't2m' and 'u'
        # psyplot.project.Project([arr2: psyplot.data.InteractiveList([
        #     arr0: 4-dim DataArray of t2m, u, with
        #         (variable, time, lev, lat)=(2, 5, 4, 96), lon=1.875,
        #     arr1: 4-dim DataArray of t2m, u, with
        #         (variable, time, lev, lat)=(2, 5, 4, 96), lon=3.75])])
        psy.register_plotter('test_plotter',
                             import_plotter=True, module='test_plotter',
                             plotter_name='TestPlotter', prefer_list=True)
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        sp = psy.plot.test_plotter(ds, name=[[['t2m', 'u']]], x=[1, 2])
        self.assertEqual(len(sp), 1)
        self.assertEqual(len(sp[0]), 2)
        self.assertIn('variable', sp[0][0].dims)
        self.assertIn('variable', sp[0][1].dims)
        self.assertEqual(list(sp[0][0].shape),
                         [2] + list(ds.t2m.isel(lon=1).shape))
        self.assertEqual(list(sp[0][1].shape),
                         [2] + list(ds.u.isel(lon=1).shape))
        self.assertEqual(
            sp[0][0].values.tolist(),
            ds[['t2m', 'u']].to_array().isel(lon=1).values.tolist())
        self.assertEqual(
            sp[0][1].values.tolist(),
            ds[['t2m', 'u']].to_array().isel(lon=2).values.tolist())
        psy.close()
        psy.unregister_plotter('test_plotter')

    def test_plot_creation_09_list_of_list_of_arrays(self):
        # test list of list of arrays
        # psyplot.project.Project([
        #     arr0: psyplot.data.InteractiveList([
        #         arr0: 3-dim DataArray of t2m, with
        #             (time, lev, lat)=(5, 4, 96), lon=1.875,
        #         arr1: 3-dim DataArray of u, with #
        #             (time, lev, lat)=(5, 4, 96), lon=1.875]),
        #     arr1: psyplot.data.InteractiveList([
        #         arr0: 3-dim DataArray of t2m, with
        #             (time, lev, lat)=(5, 4, 96), lon=3.75,
        #         arr1: 3-dim DataArray of u, with
        #             (time, lev, lat)=(5, 4, 96), lon=3.75])])
        psy.register_plotter('test_plotter',
                             import_plotter=True, module='test_plotter',
                             plotter_name='TestPlotter', prefer_list=True)
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        sp = psy.plot.test_plotter(bt.get_file('test-t2m-u-v.nc'),
                                   name=[['t2m', 'u']], x=[1, 2])
        self.assertEqual(len(sp), 2)
        self.assertEqual(len(sp[0]), 2)
        self.assertEqual(len(sp[1]), 2)
        self.assertEqual(sp[0][0].name, 't2m')
        self.assertEqual(sp[0][1].name, 'u')
        self.assertEqual(sp[1][0].name, 't2m')
        self.assertEqual(sp[1][1].name, 'u')
        self.assertEqual(sp[0][0].shape, ds.t2m.isel(lon=1).shape)
        self.assertEqual(sp[0][1].shape, ds.u.isel(lon=1).shape)
        self.assertEqual(sp[1][0].shape, ds.t2m.isel(lon=2).shape)
        self.assertEqual(sp[1][1].shape, ds.u.isel(lon=2).shape)
        self.assertEqual(sp[0][0].values.tolist(),
                         ds.t2m.isel(lon=1).values.tolist())
        self.assertEqual(sp[0][1].values.tolist(),
                         ds.u.isel(lon=1).values.tolist())
        self.assertEqual(sp[1][0].values.tolist(),
                         ds.t2m.isel(lon=2).values.tolist())
        self.assertEqual(sp[1][1].values.tolist(),
                         ds.u.isel(lon=2).values.tolist())
        psy.close()
        ds.close()
        psy.unregister_plotter('test_plotter')

    def test_plot_creation_10_list_array_and_2variables(self):
        # test list of list with array and an array out of 2 variables
        # psyplot.project.Project([
        #     arr0: psyplot.data.InteractiveList([
        #         arr0: 3-dim DataArray of t2m, with
        #             (time, lev, lat)=(5, 4, 96), lon=1.875,
        #         arr1: 4-dim DataArray of u, v, with
        #             (variable, time, lev, lat)=(2, 5, 4, 96), lon=1.875]),
        #     arr1: psyplot.data.InteractiveList([
        #         arr0: 3-dim DataArray of t2m, with
        #             (time, lev, lat)=(5, 4, 96), lon=1.875,
        #         arr1: 4-dim DataArray of u, v, with
        #             (variable, time, lev, lat)=(2, 5, 4, 96), lon=1.875])])
        psy.register_plotter('test_plotter',
                             import_plotter=True, module='test_plotter',
                             plotter_name='TestPlotter', prefer_list=True)
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        sp = psy.plot.test_plotter(ds, name=[['t2m', ['u', 'v']]], x=[1, 2])
        self.assertEqual(len(sp), 2)
        self.assertEqual(len(sp[0]), 2)
        self.assertEqual(len(sp[1]), 2)
        self.assertEqual(sp[0][0].name, 't2m')
        self.assertIn('variable', sp[0][1].dims)
        self.assertEqual(sp[0][1].coords['variable'].values.tolist(),
                         ['u', 'v'])
        self.assertEqual(sp[1][0].name, 't2m')
        self.assertIn('variable', sp[1][1].dims)
        self.assertEqual(sp[1][1].coords['variable'].values.tolist(),
                         ['u', 'v'])
        self.assertEqual(sp[0][0].shape, ds.t2m.isel(lon=1).shape)
        self.assertEqual(list(sp[0][1].shape),
                         [2] + list(ds.u.isel(lon=1).shape))
        self.assertEqual(sp[1][0].shape, ds.t2m.isel(lon=2).shape)
        self.assertEqual(list(sp[1][1].shape),
                         [2] + list(ds.u.isel(lon=2).shape))
        self.assertEqual(sp[0][0].values.tolist(),
                         ds.t2m.isel(lon=1).values.tolist())
        self.assertEqual(sp[0][1].values.tolist(),
                         ds[['u', 'v']].isel(lon=1).to_array().values.tolist())
        self.assertEqual(sp[1][0].values.tolist(),
                         ds.t2m.isel(lon=2).values.tolist())
        self.assertEqual(sp[1][1].values.tolist(),
                         ds[['u', 'v']].isel(lon=2).to_array().values.tolist())
        psy.close()
        psy.unregister_plotter('test_plotter')
        
    def test_plot_creation_11_post_fmt(self):
        """Test the :attr:`psyplot.plotter.Plotter.post` formatoption"""
        psy.register_plotter('test_plotter',
                             import_plotter=True, module='test_plotter',
                             plotter_name='TestPlotter')
        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        # test whether it is plotted automatically
        sp = psy.plot.test_plotter(ds, name='t2m', 
                                   post='self.ax.set_title("test")')
        self.assertEqual(sp.plotters[0].ax.get_title(), 'test')
        # test whether the disabling works
        sp = psy.plot.test_plotter(ds, name='t2m', enable_post=False,
                                   post='self.ax.set_title("test")')
        self.assertEqual(sp.plotters[0].ax.get_title(), '')

    def test_check_data(self):
        """Test the :meth:`psyplot.project._PlotterInterface.check_data` method
        """

        class TestPlotter(psyp.Plotter):

            @classmethod
            def check_data(cls, name, dims, is_unstructured):
                checks, messages = super(TestPlotter, cls).check_data(
                    name, dims, is_unstructured)
                self.assertEqual(name, ['t2m'])
                for n, d in zip(name, dims):
                    self.assertEqual(len(d),
                                     len(set(ds.t2m.dims) - {'lev', 'lon'}))
                    self.assertEqual(set(d), set(ds.t2m.dims) - {'lev', 'lon'})

        ds = psy.open_dataset(bt.get_file('test-t2m-u-v.nc'))

        psy.register_plotter('test_plotter', module='nothing',
                             plotter_name='dont_care', plotter_cls=TestPlotter,
                             default_dims={'x': 1}, default_slice=slice(1, 3))

        psy.plot.test_plotter.check_data(ds, 't2m', {'lev': 3})
        psy.unregister_plotter('test_plotter')


@unittest.skipIf(not psy.with_cdo, "Cdo not installed")
class TestCdo(unittest.TestCase):

    def setUp(self):
        psy.close('all')
        plt.close('all')

    def tearDown(self):
        for identifier in list(psy.registered_plotters):
            psy.unregister_plotter(identifier)
        psy.close('all')
        plt.close('all')
        tp.results.clear()

    def test_cdo(self):
        cdo = psy.Cdo()
        sp = cdo.timmean(input=bt.get_file('test-t2m-u-v.nc'),
                         name='t2m', dims=dict(z=[1, 2]))
        with psy.open_dataset(bt.get_file('test-t2m-u-v.nc')) as ds:
            lev = ds.lev.values
        self.assertEqual(len(sp), 2, msg=str(sp))
        self.assertEqual(sp[0].name, 't2m')
        self.assertEqual(sp[1].name, 't2m')
        self.assertEqual(sp[0].lev.values, lev[1])
        self.assertEqual(sp[1].lev.values, lev[2])
        self.assertIsNone(sp[0].psy.plotter)
        self.assertIsNone(sp[1].psy.plotter)

    def test_cdo_plotter(self):
        cdo = psy.Cdo()
        psy.register_plotter('test_plotter', module='test_plotter',
                             plotter_name='TestPlotter')
        sp = cdo.timmean(input=bt.get_file('test-t2m-u-v.nc'),
                         name='t2m', dims=dict(z=[1, 2]),
                         plot_method='test_plotter')
        with psy.open_dataset(bt.get_file('test-t2m-u-v.nc')) as ds:
            lev = ds.lev.values
        self.assertEqual(len(sp), 2, msg=str(sp))
        self.assertEqual(sp[0].name, 't2m')
        self.assertEqual(sp[1].name, 't2m')
        self.assertEqual(sp[0].lev.values, lev[1])
        self.assertEqual(sp[1].lev.values, lev[2])
        self.assertIsInstance(sp[0].psy.plotter, tp.TestPlotter)
        self.assertIsInstance(sp[1].psy.plotter, tp.TestPlotter)


class TestMultipleSubplots(unittest.TestCase):

    def test_one_subplot(self):
        plt.close('all')
        axes = psy.multiple_subplots()
        self.assertEqual(len(axes), 1)
        self.assertEqual(plt.get_fignums(), [1])
        self.assertEqual(len(plt.gcf().axes), 1)
        self.assertIs(axes[0], plt.gcf().axes[0])
        plt.close('all')

    def test_multiple_subplots(self):
        plt.close('all')
        axes = psy.multiple_subplots(2, 2, 3, 5)
        self.assertEqual(len(axes), 5)
        self.assertEqual(plt.get_fignums(), [1, 2])
        self.assertEqual(len(plt.figure(1).axes), 3)
        self.assertEqual(len(plt.figure(2).axes), 2)
        it_ax = iter(axes)
        for ax2 in chain(plt.figure(1).axes, plt.figure(2).axes):
            self.assertIs(next(it_ax), ax2)
        plt.close('all')


if __name__ == '__main__':
    unittest.main()
