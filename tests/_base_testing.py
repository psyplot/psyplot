"""Base testing module."""

# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht

# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: LGPL-3.0-only

import os
import os.path as osp
import subprocess as spr
import sys

test_dir = osp.dirname(__file__)


os.environ["PSYPLOT_PLUGINS"] = "yes:psyplot_test.plugin"


def get_file(fname):
    """Get the full path to the given file name in the test directory"""
    return osp.join(test_dir, fname)


# check if the seaborn version is smaller than 0.8 (without actually importing
# it), due to https://github.com/mwaskom/seaborn/issues/966
# If so, disable the import of it when import psyplot.project
try:
    sns_version = spr.check_output(
        [sys.executable, "-c", "import seaborn; print(seaborn.__version__)"]
    )
except spr.CalledProcessError:  # seaborn is not installed
    pass
else:
    if sns_version.decode("utf-8") < "0.8":
        import psyplot

        psyplot.rcParams["project.import_seaborn"] = False
