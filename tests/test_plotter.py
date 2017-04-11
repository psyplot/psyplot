"""Test module of the basic functionality in the :mod:`psyplot.plotter` module
"""
import unittest
import six
import os.path as osp
import _base_testing as bt
from psyplot.compat.pycompat import OrderedDict
import psyplot.data as psyd
import pandas as pd
import xarray as xr
import psyplot.plotter as psyp
from itertools import repeat
from psyplot import rcParams
import psyplot.config as psyc
try:
    from textwrap import indent
except ImportError:
    def indent(text, prefix, predicate=None):  # python2
        return '\n'.join(prefix + s if predicate is None or predicate(s) else s
                         for s in text.splitlines())


docstrings = psyp.docstrings


psyc.setup_logging(osp.join(osp.dirname(__file__), 'logging.yml'))


results = OrderedDict()


class TestFormatoption(psyp.Formatoption):

    @property
    def default(self):
        try:
            return super(TestFormatoption, self).default
        except KeyError:
            return ''

    _validate = str

    def update(self, value):
        key = '%s.%s' % (self.plotter.data.psy.arr_name, self.key)
        if not value:
            results.pop(key, None)
        else:
            results[key] = value


@docstrings.save_docstring('_testing.SimpleFmt')
@docstrings.get_sectionsf('_testing.SimpleFmt')
class SimpleFmt(TestFormatoption):
    """
    Just a simple formatoption to check the sharing possibility

    Possible types
    --------------
    str
        The string to use in the text"""

    group = 'labels'

    children = ['fmt2']

    dependencies = ['fmt3']


class SimpleFmt2(SimpleFmt):
    """%(_testing.SimpleFmt)s"""

    children = ['fmt3']

    dependencies = []


class SimpleFmt3(SimpleFmt):
    """
    Third test to check the sharing by groups

    Possible types
    --------------
    %(_testing.SimpleFmt.possible_types)s"""

    group = 'something'

    children = dependencies = []


ref_docstring = """Third test to check the sharing by groups

Possible types
--------------
str
    The string to use in the text"""


class TestPlotter(psyp.Plotter):
    """A simple Plotter for testing the plotter-formatoption framework"""

    fmt1 = SimpleFmt('fmt1')
    fmt2 = SimpleFmt2('fmt2')
    fmt3 = SimpleFmt3('fmt3')
    
    
class TestPostFormatoption(unittest.TestCase):
    """TestCase for the :class:`psyplot.plotter.PostProcessing` formatoption"""
    
    def test_timing(self):
        plotter = TestPlotter(xr.DataArray([]), enable_post=True)
        # test attribute for the formatoption
        plotter.post.test = []
        plotter.update(
            post='self.test.append(1)')
        # check if the post fmt has been updated
        self.assertEqual(plotter.post.test, [1])
        plotter.update(fmt1='something')
        # check if the post fmt has been updated
        self.assertEqual(plotter.post.test, [1])
        
        # -- test replot timing
        plotter.update(post_timing='replot')
        plotter.update(fmt1='something else')
        # check if the post fmt has been updated
        self.assertEqual(plotter.post.test, [1])
        plotter.update(fmt2='test', replot=True)
        # check if the post fmt has been updated
        self.assertEqual(plotter.post.test, [1, 1])
        
        # -- test always timing
        plotter.update(post_timing='always')
        # check if the post fmt has been updated
        self.assertEqual(plotter.post.test, [1, 1, 1])
        plotter.update(fmt1='okay')
        # check if the post fmt has been updated
        self.assertEqual(plotter.post.test, [1, 1, 1, 1])
        
    def test_enable(self):
        """Test if the warning is raised"""
        plotter = TestPlotter(xr.DataArray([]), 
                              post='self.ax.set_title("test")')
        self.assertEqual(plotter.ax.get_title(), '')
        plotter.enable_post = True
        plotter.update(post=plotter.post.value, force=True)
        self.assertEqual(plotter.ax.get_title(), 'test')


class PlotterTest(unittest.TestCase):
    """TestCase for testing the Plotter-Formatoption framework"""

    def setUp(self):
        results.clear()
        rcParams.defaultParams = rcParams.defaultParams.copy()

    def tearDown(self):
        results.clear()
        rcParams.clear()
        rcParams.defaultParams = psyc.rcsetup.defaultParams
        rcParams.update_from_defaultParams()

    def test_docstring(self):
        """Testing the docstring processing of formatoptions"""
        self.assertEqual(SimpleFmt.__doc__, SimpleFmt2.__doc__)
        self.assertEqual(SimpleFmt3.__doc__, ref_docstring)

    def test_shared(self):
        """Testing the sharing of formatoptions"""
        plotter1 = TestPlotter(xr.DataArray([]))
        plotter2 = TestPlotter(xr.DataArray([]))
        plotter1.data.psy.arr_name = 'test1'
        plotter2.data.psy.arr_name = 'test2'

        results.clear()
        # test sharing of two formatoptions
        plotter1.share(plotter2, ['fmt1', 'fmt3'])
        plotter1.update(fmt1='okay', fmt3='okay2')
        # check source
        self.assertIn('test1.fmt1', results)
        self.assertEqual(results['test1.fmt1'], 'okay')
        self.assertIn('test1.fmt3', results)
        self.assertEqual(results['test1.fmt3'], 'okay2')
        # checked shared
        self.assertIn('test2.fmt1', results)
        self.assertEqual(results['test2.fmt1'], 'okay')
        self.assertIn('test2.fmt3', results)
        self.assertEqual(results['test2.fmt3'], 'okay2')

        # unshare the formatoptions
        plotter1.unshare(plotter2)
        # check source
        self.assertIn('test1.fmt1', results)
        self.assertEqual(results['test1.fmt1'], 'okay')
        self.assertIn('test1.fmt3', results)
        self.assertEqual(results['test1.fmt3'], 'okay2')
        # check (formerly) shared
        self.assertNotIn('test2.fmt1', results,
                         msg='Value of fmt1: %s, in results: %s' % (
                            plotter2.fmt1.value, results.get('test2.fmt1')))
        self.assertNotIn('test2.fmt3', results,
                         msg='Value of fmt3: %s, in results: %s' % (
                            plotter2.fmt3.value, results.get('test2.fmt3')))

        # test sharing of a group of formatoptions
        plotter1.share(plotter2, 'labels')
        plotter1.update(fmt1='okay', fmt2='okay2')
        # check source
        self.assertIn('test1.fmt1', results)
        self.assertEqual(results['test1.fmt1'], 'okay')
        self.assertIn('test1.fmt2', results)
        self.assertEqual(results['test1.fmt2'], 'okay2')
        # check shared
        self.assertIn('test2.fmt1', results)
        self.assertEqual(results['test2.fmt1'], 'okay')
        self.assertIn('test2.fmt2', results)
        self.assertEqual(results['test2.fmt2'], 'okay2')
        self.assertNotIn('test2.fmt3', results)

        # unshare the plotter
        plotter2.unshare_me('fmt1')
        self.assertNotIn('test2.fmt1', results)
        self.assertIn('test2.fmt2', results)
        plotter2.unshare_me('labels')
        self.assertNotIn('test2.fmt2', results)

    def test_auto_update(self):
        """Test the :attr:`psyplot.plotter.Plotter.no_auto_update` attribute"""
        data = xr.DataArray([])
        plotter = TestPlotter(data, auto_update=False)
        self.assertFalse(plotter.no_auto_update)
        data.psy.init_accessor(auto_update=False)
        plotter = TestPlotter(data, auto_update=False)
        self.assertTrue(plotter.no_auto_update)

        plotter.update(fmt1=1)
        self.assertEqual(plotter['fmt1'], '')
        self.assertEqual(plotter._registered_updates['fmt1'], 1)

        plotter.start_update()
        self.assertEqual(plotter['fmt1'], '1')
        self.assertFalse(plotter._registered_updates)

        data.psy.no_auto_update = False
        self.assertFalse(plotter.data.psy.no_auto_update)
        self.assertFalse(plotter.no_auto_update)

    def test_rc(self):
        """Test the default values and validation
        """
        def validate(s):
            return s + 'okay'
        rcParams.defaultParams = rcParams.defaultParams.copy()
        rcParams.defaultParams['plotter.test1.fmt1'] = ('test1', validate)
        rcParams.defaultParams['plotter.test1.fmt2'] = ('test2', validate)
        rcParams.defaultParams['plotter.test1.fmt3'] = ('test3', validate)
        rcParams.defaultParams['plotter.test2.fmt3'] = ('test3.2', validate)
        rcParams.update(**{
            key: val[0] for key, val in rcParams.defaultParams.items()})

        class ThisTestPlotter(TestPlotter):
            _rcparams_string = ['plotter.test1.']

        class ThisTestPlotter2(ThisTestPlotter):
            _rcparams_string = ['plotter.test2.']

        plotter1 = ThisTestPlotter(xr.DataArray([]))
        plotter2 = ThisTestPlotter2(xr.DataArray([]))

        # plotter1
        self.assertEqual(plotter1.fmt1.value, 'test1okay')
        self.assertEqual(plotter1.fmt2.value, 'test2okay')
        self.assertEqual(plotter1.fmt3.value, 'test3okay')
        # plotter2
        self.assertEqual(plotter2.fmt1.value, 'test1okay')
        self.assertEqual(plotter2.fmt2.value, 'test2okay')
        self.assertEqual(plotter2.fmt3.value, 'test3.2okay')

    def test_fmt_connections(self):
        """Test the order of the updates"""
        plotter = TestPlotter(xr.DataArray([]),
                              fmt1='test', fmt2='test2', fmt3='test3')
        plotter.data.psy.arr_name = 'data'

        # check the initialization order
        self.assertEqual(list(results.keys()),
                         ['data.fmt3', 'data.fmt2', 'data.fmt1'])

        # check the connection properties
        self.assertIs(plotter.fmt1.fmt2, plotter.fmt2)
        self.assertIs(plotter.fmt1.fmt3, plotter.fmt3)
        self.assertIs(plotter.fmt2.fmt3, plotter.fmt3)

        # check the update
        results.clear()
        plotter.update(fmt2='something', fmt3='else')
        self.assertEqual(list(results.keys()),
                         ['data.fmt3', 'data.fmt2', 'data.fmt1'])
        self.assertEqual(plotter.fmt1.value, 'test')
        self.assertEqual(plotter.fmt2.value, 'something')
        self.assertEqual(plotter.fmt3.value, 'else')

        self.assertEqual(list(plotter._sorted_by_priority(
                             [plotter.fmt1, plotter.fmt2, plotter.fmt3])),
                         [plotter.fmt3, plotter.fmt2, plotter.fmt1])
        if six.PY3:
            with self.assertRaisesRegex(
                    TypeError, "got an unexpected keyword argument 'wrong'"):
                SimpleFmt('fmt1', wrong='something')

    def test_data_props_array(self):
        """Test the data properties of Formatoptions with a DataArray"""
        data = xr.DataArray([])
        plot_data = data.copy(True)
        plotter = TestPlotter(data)
        plotter.plot_data = plot_data

        self.assertIs(plotter.fmt1.raw_data, data)
        self.assertIs(plotter.fmt1.data, plot_data)

    def test_data_props_list(self):
        """Test the data properties of Formatoptions with an InteractiveList"""
        data = psyd.InteractiveList([xr.DataArray([]), xr.DataArray([])])
        plot_data = data.copy(True)
        plot_data.extend([xr.DataArray([]), xr.DataArray([])],
                         new_name=True)
        plotter = TestPlotter(data)
        plotter.plot_data = plot_data
        plot_data = plotter.plot_data  # the data might have been copied

        self.assertIs(plotter.fmt1.raw_data, data)
        self.assertIs(plotter.fmt1.data, plot_data)

        # test with index in list
        plotter.fmt1.index_in_list = 1
        self.assertIs(plotter.fmt1.raw_data, data[1])
        self.assertIs(plotter.fmt1.data, plot_data[1])

        # test with index in list of plot_data outside raw_data
        plotter.fmt1.index_in_list = 3
        self.assertIs(plotter.fmt1.data, plot_data[3])

    def test_decoder(self):
        """Test the decoder property of Formatoptions with a DataArray"""
        data = xr.DataArray([])
        data.psy.init_accessor(decoder=psyd.CFDecoder(data.psy.base))
        plot_data = data.copy(True)
        plotter = TestPlotter(data)
        plotter.plot_data = plot_data

        self.assertIsInstance(plotter.fmt1.decoder, psyd.CFDecoder)
        self.assertIs(plotter.fmt1.decoder, data.psy.decoder)

        # test with index in list of plot_data outside raw_data
        plotter.plot_data_decoder = decoder = psyd.CFDecoder(data.psy.base)
        self.assertIsInstance(plotter.fmt1.decoder, psyd.CFDecoder)
        self.assertIs(plotter.fmt1.decoder, decoder)

    def test_decoder_list(self):
        """Test the decoder property with an InteractiveList"""
        data = psyd.InteractiveList([xr.DataArray([]), xr.DataArray([])])
        plot_data = data.copy(True)
        plot_data.extend([xr.DataArray([]), xr.DataArray([])],
                         new_name=True)
        for arr in data:
            arr.psy.init_accessor(decoder=psyd.CFDecoder(arr.psy.base))
        plotter = TestPlotter(data)
        plotter.plot_data = plot_data
        plot_data = plotter.plot_data  # the data might have been copied

        self.assertIsInstance(plotter.fmt1.decoder, psyd.CFDecoder)
        self.assertIs(plotter.fmt1.decoder, data[0].psy.decoder)

        # test with index in list
        plotter.fmt1.index_in_list = 1
        self.assertIsInstance(plotter.fmt1.decoder, psyd.CFDecoder)
        self.assertIs(plotter.fmt1.decoder, data[1].psy.decoder)

        # test without index in list
        decoder = psyd.CFDecoder(data[0].psy.base)
        plotter.fmt2.decoder = decoder
        for i, d2 in enumerate(plotter.plot_data_decoder):
            self.assertIs(d2, decoder,
                          msg='Decoder %i has been set wrong!' % i)
        self.assertEqual(plotter.fmt2.decoder, plotter.plot_data_decoder)

        # test with index in list of plot_data outside raw_data
        plotter.fmt1.index_in_list = 3
        decoder2 = psyd.CFDecoder(data[0].psy.base)
        plotter.fmt1.decoder = decoder2
        for i, d2 in enumerate(plotter.plot_data_decoder):
            self.assertIs(d2, decoder if i != 3 else decoder2,
                          msg='Decoder %i has been set wrong!' % i)
        self.assertIsInstance(plotter.fmt1.decoder, psyd.CFDecoder)
        self.assertIs(plotter.fmt1.decoder, plotter.plot_data_decoder[3])

    def test_any_decoder(self):
        """Test the decoder property with an InteractiveList"""
        data = psyd.InteractiveList([xr.DataArray([]), xr.DataArray([])])
        plot_data = data.copy(True)
        plot_data.extend([xr.DataArray([]), xr.DataArray([])],
                         new_name=True)
        for arr in data:
            arr.psy.init_accessor(decoder=psyd.CFDecoder(arr.psy.base))
        plotter = TestPlotter(data)
        plotter.plot_data = plot_data
        plot_data = plotter.plot_data  # the data might have been copied

        # test without index in list
        decoder = psyd.CFDecoder(data[0].psy.base)
        plotter.fmt2.decoder = decoder
        for i, d2 in enumerate(plotter.plot_data_decoder):
            self.assertIs(d2, decoder,
                          msg='Decoder %i has been set wrong!' % i)
        self.assertEqual(plotter.fmt2.decoder, plotter.plot_data_decoder)
        self.assertIs(plotter.fmt2.any_decoder, decoder)

    def test_get_enhanced_attrs_01_arr(self):
        """Test the :meth:`psyplot.plotter.Plotter.get_enhanced_attrs` method
        """
        ds = psyd.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        plotter = TestPlotter(ds.t2m)
        attrs = ds.t2m.attrs.copy()
        for key, val in ds.lon.attrs.items():
            attrs['x' + key] = val
        for key, val in ds.lat.attrs.items():
            attrs['y' + key] = val
        for key, val in ds.lev.attrs.items():
            attrs['z' + key] = val
        for key, val in ds.time.attrs.items():
            attrs['t' + key] = val
        attrs['xname'] = 'lon'
        attrs['yname'] = 'lat'
        attrs['zname'] = 'lev'
        attrs['tname'] = 'time'
        attrs['name'] = 't2m'
        self.assertEqual(dict(plotter.get_enhanced_attrs(plotter.plot_data)),
                         dict(attrs))

    def test_get_enhanced_attrs_02_list(self):
        """Test the :meth:`psyplot.plotter.Plotter.get_enhanced_attrs` method
        """
        ds = psyd.open_dataset(bt.get_file('test-t2m-u-v.nc'))
        plotter = TestPlotter(psyd.InteractiveList(
            ds.psy.create_list(name=['t2m', 'u'], x=0, t=0)))
        attrs = {}
        for key, val in ds.t2m.attrs.items():
            attrs['t2m' + key] = val
        for key, val in ds.u.attrs.items():
            attrs['u' + key] = val
        for key, val in ds.lon.attrs.items():
            attrs['x' + key] = val
        for key, val in ds.lat.attrs.items():
            attrs['y' + key] = val
            attrs['x' + key] = val  # overwrite the longitude information
        # the plot_data has priority over the base variable, therefore we
        # the plotter should replace the y information with the z information
        for key, val in ds.lev.attrs.items():
            attrs['z' + key] = val
            attrs['y' + key] = val  # overwrite the latitude information
        for key, val in ds.time.attrs.items():
            attrs['t' + key] = val
        for key in set(ds.t2m.attrs) & set(ds.u.attrs):
            if ds.t2m.attrs[key] == ds.u.attrs[key]:
                attrs[key] = ds.t2m.attrs[key]
        attrs['zname'] = attrs['yname'] = 'lev'
        attrs['xname'] = 'lat'
        attrs['tname'] = 'time'
        attrs['lon'] = attrs['x'] = ds.lon.values[0]
        attrs['time'] = attrs['t'] = pd.to_datetime(
            ds.time.values[0]).isoformat()
        self.maxDiff = None
        self.assertEqual(dict(plotter.get_enhanced_attrs(plotter.plot_data)),
                         dict(attrs))

    def test_show_keys(self):
        """Test the :meth:`psyplot.plotter.Plotter.show_keys` method"""
        plotter = TestPlotter(xr.DataArray([]))
        s = plotter.show_keys(['fmt1', 'fmt2', 'fmt3'], func=str)
        self.assertEqual(s,
                         '+------+------+------+\n'
                         '| fmt1 | fmt2 | fmt3 |\n'
                         '+------+------+------+')
        s = plotter.show_keys(['fmt1', 'fmt2', 'fmt3'], func=str, grouped=True)
        title = psyp.groups['labels']
        self.assertEqual(s,
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
        s = plotter.show_keys(['fmt1', 'something'], func=str)
        self.assertEqual(s,
                         '+------+------+\n'
                         '| fmt1 | fmt3 |\n'
                         '+------+------+')
        if six.PY3:
            with self.assertWarnsRegex(UserWarning,
                                       '(?i)unknown formatoption keyword'):
                s = plotter.show_keys(['fmt1', 'wrong', 'something'], func=str)
                self.assertEqual(s,
                                 '+------+------+\n'
                                 '| fmt1 | fmt3 |\n'
                                 '+------+------+')

    def test_show_docs(self):
        """Test the :meth:`psyplot.plotter.Plotter.show_docs` method"""
        plotter = TestPlotter(xr.DataArray([]))
        s = plotter.show_docs(func=str)
        self.maxDiff = None
        self.assertEqual(s, '\n'.join([
            'fmt1', '====', SimpleFmt.__doc__, '',
            'fmt2', '====', SimpleFmt2.__doc__, '',
            'fmt3', '====', SimpleFmt3.__doc__, '',
            'post', '====', psyp.PostProcessing.__doc__, '',
            'post_timing', '===========', psyp.PostTiming.__doc__, '']))
        s = plotter.show_docs(['fmt1', 'fmt2', 'fmt3'], func=str, grouped=True)
        title = psyp.groups['labels']
        self.assertEqual(s, '\n'.join([
            '*' * len(title),
            title,
            '*' * len(title),
            'fmt1', '====', SimpleFmt.__doc__, '',
            'fmt2', '====', SimpleFmt2.__doc__, '', '',
            '*********',
            'something',
            '*********',
            'fmt3', '====', SimpleFmt3.__doc__]))

    def test_show_summaries(self):
        """Test the :meth:`psyplot.plotter.Plotter.show_summaries` method"""
        plotter = TestPlotter(xr.DataArray([]))
        s = plotter.show_summaries(func=str)
        self.assertEqual(s, '\n'.join([
            'fmt1', indent(SimpleFmt.__doc__.splitlines()[0], '    '),
            'fmt2', indent(SimpleFmt2.__doc__.splitlines()[0], '    '),
            'fmt3', indent(SimpleFmt3.__doc__.splitlines()[0], '    '),
            'post', indent(psyp.PostProcessing.__doc__.splitlines()[0], 
                           '    '),
            'post_timing', indent(psyp.PostTiming.__doc__.splitlines()[0], 
                                  '    ')]))
        s = plotter.show_summaries(['fmt1', 'fmt2', 'fmt3'], func=str, 
                                   grouped=True)
        title = psyp.groups['labels']
        self.assertEqual(s, '\n'.join([
            '*' * len(title),
            title,
            '*' * len(title),
            'fmt1', indent(SimpleFmt.__doc__.splitlines()[0], '    '),
            'fmt2', indent(SimpleFmt2.__doc__.splitlines()[0], '    '), '',
            '*********',
            'something',
            '*********',
            'fmt3', indent(SimpleFmt3.__doc__.splitlines()[0], '    ')]
            ))

    def test_has_changed(self):
        """Test the :meth:`psyplot.plotter.Plotter.show_summaries` method"""
        plotter = TestPlotter(xr.DataArray([]), fmt1='something')
        self.assertEqual(plotter['fmt1'], 'something')
        for i in range(1, 4):
            key = 'fmt%i' % i
            fmto = getattr(plotter, key)
            self.assertEqual(plotter.has_changed(key),
                             [fmto.default, plotter[key]],
                             msg="Wrong value for " + key)
        plotter.update()
        self.assertIsNone(plotter.has_changed('fmt1'))
        plotter.update(fmt1='test', fmt3=plotter.fmt3.default, force=True)
        self.assertEqual(plotter.has_changed('fmt1'),
                         ['something', 'test'])
        self.assertIsNone(plotter.has_changed('fmt2'))
        self.assertIsNone(plotter.has_changed('fmt3', include_last=False))
        self.assertEqual(plotter.has_changed('fmt3'),
                         [plotter.fmt3.default, plotter.fmt3.default])

    def test_insert_additionals(self):
        """Test whether the right formatoptions are inserted"""
        depend = 0

        class StartFormatoption(TestFormatoption):
            priority = psyp.START

        class BeforePlottingFmt(TestFormatoption):
            priority = psyp.BEFOREPLOTTING

        class PlotFmt(TestFormatoption):
            priority = psyp.BEFOREPLOTTING
            plot_fmt = True

            def make_plot(self):
                results['plot_made'] = True

        class DataDependentFmt(TestFormatoption):
            priority = psyp.START

            def data_dependent(self, *args, **kwargs):
                return bool(depend)

        class DataDependentFmt2(TestFormatoption):
            data_dependent = True

        class ThisTestPlotter(TestPlotter):
            fmt_start = StartFormatoption('fmt_start')
            fmt_plot = PlotFmt('fmt_plot')
            fmt_plot1 = BeforePlottingFmt('fmt_plot1')
            fmt_plot2 = BeforePlottingFmt('fmt_plot2')
            fmt_data1 = DataDependentFmt('fmt_data1')
            fmt_data2 = DataDependentFmt2('fmt_data2')

        def key_name(key):
            return "%s.%s" % (aname, key)

        plotter = ThisTestPlotter(xr.DataArray([]))
        for key in set(plotter) - {'post', 'post_timing'}:
            plotter[key] = 999
        aname = plotter.data.psy.arr_name
        results.clear()

        # test whether everything is updated
        plotter.update(fmt_start=1)
        self.assertTrue(results.pop('plot_made'))
        self.assertEqual(list(results),
                         [key_name('fmt_start'), key_name('fmt_plot'),
                          key_name('fmt_data2')])

        results.clear()

        # test whether the plot is updated
        plotter.update(fmt_plot1=1)
        self.assertEqual(list(results), [key_name('fmt_plot1'), 'plot_made'])

        results.clear()

        # test whether the data dependent formatoptions are updated
        plotter.update(replot=True)
        self.assertTrue(results.pop('plot_made'))
        self.assertEqual(list(results),
                         [key_name('fmt_plot'), key_name('fmt_data2')])

        results.clear()
        depend = 1
        plotter.update(replot=True)
        self.assertTrue(results.pop('plot_made'))
        self.assertEqual(sorted(list(results)),
                         sorted([key_name('fmt_plot'), key_name('fmt_data1'),
                                 key_name('fmt_data2')]))

    def test_reinit(self):
        """Test the reinitialization of a plotter"""
        class ClearingFormatoption(SimpleFmt):

            def remove(self):
                results['removed'] = True

            requires_clearing = True

        class AnotherFormatoption(SimpleFmt):

            def remove(self):
                results['removed2'] = True

        class ThisTestPlotter(TestPlotter):
            fmt_clear = ClearingFormatoption('fmt_clear')
            fmt_remove = AnotherFormatoption('fmt_remove')
        import matplotlib.pyplot as plt
        ax = plt.axes()
        ax.plot([6, 7])

        plotter = ThisTestPlotter()
        keys = list(set(plotter) - {'post', 'post_timing'})
        plotter = ThisTestPlotter(xr.DataArray([]), ax=ax,
                                  **dict(zip(keys, repeat(1))))

        self.assertNotIn('removed', results)
        self.assertNotIn('removed2', results)
        arr_name = plotter.data.psy.arr_name
        for key in keys:
            self.assertIn("%s.%s" % (arr_name, key), results)
        self.assertTrue(ax.lines)  # axes should not be cleared

        results.clear()

        plotter.reinit()
        self.assertIn('removed', results)
        self.assertIn('removed2', results)
        for key in keys:
            self.assertIn("%s.%s" % (arr_name, key), results)
        self.assertFalse(ax.lines)  # axes should be cleared

        results.clear()

        ax.plot([6, 7])
        keys.remove('fmt_clear')
        keys.remove('fmt_remove')
        plotter = TestPlotter(xr.DataArray([]), ax=ax,
                              **dict(zip(keys, repeat(1))))
        for key in keys:
            self.assertIn("%s.%s" % (arr_name, key), results)
        self.assertTrue(ax.lines)  # axes should not be cleared

        results.clear()

        plotter.reinit()
        for key in keys:
            self.assertIn("%s.%s" % (arr_name, key), results)
        self.assertTrue(ax.lines)  # axes should not be cleared

    def test_check_data(self):
        """Tests the :meth:`psyplot.plotter.Plotter.check_data` method"""
        self.assertEqual(TestPlotter.check_data('test', ('dim1', ), True),
                         ([True], ['']))
        checks, messages = TestPlotter.check_data(
            ['test1', 'test2'], [('dim1', )], [False, False])
        self.assertEqual(checks, [False, False])
        self.assertIn('not the same', messages[0])
        self.assertIn('not the same', messages[1])


class FormatoptionTest(unittest.TestCase):
    """A class to test the :class:`psyplot.plotter.Formatoption` class
    """

    def setUp(self):
        results.clear()
        rcParams.defaultParams = rcParams.defaultParams.copy()

    def tearDown(self):
        results.clear()
        rcParams.clear()
        rcParams.defaultParams = psyc.rcsetup.defaultParams
        rcParams.update_from_defaultParams()

    def test_data(self):
        """Test the :attr:`psyplot.plotter.Formatoption.data` attribute"""
        class OtherTestPlotter(TestPlotter):
            fmt4 = SimpleFmt3('fmt4', index_in_list=2)

        raw_data = psyd.InteractiveList([xr.DataArray([]) for _ in range(4)])
        plotter = OtherTestPlotter(raw_data)
        plotter.plot_data = plot_data = plotter.data.copy(True)
        copied = plotter.plot_data[2].copy()
        # -- test the getters
        self.assertIs(plotter.fmt1.data, plotter.plot_data)
        self.assertIsNot(plotter.fmt1.data, plotter.data)
        self.assertIs(plotter.fmt1.raw_data, plotter.data)
        self.assertIsNot(plotter.fmt1.raw_data, plotter.plot_data)
        # -- test the setters
        plotter.fmt4.data = copied
        self.assertIs(plotter.plot_data[2], copied)
        self.assertIsNot(plotter.data[2], copied)
        self.assertIs(plotter.plot_data[1], plot_data[1])

        plotter.fmt3.data = raw_data
        for i, arr in enumerate(plotter.plot_data):
            self.assertIs(arr, raw_data[i],
                          msg='Wrong array at position %i' % i)
        # undo the setting
        plotter.fmt3.data = plot_data

        # -- test iteration over data
        # plot data
        it_data = plotter.fmt3.iter_data
        for i, arr in enumerate(plotter.fmt3.data):
            self.assertIs(next(it_data), arr,
                          msg='Wrong array at position %i' % i)
        # raw data
        it_data = plotter.fmt3.iter_raw_data
        for i, arr in enumerate(plotter.fmt3.raw_data):
            self.assertIs(next(it_data), arr,
                          msg='Wrong raw data array at position %i' % i)
        self.assertIs(next(plotter.fmt4.iter_data), plot_data[2])
        self.assertIs(next(plotter.fmt4.iter_raw_data), raw_data[2])

    def test_rc(self):
        """Test whether the rcParams are interpreted correctly"""
        checks = []

        def validate(val):
            checks.append(val)
            return val

        def validate_false(val):
            if val == 4:
                raise ValueError("Expected ValueError")
            return val

        try:
            class RcTestPlotter(TestPlotter):
                _rcparams_string = ['plotter.test.data.']
            # delete the validation
            del TestFormatoption._validate
            rcParams.defaultParams['plotter.test.data.fmt1'] = (1, validate)
            rcParams.defaultParams['plotter.test.data.fmt3'] = (
                3, validate_false)
            rcParams.update_from_defaultParams()
            plotter = RcTestPlotter(xr.DataArray([]))

            self.assertEqual(checks, [1],
                             msg='Validation function has not been called!')
            # test general functionality
            self.assertEqual(plotter.fmt1.default_key,
                             'plotter.test.data.fmt1')
            self.assertEqual(plotter.fmt3.default_key,
                             'plotter.test.data.fmt3')
            if six.PY3:
                with self.assertRaisesRegex(KeyError, 'fmt2'):
                    plotter.fmt2.default_key
            self.assertEqual(plotter['fmt1'], 1)
            self.assertEqual(plotter.fmt1.default, 1)
            self.assertFalse(plotter.fmt2.value)
            self.assertIs(plotter.fmt1.validate, validate)
            # test after update
            plotter.update(fmt1=8)
            self.assertEqual(checks, [1, 8],
                             msg='Validation function has not been called!')
            self.assertEqual(plotter.fmt1.value, 8)
            self.assertEqual(plotter['fmt1'], 8)
            self.assertEqual(plotter.fmt1.default, 1)
            # test false validation
            if six.PY3:
                with self.assertWarnsRegex(RuntimeWarning,
                                           "Could not find a validation "
                                           "function"):
                    plotter.fmt2.validate
                with self.assertRaisesRegex(ValueError, 'Expected ValueError'):
                    plotter.update(fmt3=4)
                plotter.update(fmt3=3)
            plotter.fmt2.validate = validate
            plotter.update(fmt2=9)
            self.assertEqual(checks, [1, 8, 9])
            self.assertEqual(plotter.fmt2.value, 9)
        except:
            raise
        finally:
            TestFormatoption._validate = str

    def test_groupname(self):
        if not six.PY2:
            with self.assertWarnsRegex(RuntimeWarning,
                                       'Unknown formatoption group'):
                self.assertEqual(TestPlotter.fmt3.groupname, 'something')
        self.assertEqual(TestPlotter.fmt1.groupname,
                         psyp.groups['labels'])


class TestDictFormatoption(unittest.TestCase):
    """Test the :class:`psyplot.plotter.DictFormatoption` class"""

    def test_update(self):
        class TestDictFormatoption(psyp.DictFormatoption):

            @property
            def default(self):
                try:
                    return super(TestDictFormatoption, self).default
                except KeyError:
                    return {}

            _validate = psyp._identity

            def update(self, value):
                pass

        class ThisTestPlotter(TestPlotter):

            fmt4 = TestDictFormatoption('fmt4')

        plotter = ThisTestPlotter(xr.DataArray([]))

        self.assertEqual(plotter.fmt4.value, {})
        # perform 2 updates which each should be considered
        plotter.update(fmt4=dict(a=1))
        plotter.update(fmt4=dict(b=2))
        self.assertEqual(plotter.fmt4.value, dict(a=1, b=2))

        # update to default
        plotter.update(fmt4=dict(a=3), todefault=True)
        self.assertEqual(plotter.fmt4.value, dict(a=3))

        # clear the value
        plotter.update(fmt4=None)
        self.assertEqual(plotter.fmt4.value, {})

if __name__ == '__main__':
    unittest.main()
