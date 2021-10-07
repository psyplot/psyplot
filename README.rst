===============================================
The psyplot interactive visualization framework
===============================================

.. start-badges

.. list-table::
    :stub-columns: 1
    :widths: 10 90

    * - docs
      - |docs| |joss| |zenodo|
    * - tests
      - |circleci| |appveyor| |codecov|
    * - package
      - |version| |conda| |github|
    * - implementations
      - |supported-versions| |supported-implementations|
    * - get in touch
      - |gitter| |mailing-list| |issues|

.. |docs| image:: https://img.shields.io/github/deployments/psyplot/psyplot/github-pages
    :alt: Documentation
    :target: http://psyplot.github.io/psyplot/

.. |circleci| image:: https://circleci.com/gh/psyplot/psyplot/tree/master.svg?style=svg
    :alt: CircleCI
    :target: https://circleci.com/gh/psyplot/psyplot/tree/master

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/4nt6qrw66iw65w33/branch/master?svg=true
    :alt: AppVeyor
    :target: https://ci.appveyor.com/project/psyplot/psyplot/branch/master

.. |codecov| image:: https://codecov.io/gh/psyplot/psyplot/branch/master/graph/badge.svg
    :alt: Coverage
    :target: https://codecov.io/gh/psyplot/psyplot

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

.. |zenodo| image:: https://zenodo.org/badge/87944102.svg
    :alt: Zenodo
    :target: https://zenodo.org/badge/latestdoi/87944102

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
on `GitHub <https://github.com/psyplot/psyplot>`__ (see also
`How to contribute`_ in the docs).

.. _psyplot-gui: http://psyplot.github.io/psyplot-gui/
.. _How to contribute: http://psyplot.github.io/psyplot/contribute.html

You can see the full documentation on
`psyplot.github.io/psyplot <http://psyplot.github.io/psyplot/>`__.


Get in touch
------------
Any quesions? Do not hessitate to get in touch with the psyplot developers.

- Create an issue at the `bug tracker`_
- Chat with the developers in out `channel on gitter`_
- Subscribe to the `mailing list`_ and ask for support
- Sent a mail to psyplot@hzg.de

See also the `code of conduct`_, and our `contribution guide`_ for more
information and a guide about good bug reports.

.. _bug tracker: https://github.com/psyplot/psyplot
.. _channel on gitter: https://gitter.im/psyplot/community
.. _mailing list: https://www.listserv.dfn.de/sympa/subscribe/psyplot
.. _code of conduct: https://github.com/psyplot/psyplot/blob/master/CODE_OF_CONDUCT.md
.. _contribution guide: https://github.com/psyplot/psyplot/blob/master/CONTRIBUTING.md


How to cite psyplot
-------------------

When using psyplot, you should at least cite the publication in
`the Journal of Open Source Software`_:

.. image:: http://joss.theoj.org/papers/3535c28017003f0b5fb63b1b64118b60/status.svg
    :alt: Journal of Open Source Software
    :target: http://joss.theoj.org/papers/3535c28017003f0b5fb63b1b64118b60

Sommer, P. S.: The psyplot interactive visualization framework,
*The Journal of Open Source Software*, 2, doi:10.21105/joss.00363,
https://doi.org/10.21105/joss.00363, 2017.

Furthermore, each release of psyplot and it's subprojects_ is
associated with a DOI using zenodo.org_. If you want to cite a specific
version or plugin, please refer to the `releases page of psyplot` or the
releases page of the corresponding subproject.


.. _the Journal of Open Source Software: http://joss.theoj.org/
.. _subprojects: https://psyplot.github.io/
.. _zenodo.org: https://zenodo.org/
.. _releases page of psyplot: https://github.com/psyplot/psyplot/releases/


Acknowledgment
--------------
This package is being developed by Philipp S. Sommer at the
`Helmholtz Coastal Data Center (HCDC)`_ of the `Helmholtz-Zentrum Hereon`_.

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

.. _Helmholtz Coastal Data Center (HCDC): https://hcdc.hereon.de
.. _Helmholtz-Zentrum Hereon: https://www.hereon.de
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


Copyright
---------
Copyright © 2021 Helmholtz-Zentrum Hereon, 2020-2021 Helmholtz-Zentrum
Geesthacht, 2016-2021 University of Lausanne

psyplot is released under the GNU LGPL-3.O license.
See COPYING and COPYING.LESSER in the root of the repository for full
licensing details.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License version 3.0 as
published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU LGPL-3.0 license for more details.

You should have received a copy of the GNU LGPL-3.0 license
along with this program.  If not, see https://www.gnu.org/licenses/.
