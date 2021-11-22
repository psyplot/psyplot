"""psyplot visualization framework."""

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

import sys
import datetime as dt
import logging as _logging
from psyplot.warning import warn, critical, disable_warnings
from psyplot.config.rcsetup import rcParams
import psyplot.config as config
from psyplot.data import (
    ArrayList, InteractiveArray, InteractiveList, open_dataset, open_mfdataset)

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


__author__ = "Philipp S. Sommer"
__copyright__ = """
Copyright (C) 2021 Helmholtz-Zentrum Hereon
Copyright (C) 2020-2021 Helmholtz-Zentrum Geesthacht
Copyright (C) 2016-2021 University of Lausanne
"""
__credits__ = ["Philipp S. Sommer"]
__license__ = "LGPL-3.0-only"

__maintainer__ = "Philipp S. Sommer"
__email__ = "psyplot@hereon.de"

__status__ = "Production"


logger = _logging.getLogger(__name__)
logger.debug(
    "%s: Initializing psyplot, version %s",
    dt.datetime.now().isoformat(), __version__)
logger.debug("Logging configuration file: %s", config.logcfg_path)
logger.debug("Configuration file: %s", config.config_path)


rcParams.HEADER += "\n\npsyplot version: " + __version__
rcParams.load_plugins()
rcParams.load_from_file()


_project_imported = False

#: Boolean that is True, if psyplot runs inside the graphical user interface
#: by the ``psyplot_gui`` module
with_gui = False


def get_versions(requirements=True, key=None):
    """
    Get the version information for psyplot, the plugins and its requirements

    Parameters
    ----------
    requirements: bool
        If True, the requirements of the plugins and psyplot are investigated
    key: func
        A function that determines whether a plugin shall be considererd or
        not. The function must take a single argument, that is the name of the
        plugin as string, and must return True (import the plugin) or False
        (skip the plugin). If None, all plugins are imported

    Returns
    -------
    dict
        A mapping from ``'psyplot'``/the plugin names to a dictionary with the
        ``'version'`` key and the corresponding version is returned. If
        `requirements` is True, it also contains a mapping from
        ``'requirements'`` a dictionary with the versions

    Examples
    --------
    Using the built-in JSON module, we get something like

    .. code-block:: python

        import json
        print(json.dumps(psyplot.get_versions(), indent=4))
        {
            "psy_simple.plugin": {
                "version": "1.0.0.dev0"
            },
            "psyplot": {
                "version": "1.0.0.dev0",
                "requirements": {
                    "matplotlib": "1.5.3",
                    "numpy": "1.11.3",
                    "pandas": "0.19.2",
                    "xarray": "0.9.1"
                }
            },
            "psy_maps.plugin": {
                "version": "1.0.0.dev0",
                "requirements": {
                    "cartopy": "0.15.0"
                }
            }
        }
    """
    from importlib.metadata import entry_points
    ret = {'psyplot': _get_versions(requirements)}

    try:
        eps = entry_points(group='psyplot', name='plugin')
    except TypeError:  # python<3.10
        eps = [ep for ep in entry_points().get('psyplot', [])
                if ep.name ==  'plugin']
    for ep in eps:
        if str(ep) in rcParams._plugins:
            logger.debug('Loading entrypoint %s', ep)

            try:
                ep.module
            except AttributeError:  # python<3.10
                ep.module = ep.pattern.match(ep.value).group("module")

            if key is not None and not key(ep.module):
                continue
            try:
                mod = ep.load()
            except (ImportError, ModuleNotFoundError) as e:
                logger.debug("Could not import %s" % (ep, ), exc_info=True)
                logger.warning("Could not import %s" % (ep, ), exc_info=True)
            else:
                try:
                    ret[str(ep.module)] = mod.get_versions(requirements)
                except AttributeError:
                    ret[str(ep.module)] = {
                        'version': getattr(
                            mod, 'plugin_version',
                            getattr(mod, '__version__', ''))
                        }
    if key is None:
        try:
            import psyplot_gui
        except ImportError:
            pass
        else:
            ret['psyplot_gui'] = psyplot_gui.get_versions(requirements)
    return ret


def _get_versions(requirements=True):
    if requirements:
        import matplotlib as mpl
        import xarray as xr
        import pandas as pd
        import numpy as np
        return {'version': __version__,
                'requirements': {'matplotlib': mpl.__version__,
                                 'xarray': xr.__version__,
                                 'pandas': pd.__version__,
                                 'numpy': np.__version__,
                                 'python': ' '.join(sys.version.splitlines())}}
    else:
        return {'version': __version__}
