.. highlight:: bash

.. _command-line:

Command line usage
==================
The :mod:`psyplot.__main__` module defines a simple parser to parse commands
from the command line to make a plot of data in a netCDF file. Note that the
arguments change slightly if you have the ``psyplot-gui`` module installed
(see :ref:`psyplot-gui <psyplot_gui:command-line>` documentation).

It can be run from the command line via::

    python -m psyplot [options] [arguments]

or simply::

    psyplot [options] [arguments]

.. argparse::
   :module: psyplot.__main__
   :func: get_parser
   :prog: psyplot
