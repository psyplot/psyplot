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
on `GitHub <https://github.com/psyplot/psyplot>`__.


.. start-badges

.. only:: html and not epub

    .. list-table::
        :stub-columns: 1
        :widths: 10 90

        * - docs
          - |docs| |joss|
        * - tests
          - |travis| |appveyor| |requires| |codecov|
        * - package
          - |version| |conda| |github|
        * - implementations
          - |supported-versions| |supported-implementations|
        * - get in touch
          - |gitter| |mailing-list| |issues|

    .. |docs| image:: http://readthedocs.org/projects/psyplot/badge/?version=latest
        :alt: Documentation Status
        :target: http://psyplot.readthedocs.io/en/latest/?badge=latest

    .. |travis| image:: https://travis-ci.org/psyplot/psyplot.svg?branch=master
        :alt: Travis
        :target: https://travis-ci.org/psyplot/psyplot

    .. |appveyor| image:: https://ci.appveyor.com/api/projects/status/4nt6qrw66iw65w33/branch/master?svg=true
        :alt: AppVeyor
        :target: https://ci.appveyor.com/project/psyplot/psyplot/branch/master

    .. |codecov| image:: https://codecov.io/gh/psyplot/psyplot/branch/master/graph/badge.svg
        :alt: Coverage
        :target: https://codecov.io/gh/psyplot/psyplot

    .. |requires| image:: https://requires.io/github/psyplot/psyplot/requirements.svg?branch=master
        :alt: Requirements Status
        :target: https://requires.io/github/psyplot/psyplot/requirements/?branch=master

    .. |version| image:: https://img.shields.io/pypi/v/psyplot.svg?style=flat
        :alt: PyPI Package latest release
        :target: https://pypi.python.org/pypi/psyplot

    .. |conda| image:: https://anaconda.org/conda-forge/psyplot/badges/version.svg
        :alt: conda
        :target: https://anaconda.org/conda-forge/psyplot

    .. |supported-versions| image:: https://img.shields.io/pypi/pyversions/psyplot.svg?style=flat
        :alt: Supported versions
        :target: https://pypi.python.org/pypi/psyplot

    .. |supported-implementations| image:: https://img.shields.io/pypi/implementation/psyplot.svg?style=flat
        :alt: Supported implementations
        :target: https://pypi.python.org/pypi/psyplot

    .. |joss| image:: http://joss.theoj.org/papers/3535c28017003f0b5fb63b1b64118b60/status.svg
        :alt: Journal of Open Source Software
        :target: http://joss.theoj.org/papers/3535c28017003f0b5fb63b1b64118b60

    .. |github| image:: https://img.shields.io/github/release/psyplot/psyplot.svg
        :target: https://github.com/psyplot/psyplot/releases/latest
        :alt: Latest github release

    .. |gitter| image:: https://img.shields.io/gitter/room/psyplot/community.svg?style=flat
        :target: https://gitter.im/psyplot/community
        :alt: Gitter

    .. |mailing-list| image:: https://img.shields.io/badge/join-mailing%20list-brightgreen.svg?style=flat
        :target: https://www.listserv.dfn.de/sympa/subscribe/psyplot
        :alt: DFN mailing list

    .. |issues| image:: https://img.shields.io/github/issues-raw/psyplot/psyplot.svg?style=flat
        :target: https://github.com/psyplot/psyplot/issues
        :alt: GitHub issues

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
    accessors
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


Get in touch
------------
Any quesions? Do not hessitate to get in touch with the psyplot developers.

- Create an issue at the `bug tracker`_
- Chat with the developers in out `channel on gitter`_
- Subscribe to the `mailing list`_ and ask for support

See also the `code of conduct`_, and our
:ref:`contribution guide <how-to-contribute>`_ for more information and a guide
about good bug reports.

.. _bug tracker: https://github.com/psyplot/psyplot
.. _channel on gitter: https://gitter.im/psyplot/community
.. _mailing list: https://www.listserv.dfn.de/sympa/subscribe/psyplot
.. _code of conduct: https://github.com/psyplot/psyplot/blob/master/CODE_OF_CONDUCT.md
.. _contribution guide: https://github.com/psyplot/psyplot/blob/master/CONTRIBUTING.md

.. _citation:

How to cite psyplot
-------------------

When using psyplot, you should at least cite the publication in
`the Journal of Open Source Software`_:

.. only:: html and not epub

    .. image:: http://joss.theoj.org/papers/3535c28017003f0b5fb63b1b64118b60/status.svg
        :alt: Journal of Open Source Software
        :target: http://joss.theoj.org/papers/3535c28017003f0b5fb63b1b64118b60

Sommer, P. S.: The psyplot interactive visualization framework,
*The Journal of Open Source Software*, 2, doi:10.21105/joss.00363,
https://doi.org/10.21105/joss.00363, 2017.

:download:`BibTex <psyplot_entry.bib>` - :download:`EndNote <psyplot_entry.enw>`

Furthermore, each release of psyplot and it's :ref:`subprojects <projects>` is
associated with a DOI using zenodo.org_. If you want to cite a specific
version or plugin, please refer to the `releases page of psyplot` or the
releases page of the corresponding subproject.


.. _the Journal of Open Source Software: http://joss.theoj.org/
.. _zenodo.org: https://zenodo.org/
.. _releases page of psyplot: https://github.com/psyplot/psyplot/releases/

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
.. _HORNET grant (200021_169598): http://p3.snf.ch/project-169598



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
