"""Configuration module of the psyplot package

This module contains the module for managing rc parameters and the logging.
Default parameters are defined in the :data:`rcsetup.defaultParams`
dictionary, however you can set up your own configuration in a yaml file (see
:func:`psyplot.load_rc_from_file`)"""

# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht

# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: LGPL-3.0-only

from .logsetup import setup_logging
from .rcsetup import psyplot_fname

#: :class:`str`. Path to the yaml logging configuration file
logcfg_path = setup_logging()


#: class:`str` or ``None``. Path to the yaml configuration file (if found).
#: See :func:`~psyplot.config.rcsetup.psyplot_fname` for further information
config_path = psyplot_fname()
