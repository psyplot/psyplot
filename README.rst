.. SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
..
.. SPDX-License-Identifier: CC-BY-4.0

===============================================
The psyplot interactive visualization framework
===============================================

.. start-badges

|CI|
|Code coverage|
|Latest Release|
|PyPI version|
|Code style: black|
|Imports: isort|
|PEP8|
|REUSE status|

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
on `GitHub <https://codebase.helmholtz.cloud/psyplot/psyplot>`__ (see also
`How to contribute`_ in the docs).

.. _psyplot-gui: http://psyplot.github.io/psyplot-gui/
.. _How to contribute: http://psyplot.github.io/psyplot/contribute.html

You can see the full documentation on
`psyplot.github.io/psyplot <http://psyplot.github.io/psyplot/>`__.


Get in touch
------------
Any quesions? Do not hessitate to get in touch with the psyplot developers.

- Create an issue at the `bug tracker`_
- Chat with the developers in out `team on mattermost`_
- Subscribe to the `mailing list`_ and ask for support
- Sent a mail to psyplot@hzg.de

See also the `code of conduct`_, and our `contribution guide`_ for more
information and a guide about good bug reports.

.. _bug tracker: https://codebase.helmholtz.cloud/psyplot/psyplot
.. _team on mattermost: https://mattermost.hzdr.de/psyplot/
.. _mailing list: https://www.listserv.dfn.de/sympa/subscribe/psyplot
.. _code of conduct: https://codebase.helmholtz.cloud/psyplot/psyplot/blob/master/CODE_OF_CONDUCT.md
.. _contribution guide: https://codebase.helmholtz.cloud/psyplot/psyplot/blob/master/CONTRIBUTING.md


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
.. _releases page of psyplot: https://codebase.helmholtz.cloud/psyplot/psyplot/-/releases


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


.. |CI| image:: https://codebase.helmholtz.cloud/psyplot/psyplot/badges/master/pipeline.svg
   :target: https://codebase.helmholtz.cloud/psyplot/psyplot/-/pipelines?page=1&scope=all&ref=master
.. |Code coverage| image:: https://codebase.helmholtz.cloud/psyplot/psyplot/badges/master/coverage.svg
   :target: https://codebase.helmholtz.cloud/psyplot/psyplot/-/graphs/develop/charts
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
.. |REUSE status| image:: https://api.reuse.software/badge/codebase.helmholtz.cloud/psyplot/psyplot
   :target: https://api.reuse.software/info/codebase.helmholtz.cloud/psyplot/psyplot
