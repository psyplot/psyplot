"""Logging configuration module of the psyplot package

This module defines the essential functions for setting up the
:class:`logging.Logger` instances that are used by the psyplot package."""
import os
import six
import sys
import logging
import logging.config
import yaml
from psyplot.docstring import dedent


def _get_home():
    """Find user's home directory if possible.
    Otherwise, returns None.

    :see:  http://mail.python.org/pipermail/python-list/2005-February/325395.html

    This function is copied from matplotlib version 1.4.3, Jan 2016
    """
    try:
        if six.PY2 and sys.platform == 'win32':
            path = os.path.expanduser(b"~").decode(sys.getfilesystemencoding())
        else:
            path = os.path.expanduser("~")
    except ImportError:
        # This happens on Google App Engine (pwd module is not present).
        pass
    else:
        if os.path.isdir(path):
            return path
    for evar in ('HOME', 'USERPROFILE', 'TMP'):
        path = os.environ.get(evar)
        if path is not None and os.path.isdir(path):
            return path
    return None


@dedent
def setup_logging(default_path=None, default_level=logging.INFO,
                  env_key='LOG_PSYPLOT'):
    """
    Setup logging configuration

    Parameters
    ----------
    default_path: str
        Default path of the yaml logging configuration file. If None, it
        defaults to the 'logging.yaml' file in the config directory
    default_level: int
        Default: :data:`logging.INFO`. Default level if default_path does not
        exist
    env_key: str
        environment variable specifying a different logging file than
        `default_path` (Default: 'LOG_CFG')

    Returns
    -------
    path: str
        Path to the logging configuration file

    Notes
    -----
    Function taken from
    http://victorlin.me/posts/2012/08/26/good-logging-practice-in-python"""
    path = default_path or os.path.join(
        os.path.dirname(__file__), 'logging.yml')
    value = os.getenv(env_key, None)
    home = _get_home()
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.load(f.read())
        for handler in config.get('handlers', {}).values():
            if '~' in handler.get('filename', ''):
                handler['filename'] = handler['filename'].replace(
                    '~', home)
        logging.config.dictConfig(config)
    else:
        path = None
        logging.basicConfig(level=default_level)
    return path
