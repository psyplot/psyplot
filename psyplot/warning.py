# coding: utf-8
"""Warning module of the psyplot python module

This module controls the warning behaviour of the module via the python
builtin warnings module and introduces three new warning classes:

..autosummay::

    PsPylotRuntimeWarning
    PsyPlotWarning
    PsyPlotCritical"""
import warnings
import logging


# disable a warning about "comparison to 'None' in backend_pdf which occurs
# in the matplotlib.backends.backend_pdf.PdfPages class
warnings.filterwarnings(
    'ignore', 'comparison', FutureWarning, 'matplotlib.backends.backend_pdf',
    2264)
# disable a warning about "np.array_split" that occurs for certain numpy
# versions
warnings.filterwarnings(
    'ignore', 'in the future np.array_split will retain', FutureWarning,
    'numpy.lib.shape_base', 431)
# disable a warning about "elementwise comparison of a string" in the
# matplotlib.collection.Collection.get_edgecolor method that occurs for certain
# matplotlib and numpy versions
warnings.filterwarnings(
    'ignore', 'elementwise comparison failed', FutureWarning,
    'matplotlib.collections', 590)


logger = logging.getLogger(__name__)


class PsyPlotRuntimeWarning(RuntimeWarning):
    """Runtime warning that appears only ones"""
    pass


class PsyPlotWarning(UserWarning):
    """Normal UserWarning for psyplot module"""
    pass


class PsyPlotCritical(UserWarning):
    """Critical UserWarning for psyplot module"""
    pass


warnings.simplefilter('always', PsyPlotWarning, append=True)
warnings.simplefilter('always', PsyPlotCritical, append=True)


def disable_warnings(critical=False):
    """Function that disables all warnings and all critical warnings (if
    critical evaluates to True) related to the psyplot Module.
    Please note that you can also configure the warnings via the
    psyplot.warning logger (logging.getLogger(psyplot.warning))."""
    warnings.filterwarnings('ignore', '\w', PsyPlotWarning, 'psyplot', 0)
    if critical:
        warnings.filterwarnings('ignore', '\w', PsyPlotCritical, 'psyplot', 0)


def warn(message, category=PsyPlotWarning, logger=None):
    """wrapper around the warnings.warn function for non-critical warnings.
    logger may be a logging.Logger instance"""
    if logger is not None:
        message = "[Warning by %s]\n%s" % (logger.name, message)
    warnings.warn(message, category, stacklevel=3)


def critical(message, category=PsyPlotCritical, logger=None):
    """wrapper around the warnings.warn function for critical warnings.
    logger may be a logging.Logger instance"""
    if logger is not None:
        message = "[Critical warning by %s]\n%s" % (logger.name, message)
    warnings.warn(message, category, stacklevel=2)


old_showwarning = warnings.showwarning


def customwarn(message, category, filename, lineno, *args, **kwargs):
    """Use the psyplot.warning logger for categories being out of
    PsyPlotWarning and PsyPlotCritical and the default warnings.showwarning
    function for all the others."""
    if category is PsyPlotWarning:
        logger.warning(warnings.formatwarning(
            "\n%s" % message, category, filename, lineno))
    elif category is PsyPlotCritical:
        logger.critical(warnings.formatwarning(
            "\n%s" % message, category, filename, lineno),
            exc_info=True)
    else:
        old_showwarning(message, category, filename, lineno, *args, **kwargs)


warnings.showwarning = customwarn
