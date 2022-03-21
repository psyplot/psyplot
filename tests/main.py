#!/usr/bin/env python
"""Script to run all tests from the psyplot package

This script may be used from the command line run all tests from the psyplot
package. See::

    python main.py -h

for details. You can also use the py.test module (which however leads to a
failure of some tests in python 3.4)
"""

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
import os

import unittest

test_suite = unittest.defaultTestLoader.discover(bt.test_dir)


if __name__ == '__main__':
    test_runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    test_runner.run(test_suite)
