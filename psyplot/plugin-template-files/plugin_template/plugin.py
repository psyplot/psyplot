"""PLUGIN_NAME psyplot plugin

This module defines the rcParams for the PLUGIN_NAME plugin. This module will
be imported when psyplot is imported. What is should contain is:

- an rcParams variable as instance of :class:`psyplot.config.rcsetup.RcParams`
  that describes the configuration of your plugin
- a get_versions function that returns the version of your plugin and the ones
  from its requirements

.. warning::

    Because of recursion issues, You have to load the psyplot module before
    loading this module! In other words, you have to type

    .. code-block:: python

        import psyplot
        import PLUGIN_PYNAME.plugin"""
from psyplot.config.rcsetup import RcParams
from PLUGIN_PYNAME import __version__ as plugin_version


def get_versions(requirements=True):
    """Get the versions of PLUGIN_NAME and it's requirements

    Parameters
    ----------
    requirements: bool
        If True, the requirements are imported and it's versions are included
    """
    ret = {'version': plugin_version}
    if requirements:
        # insert versions of the requirements, e.g. via
        #   >>> import requirement
        #   >>> ret['requirement'] = requirement.__version__
        pass
    return ret


# -----------------------------------------------------------------------------
# ------------------------- validation functions ------------------------------
# -----------------------------------------------------------------------------


# define your validation functions for the values in the rcParams here. If
# a validation fails, the function should raise a ValueError or TypeError


# -----------------------------------------------------------------------------
# ------------------------------ rcParams -------------------------------------
# -----------------------------------------------------------------------------


# define your defaultParams. A mapping from rcParams key to a list of length 3:
#
# 1. the default value
# 2. the validation function of type conversion function
# 3. a short description of the default value
#
# Example::
#
#     defaultParams = {'my.key': [True, bool, 'What my key does']}
defaultParams = {

    # key for defining new plotters
    'project.plotters': [
        {'plot_method_identifer': {
             'module': 'PLUGIN_PYNAME.plotters',
             'plotter_name': 'MyPlotter',   # or any other name
             # any other item for the :func:`psyplot.project.register_plotter`
             # function
             # 'plot_func': False,
             # 'prefer_list': True,
             # ...
             },
         }, dict, "The plot methods in the PLUGIN_NAME package"],
    # if you define new plotters, we recommend to assign a specific rcParams
    # key for it, e.g.
    # 'plotter.PLUGIN_PYNAME.my_fmt': [1, int, ' the value for my_fmt']
    }

# create the rcParams and populate them with the defaultParams. For more
# information on this class, see the :class:`psyplot.config.rcsetup.RcParams`
# class
rcParams = RcParams(defaultParams=defaultParams)
rcParams.update_from_defaultParams()
