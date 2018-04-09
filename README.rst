===============================================
The psyplot interactive visualization framework
===============================================

.. start-badges

.. list-table::
    :stub-columns: 1
    :widths: 10 90

    * - docs
      - |docs| |joss|
    * - tests
      - |travis| |appveyor| |requires| |coveralls|
    * - package
      - |version| |conda| |github|
    * - implementations
      - |supported-versions| |supported-implementations|

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

.. |github| image:: https://img.shields.io/github/release/Chilipp/psyplot.svg
    :target: https://github.com/Chilipp/psyplot/releases/latest
    :alt: Latest github release

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
provides a graphical user interface for an easier interactive usage.

The package is very new and there are many features that will be included in
the future. So we are very pleased for feedback! Please simply raise an issue
on `GitHub <https://github.com/Chilipp/psyplot>`__ (see also
`How to contribute`_ in the docs).

.. _psyplot-gui: http://psyplot.readthedocs.io/projects/psyplot-gui/en/latest
.. _How to contribute: http://psyplot.readthedocs.io/en/latest/contribute.html

You can see the full documentation on
`readthedocs.org <http://psyplot.readthedocs.io/en/latest/>`__.


Acknowledgment
--------------
This package has been developed by Philipp Sommer.

I want to thank the developers of the matplotlib_, xarray_ and cartopy_
packages for their great packages and of course the python developers for their
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
.. _HORNET grant (200021_169598): http://p3.snf.ch/project-169598



Note
----
Commits on github prior to version 1.0 were moved into another repository, the
`psyplot_old`_ repository. This has been done because prior to version 1.0,
the github repository contained all the reference figures used for testing
which made the size of the repository too large.

.. _psyplot_old: https://github.com/Chilipp/psyplot_old
