.. psyplot documentation master file, created by
   sphinx-quickstart on Mon Jul 20 18:01:33 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _psyplot:

Interactive data visualization with python
==========================================

.. image:: _static/psyplot.png
    :width: 50%
    :alt: psyplot logo
    :align: center

Welcome! Looking for a fast and flexible visualization software? Here we
present **psyplot**, an open source python project that mainly combines the
plotting utilities of matplotlib_ and the data management of the xarray_
package and integrates them into a software that can be used via command-line
and via a GUI!

The main purpose is to have a framework that allows a  fast, attractive,
flexible, easily applicable, easily reproducible and especially an interactive
visualization of your data.

The ultimate goal is to help scientists in their daily work by providing a
flexible visualization tool that can be enhanced by their own visualization
scripts. ``psyplot`` can be used via command line and with the
graphical user interface (GUI) from the
:ref:`psyplot-gui <psyplot_gui:psyplot-gui>` module.

If you want more motivation: Have a look into the :ref:`about` section.

The package is very new and there are many features that will be included in
the future. So we are very pleased for feedback! Please simply raise an issue
on `GitHub <https://github.com/Chilipp/psyplot>`__.


.. start-badges

.. only:: html and not epub

    .. list-table::
        :stub-columns: 1
        :widths: 10 90

        * - docs
          - |docs| |joss|
        * - tests
          - |travis| |appveyor| |requires| |coveralls|
        * - package
          - |version| |conda| |supported-versions| |supported-implementations|

    .. |docs| image:: http://readthedocs.org/projects/psyplot/badge/?version=latest
        :alt: Documentation Status
        :target: http://psyplot.readthedocs.io/en/latest/?badge=latest

    .. |travis| image:: https://travis-ci.org/Chilipp/psyplot.svg?branch=master
        :alt: Travis
        :target: https://travis-ci.org/Chilipp/psyplot

    .. |appveyor| image:: https://ci.appveyor.com/api/projects/status/3jk6ea1n4a4dl6vk/branch/master?svg=true
        :alt: AppVeyor
        :target: https://ci.appveyor.com/project/Chilipp/psyplot/branch/master

    .. |coveralls| image:: https://coveralls.io/repos/github/Chilipp/psyplot/badge.svg?branch=master
        :alt: Coverage
        :target: https://coveralls.io/github/Chilipp/psyplot?branch=master

    .. |requires| image:: https://requires.io/github/Chilipp/psyplot/requirements.svg?branch=master
        :alt: Requirements Status
        :target: https://requires.io/github/Chilipp/psyplot/requirements/?branch=master

    .. |version| image:: https://img.shields.io/pypi/v/psyplot.svg?style=flat
        :alt: PyPI Package latest release
        :target: https://pypi.python.org/pypi/psyplot

    .. |conda| image:: https://anaconda.org/conda-forge/psyplot/badges/version.svg
        :alt: conda
        :target: https://conda.anaconda.org/conda-forge/psyplot

    .. |supported-versions| image:: https://img.shields.io/pypi/pyversions/psyplot.svg?style=flat
        :alt: Supported versions
        :target: https://pypi.python.org/pypi/psyplot

    .. |supported-implementations| image:: https://img.shields.io/pypi/implementation/psyplot.svg?style=flat
        :alt: Supported implementations
        :target: https://pypi.python.org/pypi/psyplot

    .. |joss| image:: http://joss.theoj.org/papers/3535c28017003f0b5fb63b1b64118b60/status.svg
        :alt: Journal of Open Source Software
        :target: http://joss.theoj.org/papers/3535c28017003f0b5fb63b1b64118b60

.. end-badges


Documentation
-------------

.. toctree::
    :maxdepth: 1

    about
    installing
    getting_started
    configuration
    projects
    plugins
    command_line
    examples/index
    develop/index
    contribute
    api/psyplot
    todos
    changelog


Examples
--------

.. linkgalleries::

    psyplot
    psy_simple
    psy_maps
    psy_reg


Acknowledgment
--------------
This package has been developed by Philipp Sommer.

I want to thank the matplotlib_, xarray_ and cartopy_ developers
for their great packages and of course the python developers for their
fascinating work on this beautiful language.

A special thanks to Stefan Hagemann and Tobias Stacke from the
Max-Planck-Institute of Meteorology in Hamburg, Germany for the motivation on
this project and to the people of the `Not yet visible`_ agency for their
advice in designing the logo and webpage.

Finally the author thanks the Swiss National Science Foundation (SNF) for their
support. Funding for the author came from the `ACACIA grant (CR10I2_146314)`_
and the `HORNET grant (200021_169598)`_.

.. _matplotlib: http://matplotlib.org
.. _xarray: http://xarray.pydata.org/
.. _cartopy: http://scitools.org.uk/cartopy
.. _Not yet visible: https://notyetvisible.de/
.. _ACACIA grant (CR10I2_146314): http://p3.snf.ch/project-146314
.. _HORNET grant (169598): http://p3.snf.ch/project-169598



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
