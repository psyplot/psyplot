#!/bin/bash
# script to automatically generate the psyplot api documentation using
# sphinx-apidoc and sed

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

sphinx-apidoc -f -M -e  -T -o api ../psyplot/
# replace chapter title in psyplot.rst
sed -i -e 1,1s/.*/'API Reference'/ api/psyplot.rst
# add imported members at the top level module
sed -i -e /Subpackages/'i\'$'\n'".. autosummary:: \\
\    ~psyplot.config.rcsetup.rcParams \\
\    ~psyplot.data.InteractiveArray \\
\    ~psyplot.data.InteractiveList \\
    \\
    " api/psyplot.rst

sphinx-autogen -o generated *.rst */*.rst

