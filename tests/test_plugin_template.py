"""Test script for the psyplot.plugin_template module."""

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
