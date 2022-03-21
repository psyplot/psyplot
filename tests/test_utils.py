"""Module for testing the :mod:`psyplot.utils` module."""

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
import unittest
import psyplot.utils as utils


class TestTempBool(unittest.TestCase):
    """Test the :class:`psyplot.utils._TempBool` class"""

    def test_descriptor(self):
        """Test the descriptor functionality"""

        class Test(object):

            test = utils._temp_bool_prop('test')

        t = Test()

        self.assertFalse(t.test)
        with t.test:
            self.assertTrue(t.test)

        t.test = True
        self.assertTrue(t.test)
        with t.test:
            self.assertTrue(t.test)

        del t.test
        self.assertFalse(t.test)


class TestUniqueEverSeen(unittest.TestCase):
    """Test the :func:`psyplot.utils.unique_everseen` function"""

    def test_simple(self):
        self.assertEqual(list(utils.unique_everseen([1, 1, 2, 3, 4, 3])),
                         [1, 2, 3, 4])

    def test_key(self):
        self.assertEqual(list(utils.unique_everseen([1, 1, 2, 3, 4, 3],
                                                    key=lambda i: i % 3)),
                         [1, 2, 3])
