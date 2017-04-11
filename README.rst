===============================================
The psyplot interactive visualization framework
===============================================

.. start-badges

.. list-table::
    :stub-columns: 1
    :widths: 10 90

    * - docs
      - |docs|
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

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/3jk6ea1n4a4dl6vk?svg=true
    :alt: AppVeyor
    :target: https://ci.appveyor.com/project/Chilipp/psyplot

.. |coveralls| image:: https://coveralls.io/repos/github/Chilipp/psyplot/badge.svg?branch=master
    :alt: Coverage
    :target: https://coveralls.io/github/Chilipp/psyplot?branch=master

.. |requires| image:: https://requires.io/github/Chilipp/psyplot/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/Chilipp/psyplot/requirements/?branch=master

.. |version| image:: https://img.shields.io/pypi/v/psyplot.svg?style=flat
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/psyplot

.. |conda| image:: https://anaconda.org/chilipp/psyplot/badges/installer/conda.svg
    :alt: conda
    :target: https://conda.anaconda.org/chilipp

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/psyplot.svg?style=flat
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/psyplot

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/psyplot.svg?style=flat
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/psyplot


.. end-badges

Welcome! **psyplot** is an open source python project that mainly combines the
plotting utilities of matplotlib_ and the data management of the xarray_
package. The main purpose is to have a framework that allows a  fast,
attractive, flexible, easily applicable, easily reproducible and especially
an interactive visualization of your data.

The ultimate goal is to help scientists and especially climate model
developers in their daily work by providing a flexible visualization tool that
can be enhanced by their own visualization scripts. ``psyplot`` can be used
through the python command line and through the psyplot-gui_ module which
provides a graphical user interface for an easier interactive usage. See the
:ref:`about` section for more motivation.

The package is very new and there are many features that will be included in
the future. So we are very pleased for feedback! Please simply raise an issue
on `GitHub <https://github.com/Chilipp/psyplot>`__.

.. _psyplot-gui: http://psyplot-gui.readthedocs.io/en/latest/

You can see the full documentation on
`readthedocs.org <http://psyplot.readthedocs.io/en/latest/?badge=latest>`__.


Acknowledgment
--------------
This package has been developed by Philipp Sommer.

I want to thank the developers of the matplotlib_, xarray_ and cartopy_
packages for their great packages and of course the python developers for their
fascinating work on this beautiful language.

A special thanks to Stefan Hagemann and Tobias Stacke from the
Max-Planck-Institute of Meteorology in Hamburg, Germany for the motivation on
this project.

.. _matplotlib: http://matplotlib.org
.. _xarray: http://xarray.pydata.org/
.. _cartopy: http://scitools.org.uk/cartopy
