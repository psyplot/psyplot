"""psyplot visualization framework
"""
import sys
import datetime as dt
import logging as _logging
from psyplot.warning import warn, critical, disable_warnings
from psyplot.config.rcsetup import rcParams
import psyplot.config as config
from psyplot.data import (
    ArrayList, InteractiveArray, InteractiveList, open_dataset, open_mfdataset)
from psyplot.version import __version__

__author__ = "Philipp Sommer (philipp.sommer@unil.ch)"

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
    from pkg_resources import iter_entry_points
    ret = {'psyplot': _get_versions(requirements)}
    for ep in iter_entry_points(group='psyplot', name='plugin'):
        if str(ep) in rcParams._plugins:
            logger.debug('Loading entrypoint %s', ep)
            if key is not None and not key(ep.module_name):
                continue
            mod = ep.load()
            try:
                ret[str(ep.module_name)] = mod.get_versions(requirements)
            except AttributeError:
                ret[str(ep.module_name)] = {
                    'version': getattr(mod, 'plugin_version',
                                       getattr(mod, '__version__', ''))}
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
