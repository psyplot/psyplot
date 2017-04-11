"""Test the :mod:`psyplot.__main__` module"""
import sys
import os
import os.path as osp
import subprocess as spr
import yaml
import shutil
import tempfile
import unittest
from itertools import product
import six
import _base_testing as bt
import psyplot.__main__ as main
import psyplot.project as psy
import psyplot
import matplotlib.pyplot as plt
import test_plotter as tp
import inspect

remove_temp_files = True


class TestCommandLine(unittest.TestCase):
    """Test the command line utitliy of psyplot"""

    _created_files = set()

    def setUp(self):
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

    def _create_and_save_test_project(self):
        psy.register_plotter('test_plotter', module='test_plotter',
                             plotter_name='TestPlotter')
        sp = psy.plot.test_plotter(bt.get_file('test-t2m-u-v.nc'),
                                   name=['t2m', 'u'], time=[0, 1])
        self.assertEqual(len(sp), 4, sp)
        fname = tempfile.NamedTemporaryFile(
            suffix='.pkl', prefix='test_psyplot_').name
        self._created_files.add(fname)
        sp.save_project(fname, use_rel_paths=False)
        return sp, fname

    def test_get_parser(self):
        parser = main.get_parser()
        args = inspect.getargspec(main.make_plot)[0]
        for arg in args:
            self.assertIn(arg, parser.unfinished_arguments,
                          msg='Missing ' + arg)

    def test_main_01_from_project(self):
        """Test the :func:`psyplot.__main__.main` function"""
        if not six.PY2:
            with self.assertRaisesRegex(ValueError, 'filename'):
                main.main(['-o', 'test.pdf'])
        sp, fname1 = self._create_and_save_test_project()
        fname2 = tempfile.NamedTemporaryFile(
                    suffix='.pdf', prefix='test_psyplot_').name
        self._created_files.add(fname2)
        sp.save_project(fname1, use_rel_paths=False)
        psy.close('all')
        if six.PY2:
            main.main(['-p', fname1, '-o', fname2])
        else:
            with self.assertWarnsRegex(UserWarning, 'ignored'):
                main.main(['-p', fname1, '-o', fname2, '-n', 't2m'])
        self.assertTrue(osp.exists(fname2), msg='Missing ' + fname2)
        self.assertEqual(len(psy.gcp(True)), 4)

    def test_main_02_alternative_ds(self):

        sp, fname1 = self._create_and_save_test_project()
        fname2 = tempfile.NamedTemporaryFile(
            suffix='.pdf', prefix='test_psyplot_').name
        self._created_files.add(fname2)
        sp.save_project(fname1, use_rel_paths=False)
        psy.close('all')
        main.main([bt.get_file('circumpolar_test.nc'), '-p', fname1,
                   '-o', fname2])
        self.assertTrue(osp.exists(fname2), msg='Missing ' + fname2)
        mp = psy.gcp(True)
        self.assertEqual(len(mp), 4)
        self.assertEqual(
             set(t[0] for t in mp._get_dsnames(mp.array_info(
                 dump=False, use_rel_paths=False))),
             {bt.get_file('circumpolar_test.nc')})

    def test_main_03_dims(self):
        import yaml
        psy.register_plotter('test_plotter', module='test_plotter',
                             plotter_name='TestPlotter')
        fname2 = tempfile.NamedTemporaryFile(
            suffix='.pdf', prefix='test_psyplot_').name
        self._created_files.add(fname2)
        # create a formatoptions file
        fmt_file = tempfile.NamedTemporaryFile(
            suffix='.yml', prefix='test_psyplot_').name
        self._created_files.add(fmt_file)
        with open(fmt_file, 'w') as f:
            yaml.dump({'fmt1': 'fmt1', 'fmt2': 'fmt2'}, f)
        if not six.PY2:
            with self.assertRaisesRegex(ValueError, 'plotting method'):
                main.main([bt.get_file('test-t2m-u-v.nc'), '-o', fname2,
                           '-d', 'time,1,2', 'y,3,4', '-n', 'u', 'v'])
        main.main([bt.get_file('test-t2m-u-v.nc'), '-o', fname2,
                   '-d', 'time,1,2', 'y,3,4', '-n', 'u', 'v',
                   '-pm', 'test_plotter', '-fmt', fmt_file])
        mp = psy.gcp(True)
        self.assertEqual(len(mp), 2*2*2, msg=mp)
        all_dims = set(product((1, 2), (3, 4), ('u', 'v')))
        for arr in mp:
            idims = arr.psy.idims
            all_dims -= {(idims['time'], idims['lat'], arr.name)}
        self.assertFalse(all_dims)
        for i, plotter in enumerate(mp.plotters):
            self.assertEqual(plotter['fmt1'], 'fmt1',
                             msg='Wrong value for fmt1 of plotter %i!' % i)
            self.assertEqual(plotter['fmt2'], 'fmt2',
                             msg='Wrong value for fmt2 of plotter %i!' % i)

    def test_all_versions(self):
        """Test to display all versions"""
        ref = psyplot.get_versions()
        proc = spr.Popen([sys.executable, '-m', 'psyplot', '-aV'],
                         stdout=spr.PIPE, stderr=spr.PIPE)
        proc.wait()
        self.assertFalse(proc.poll(), msg=proc.stderr.read())
        d = yaml.load(proc.stdout.read())
        self.assertEqual(d, ref)

    def test_list_plugins(self):
        """Test to display all versions"""
        ref = psyplot.rcParams._plugins
        proc = spr.Popen([sys.executable, '-m', 'psyplot', '-lp'],
                         stdout=spr.PIPE, stderr=spr.PIPE)
        proc.wait()
        self.assertFalse(proc.poll(), msg=proc.stderr.read())
        d = yaml.load(proc.stdout.read())
        self.assertEqual(d, ref)

    def test_list_plot_methods(self):
        """Test to display all versions"""
        proc = spr.Popen([sys.executable, '-m', 'psyplot', '-lpm'],
                         stdout=spr.PIPE, stderr=spr.PIPE)
        proc.wait()
        self.assertFalse(proc.poll(), msg=proc.stderr.read())
        import psyplot.project as psy
        for pm, d in psyplot.rcParams['project.plotters'].items():
            try:
                psy.register_plotter(pm, **d)
            except:
                pass
        ref = psy.plot._plot_methods
        d = yaml.load(proc.stdout.read())
        self.assertEqual(d, ref)
