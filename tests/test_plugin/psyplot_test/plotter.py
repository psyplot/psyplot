# Test module that defines a plotter
#
# The plotter in this module has been registered by the rcParams in the plugin
# package

# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht

# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: LGPL-3.0-only

from psyplot.plotter import Formatoption, Plotter


class TestFmt(Formatoption):
    """Some documentation"""

    default = None

    def update(self, value):
        pass


class TestPlotter(Plotter):
    fmt1 = TestFmt("fmt1")
