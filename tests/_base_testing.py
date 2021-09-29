"""Base testing module."""

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

import os
import sys
import os.path as osp
import subprocess as spr

test_dir = osp.dirname(__file__)


os.environ['PSYPLOT_PLUGINS'] = 'yes:psyplot_test.plugin'


def get_file(fname):
    """Get the full path to the given file name in the test directory"""
    return osp.join(test_dir, fname)

# check if the seaborn version is smaller than 0.8 (without actually importing
# it), due to https://github.com/mwaskom/seaborn/issues/966
# If so, disable the import of it when import psyplot.project
try:
    sns_version = spr.check_output(
        [sys.executable, '-c', 'import seaborn; print(seaborn.__version__)'])
except spr.CalledProcessError:  # seaborn is not installed
    pass
else:
    if sns_version.decode('utf-8') < '0.8':
        import psyplot
        psyplot.rcParams['project.import_seaborn'] = False
