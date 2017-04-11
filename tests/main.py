#!/usr/bin/env python
"""Script to run all tests from the psyplot package

This script may be used from the command line run all tests from the psyplot
package. See::

    python main.py -h

for details. You can also use the py.test module (which however leads to a
failure of some tests in python 3.4)
"""

import _base_testing as bt
import os

import unittest

test_suite = unittest.defaultTestLoader.discover(bt.test_dir)


if __name__ == '__main__':
    test_runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    test_runner.run(test_suite)
