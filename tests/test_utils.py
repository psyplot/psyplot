"""Module for testing the :mod:`psyplot.utils` module."""

# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht

# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: LGPL-3.0-only

import unittest

import psyplot.utils as utils


class TestTempBool(unittest.TestCase):
    """Test the :class:`psyplot.utils._TempBool` class"""

    def test_descriptor(self):
        """Test the descriptor functionality"""

        class Test(object):
            test = utils._temp_bool_prop("test")

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
        self.assertEqual(
            list(utils.unique_everseen([1, 1, 2, 3, 4, 3])), [1, 2, 3, 4]
        )

    def test_key(self):
        self.assertEqual(
            list(
                utils.unique_everseen([1, 1, 2, 3, 4, 3], key=lambda i: i % 3)
            ),
            [1, 2, 3],
        )
