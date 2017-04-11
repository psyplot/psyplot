"""Test script for the psyplot.plugin_template module
"""
import _base_testing as bt
import os.path as osp
import unittest
import tempfile
import psyplot.plugin_template as pp


class TestPluginTemplate(unittest.TestCase):
    """Test case for the psyplot.plugin_template module"""

    def test_main(self):
        tempdir = tempfile.mkdtemp()
        target = osp.join(tempdir, 'test-plugin')
        pp.main([target])
        self.assertTrue(osp.exists(target), msg=target + ' is missing!')
        setup_script = osp.join(target, 'setup.py')
        self.assertTrue(osp.exists(setup_script),
                        msg=setup_script + ' is missing!')
        plugin_file = osp.join(target, 'test_plugin', 'plugin.py')
        self.assertTrue(osp.exists(plugin_file),
                        msg=plugin_file + ' is missing!')
