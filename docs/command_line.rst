.. _command-line:

Command line usage
==================
The :mod:`psyplot.main` module defines a simple parser to parse commands
from the command line to make a plot of data in a netCDF file. Note that the
arguments change slightly if you have the ``psyplot-gui`` module installed
(see :ref:`psyplot-gui <psyplot_gui:command-line>` documentation)

.. highlight:: bash

.. argparse::
   :module: psyplot.__main__
   :func: get_parser
   :prog: psyplot
