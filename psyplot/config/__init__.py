"""Configuration module of the psyplot package

This module contains the module for managing rc parameters and the logging.
Default parameters are defined in the :data:`rcsetup.defaultParams`
dictionary, however you can set up your own configuration in a yaml file (see
:func:`psyplot.load_rc_from_file`)"""

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

from .logsetup import setup_logging

#: :class:`str`. Path to the yaml logging configuration file
logcfg_path = setup_logging()


from .rcsetup import psyplot_fname


#: class:`str` or ``None``. Path to the yaml configuration file (if found).
#: See :func:`~psyplot.config.rcsetup.psyplot_fname` for further information
config_path = psyplot_fname()
