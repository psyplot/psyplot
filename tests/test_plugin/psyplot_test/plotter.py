# Test module that defines a plotter
#
# The plotter in this module has been registered by the rcParams in the plugin
# package
from psyplot.plotter import Plotter, Formatoption
from psyplot_test.plugin import rcParams


class TestFmt(Formatoption):
    """Some documentation"""

    default = None

    def update(self, value):
        pass


class TestPlotter(Plotter):

    fmt1 = TestFmt('fmt1')
