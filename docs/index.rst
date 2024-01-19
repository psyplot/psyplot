.. SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
..
.. SPDX-License-Identifier: CC-BY-4.0

.. psyplot documentation master file
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _psyplot:

Interactive data visualization with python
==========================================

|CI|
|Code coverage|
|Latest Release|
|PyPI version|
|Code style: black|
|Imports: isort|
|PEP8|
|Checked with mypy|
|REUSE status|

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
:ref:`psyplot-gui <psyplot_gui:psyplot-gui>` and
:ref:`psy-view <psy_view:psy-view>` module.

If you want more motivation: Have a look into the :ref:`about` section.


Documentation
-------------

.. toctree::
    :maxdepth: 1

    about
    installing
    getting_started
    Example Gallery <https://psyplot.github.io/examples/>
    configuration
    projects
    accessors
    plugins
    command_line
    develop/index
    contributing
    api
    todos
    changelog


Get in touch
------------
Any quesions? Do not hessitate to get in touch with the psyplot developers.

- Create an issue at the `bug tracker`_
- Chat with the developers in out `team on mattermost`_
- Subscribe to the `mailing list`_ and ask for support

See also the `code of conduct`, and our
:ref:`contribution guide <how-to-contribute>` for more information and a guide
about good bug reports.

.. _bug tracker: https://github.com/psyplot/psyplot
.. _team on mattermost: https://mattermost.hzdr.de/psyplot/
.. _mailing list: https://www.listserv.dfn.de/sympa/subscribe/psyplot
.. _code of conduct: https://github.com/psyplot/psyplot/blob/master/CODE_OF_CONDUCT.md
.. _contribution guide: https://github.com/psyplot/psyplot/blob/master/CONTRIBUTING.md

.. _citation:

How to cite this software
-------------------------

.. card:: Please do cite this software!

   .. tab-set::

      .. tab-item:: APA

         .. citation-info::
            :format: apalike

      .. tab-item:: BibTex

         .. citation-info::
            :format: bibtex

      .. tab-item:: RIS

         .. citation-info::
            :format: ris

      .. tab-item:: Endnote

         .. citation-info::
            :format: endnote

      .. tab-item:: CFF

         .. citation-info::
            :format: cff

Furthermore, each release of psyplot and it's :ref:`subprojects <projects>` is
associated with a DOI on zenodo_. If you want to cite a specific
version or plugin, please refer to the `releases page of psyplot` or the
releases page of the corresponding subproject.

.. _zenodo: https://zenodo.org


Acknowledgment
--------------
This package is being developed by Philipp S. Sommer at the
`Helmholtz Coastal Data Center (HCDC)`_ of the `Helmholtz-Zentrum Hereon`_.

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

.. _Helmholtz Coastal Data Center (HCDC): https://hcdc.hereon.de
.. _Helmholtz-Zentrum Hereon: https://www.hereon.de
.. _matplotlib: https://matplotlib.org
.. _xarray: https://xarray.pydata.org/
.. _cartopy: https://scitools.org.uk/cartopy
.. _Not yet visible: https://notyetvisible.de/
.. _ACACIA grant (CR10I2_146314): https://p3.snf.ch/project-146314
.. _HORNET grant (200021_169598): https://p3.snf.ch/project-169598



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. |CI| image:: https://codebase.helmholtz.cloud/psyplot/psyplot/badges/main/pipeline.svg
   :target: https://codebase.helmholtz.cloud/psyplot/psyplot/-/pipelines?page=1&scope=all&ref=main
.. |Code coverage| image:: https://codebase.helmholtz.cloud/psyplot/psyplot/badges/main/coverage.svg
   :target: https://codebase.helmholtz.cloud/psyplot/psyplot/-/graphs/package-template/charts
.. |Latest Release| image:: https://codebase.helmholtz.cloud/psyplot/psyplot/-/badges/release.svg
   :target: https://codebase.helmholtz.cloud/psyplot/psyplot
.. |PyPI version| image:: https://img.shields.io/pypi/v/psyplot.svg
   :target: https://pypi.python.org/pypi/psyplot/
.. |Code style: black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
.. |Imports: isort| image:: https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336
   :target: https://pycqa.github.io/isort/
.. |PEP8| image:: https://img.shields.io/badge/code%20style-pep8-orange.svg
   :target: https://www.python.org/dev/peps/pep-0008/
.. |Checked with mypy| image:: http://www.mypy-lang.org/static/mypy_badge.svg
   :target: http://mypy-lang.org/
.. TODO: uncomment the following line when the package is registered at https://api.reuse.software
.. .. |REUSE status| image:: https://api.reuse.software/badge/codebase.helmholtz.cloud/psyplot/psyplot
..    :target: https://api.reuse.software/info/codebase.helmholtz.cloud/psyplot/psyplot
