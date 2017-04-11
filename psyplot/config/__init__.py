"""Configuration module of the psyplot package

This module contains the module for managing rc parameters and the logging.
Default parameters are defined in the :data:`rcsetup.defaultParams`
dictionary, however you can set up your own configuration in a yaml file (see
:func:`psyplot.load_rc_from_file`)"""
from .logsetup import setup_logging

#: :class:`str`. Path to the yaml logging configuration file
logcfg_path = setup_logging()


from .rcsetup import psyplot_fname


#: class:`str` or ``None``. Path to the yaml configuration file (if found).
#: See :func:`psyplot.config.rcsetup.psyplot_fname` for further information
config_path = psyplot_fname()
