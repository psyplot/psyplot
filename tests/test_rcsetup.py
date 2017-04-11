"""Test module of the basic functionality in the :mod:`psyplot.plotter` module
"""
import _base_testing as bt
import os.path as osp
import unittest
import six
import psyplot
from psyplot.config.rcsetup import SubDict, RcParams, rcParams


class SubDictTest(unittest.TestCase):

    def test_basic(self):
        """Test the basic functionality
        """
        d = {'test.1': 'test1', 'test.2': 'test2',
             'test1.1': 'test11', 'test1.2': 'test12'}
        sub = SubDict(d, 'test.', pattern_base='test\.')
        self.assertIn('1', sub)
        self.assertIn('2', sub)
        self.assertEqual(sub['1'], 'test1')
        self.assertEqual(sub['2'], 'test2')
        self.assertNotIn('test11', sub.values(),
                         msg='Item test1.1 catched in %s' % (sub, ))
        self.assertNotIn('test12', sub.values(),
                         msg='Item test1.2 catched in %s' % (sub, ))

    def test_replace(self):
        """Test the replace property
        """
        d = {'test.1': 'test1', 'test.2': 'test2',
             'test1.1': 'test11', 'test1.2': 'test12'}
        sub = SubDict(d, 'test.', pattern_base='test\.')
        sub['test'] = 5  # test something that is not traced back to d
        self.assertNotIn('test.1', sub)
        self.assertIn('1', sub)
        sub.replace = False
        sub.trace = True
        sub['test.2'] = 4
        self.assertIn('test.1', sub)
        self.assertNotIn('1', sub)
        self.assertEqual(sub['test.2'], 4)
        self.assertEqual(d['test.2'], 4)
        sub.replace = True
        self.assertNotIn('test.1', sub)
        self.assertIn('1', sub)

    def test_trace(self):
        """Test the backtracing to the origin dictionary"""
        d = {'test.1': 'test1', 'test.2': 'test2',
             'test1.1': 'test11', 'test1.2': 'test12'}
        sub = SubDict(d, 'test.', pattern_base='test\.', trace=True)
        self.assertIn('1', sub)
        sub['1'] = 'change in d'
        sub['test.3'] = 'test3'  # new item
        self.assertEqual(d['test.1'], 'change in d')
        self.assertEqual(sub['1'], 'change in d')
        self.assertIn('3', sub)
        self.assertIn('test.3', d)

        sub.trace = False
        sub['1'] = 'do not change in d'
        sub['4'] = 'test4'
        self.assertEqual(d['test.1'], 'change in d')
        self.assertEqual(sub['1'], 'do not change in d')
        self.assertIn('4', sub)
        self.assertNotIn('4', d)


class RcParamsTest(unittest.TestCase):
    """Test the functionality of RcParams"""

    @unittest.skipIf(six.PY2, "Missing necessary unittest methods")
    def test_dump(self):
        """Test the dumping of the rcParams"""
        rc = RcParams(defaultParams={
            'some.test': [1, lambda i: int(i), 'The documentation'],
            'some.other_test': [2, lambda i: int(i), 'Another documentation']})
        rc.update_from_defaultParams()

        rc.HEADER = 'the header'
        s = rc.dump(default_flow_style=False)
        self.assertIn('the header', s)
        self.assertRegex(s, r'# The documentation\n\s*some.test')
        self.assertRegex(s, r'# Another documentation\n\s*some.other_test')

    @unittest.skipIf(six.PY2, 'Method not available on Python2')
    def test_error(self):
        """Test whether the correct Error is raised"""
        def validate(i):
            try:
                return int(i)
            except:
                raise ValueError("Expected failure")
        rc = RcParams(defaultParams={
            'some.test': [1, validate, 'The documentation'],
            'some.other_test': [2, validate, 'Another documentation']})
        rc.update_from_defaultParams()
        with self.assertRaisesRegex(ValueError, "Expected failure"):
            rc['some.test'] = 'test'
        with self.assertRaises(KeyError):
            rc['wrong_key'] = 1
        rc._deprecated_map['something'] = ['some.test', lambda x: x]
        with self.assertWarnsRegex(UserWarning, rc.msg_depr % ('something',
                                                               'some.test')):
            rc['something'] = 3
        # check whether the value has been changed correctly
        self.assertEqual(rc['some.test'], 3)
        rc._deprecated_ignore_map['ignored'] = 'some.test'
        with self.assertWarnsRegex(UserWarning, rc.msg_depr_ignore % (
                'ignored', 'some.test')):
            rc['ignored'] = None
        # check whether the value has not been changed
        self.assertEqual(rc['some.test'], 3)

    def test_findall(self):
        rc = RcParams(defaultParams={
            'some.test': [1, lambda i: int(i), 'The documentation'],
            'some.other_test': [2, lambda i: int(i), 'Another documentation']})
        rc.update_from_defaultParams()
        self.assertEqual(rc.find_all('other'), {'some.other_test': 2})

    @unittest.skipIf(six.PY2, "Missing necessary unittest methods")
    def test_plugin(self):
        """Test whether the plugin interface works"""

        try:
            from psyplot_test.plugin import rcParams as test_rc
        except ImportError:
            self.skipTest("Could not import the psyplot_test package")
            return
        rc = psyplot.rcParams.copy()
        rc.load_plugins()
        self.assertIn('test', rc)
        self.assertEqual(rc['test'], 1)
        with self.assertRaisesRegex(
                ImportError, "plotters have already been defined"):
            rc.load_plugins(True)
        plotters = test_rc.pop('project.plotters')
        try:
            with self.assertRaisesRegex(
                    ImportError, "default keys have already been defined"):
                rc.load_plugins(True)
        except:
            raise
        finally:
            test_rc['project.plotters'] = plotters

    def test_connect(self):
        """Test the connection and disconnection to rcParams"""
        x = set()
        y = set()

        def update_x(val):
            x.update(val)

        def update_y(val):
            y.update(val)

        rcParams.connect('decoder.x', update_x)
        rcParams.connect('decoder.y', update_y)

        rcParams['decoder.x'] = {'test'}
        self.assertEqual(x, {'test'})
        self.assertEqual(y, set())

        rcParams['decoder.y'] = {'test2'}
        self.assertEqual(y, {'test2'})

        rcParams.disconnect('decoder.x', update_x)
        rcParams['decoder.x'] = {'test3'}
        self.assertEqual(x, {'test'})

        rcParams.disconnect()
        rcParams['decoder.y'] = {'test4'}
        self.assertEqual(y, {'test2'})


if __name__ == '__main__':
    unittest.main()
