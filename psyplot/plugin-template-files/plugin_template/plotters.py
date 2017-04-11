"""plotters module of the PLUGIN_NAME psyplot plugin

This module defines the plotters for the PLUGIN_NAME package. It should import
all requirements and define the formatoptions and plotters that are specified
in the :mod:`PLUGIN_PYNAME.plugin` module.
"""
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
