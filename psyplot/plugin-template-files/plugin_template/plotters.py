"""plotters module of the PLUGIN_NAME psyplot plugin

This module defines the plotters for the PLUGIN_NAME package. It should import
all requirements and define the formatoptions and plotters that are specified
in the :mod:`PLUGIN_PYNAME.plugin` module.
"""

# Disclaimer
# ----------
#
# Copyright (C) YOUR-INSTITUTION
#
# This file is part of PLUGIN_NAME and is released under the GNU LGPL-3.O license.
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

from psyplot.plotter import Formatoption, Plotter


# -----------------------------------------------------------------------------
# ---------------------------- Formatoptions ----------------------------------
# -----------------------------------------------------------------------------


class MyNewFormatoption(Formatoption):

    def update(self, value):
        # hooray
        pass


# -----------------------------------------------------------------------------
# ------------------------------ Plotters -------------------------------------
# -----------------------------------------------------------------------------


class MyPlotter(Plotter):

    _rcparams_string = ['plotter.PLUGIN_PYNAME.']

    my_fmt = MyNewFormatoption('my_fmt')
