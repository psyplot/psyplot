"""Dummy plugin file."""

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

from psyplot.config.rcsetup import RcParams, validate_dict


plugin_version = '1.0.0'


rcParams = RcParams(defaultParams={
    'test': [1, lambda i: int(i)],
    'project.plotters': [
        {'test_plotter': {
            'module': 'psyplot_test.plotter',
            'plotter_name': 'TestPlotter', 'import_plotter': True}},
        validate_dict]})
rcParams.update_from_defaultParams()


patch_check = []

checking_patch = False


def test_patch(plotter_d, versions):
    if not checking_patch:
        raise ValueError("Accidently applied the patch!")
    patch_check.append({'plotter': plotter_d, 'versions': versions})


patches = {('psyplot_test.plotter', 'TestPlotter'): test_patch}
