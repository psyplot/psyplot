.. SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
..
.. SPDX-License-Identifier: CC-BY-4.0
.. SPDX-License-Identifier: CC-BY-4.0

.. _contributing:

Contribution and development hints
==================================

.. warning::

   This page has been automatically generated as has not yet been reviewed by the
   authors of psyplot!

The psyplot project is developed by the
`Helmholtz-Zentrum Hereon`_. It is open-source
as we believe that this analysis can be helpful for reproducibility and
collaboration, and we are looking forward for your feedback,
questions and especially for your contributions.

- If you want to ask a question, are missing a feature or have comments on the
  docs, please `open an issue at the source code repository`_
- If you have suggestions for improvement, please let us know in an issue, or
  fork the repository and create a merge request. See also :ref:`development`.



.. contents:: Table of Contents

Code of Conduct
---------------

This project and everyone participating in it is governed by the
`psyplot Code of Conduct <https://github.com/psyplot/psyplot/blob/master/CODE_OF_CONDUCT.md>`__.
By participating, you are expected to uphold this code.

What should I know before I get started?
----------------------------------------

The psyplot framework
~~~~~~~~~~~~~~~~~~~~~

``psyplot`` is just the framework that allows interactive data analysis
and visualization. Much of the functionality however is implemented by
other packages. What package is the correct one for your bug
report/feature request, can be determined by the following list

-  `psyplot-gui <https://github.com/psyplot/psyplot-gui/issues>`__:
   Everything specific to the graphical user interface
- `psy-view <https://github.com/psyplot/psy-view/issues>`__:
  Everything specific to the psy-view graphical user interface
-  `psy-simple <https://github.com/psyplot/psy-simple/issues>`__:
   Everything concerning, e.g. the ``lineplot``, ``plot2d``, ``density``
   or ``vector`` plot methods
-  `psy-maps <https://github.com/psyplot/psy-maps/issues>`__: Everything
   concerning, e.g. the ``mapplot``, ``mapvector`` ``mapcombined`` plot
   methods
-  `psy-reg <https://github.com/psyplot/psy-reg/issues>`__: Everything
   concerning, e.g. the ``linreg`` or ``densityreg`` plot methods
-  `psyplot <https://github.com/psyplot/psyplot/issues>`__: Everything
   concerning the general framework, e.g. data handling, parallel
   update, etc.

Concerning plot methods, you can simply find out which module
implemented it via

.. code:: python

    import psyplot.project as psy

    print(psy.plot.name - of - your - plot - method._plugin)

If you still don’t know, where to open the issue, just go for
`psyplot <https://github.com/psyplot/psyplot/issues>`__.

.. _Helmholtz-Zentrum Hereon: https://www.hereon.de
.. _open an issue at the source code repository: https://codebase.helmholtz.cloud/psyplot/psyplot

.. _development:

Contributing in the development
-------------------------------

.. note::

    We use automated formatters to ensure a high quality and maintanability of
    our source code. Getting familiar with these techniques can take quite some
    time and you might get error messages that are hard to understand.

    We not slow down your development and we do our best to support you with
    these techniques. If you have any troubles, just commit with
    ``git commit --no-verify`` (see below) and the maintainers will take care
    of the tests and continuous integration.

Thanks for your wish to contribute to this project!! The source code of
the `psyplot` package is hosted at
https://codebase.helmholtz.cloud/psyplot/psyplot.


This is an open gitlab where you can register via the Helmholtz AAI. If your
home institution is not listed in the Helmholtz AAI, please use one of the
social login providers, such as Google, GitHub or OrcID.


Once you created an account in this gitlab, you can fork_ this
repository to your own user account and implement the changes.

Afterwards, please make a merge request into the main repository. If you
have any questions, please do not hesitate to create an issue on gitlab
and contact the maintainers of this package.

Once you created you fork, you can clone it via

.. code-block:: bash

    git clone https://codebase.helmholtz.cloud/<your-user>/psyplot.git

we recommend that you change into the directory and create a virtual
environment via::

   cd psyplot
   python -m venv venv
   source venv/bin/activate # (or venv/Scripts/Activate.bat on windows)

and install it in development mode with the ``[dev]`` option via::

    pip install -e ./psyplot/[dev]


Helpers
-------

Shortcuts with make
~~~~~~~~~~~~~~~~~~~
There are several shortcuts available with the ``Makefile`` in the root of
the repository. On Linux, you can execute ``make help`` to get an overview.

Annotating licenses
~~~~~~~~~~~~~~~~~~~

If you want to create new files, you need to set license and copyright
statements correctly. We use ``reuse`` to check that the licenses are
correctly encoded. As a helper script, you can use the script at
``.reuse/add_license.py`` that provides several shortcuts from
``.reuse/shortcuts.yaml``. Please select the correct shortcut, namely

- If you create a new python file, you should run::

      python .reuse/add_license.py code <file-you-created>.py

- If you created a new file for the docs, you should run::

      python .reuse/add_license.py docs <file-you-created>.py

- If you created any other non-code file, you should run::

      python .reuse/add_license.py supp <file-you-created>.py

If you have any questions on how licenses are handled, please do not hesitate
to contact the maintainers of `psyplot`.


Fixing the docs
---------------
The documentation for this package is written in restructured Text and built
with sphinx_ and deployed on readthedocs_.

If you found something in the docs that you want to fix, head over to the
``docs`` folder, install the necessary requirements via
``pip install -r requirements.txt ../[docs]`` and build the docs with
``make html`` (or ``make.bat`` on windows).

The docs are then available in ``docs/_build/html/index.html`` that you can
open with your local browser.

Implement your fixes in the corresponding ``.rst``-file and push them to your
fork on gitlab.

Contributing to the code
------------------------
We use automated formatters (see their config in ``pyproject.toml``), namely

- `Black <https://black.readthedocs.io/en/stable/>`__ for standardized
  code formatting
- `blackdoc <https://blackdoc.readthedocs.io/en/latest/>`__ for
  standardized code formatting in documentation
- `Flake8 <http://flake8.pycqa.org/en/latest/>`__ for general code
  quality
- `isort <https://github.com/PyCQA/isort>`__ for standardized order in
  imports.
- `mypy <http://mypy-lang.org/>`__ for static type checking on
  `type hints <https://docs.python.org/3/library/typing.html>`__
- `reuse <https://reuse.readthedocs.io/>`__ for handling of licenses
- `cffconvert <https://github.com/citation-file-format/cff-converter-python>`__
  for validating the ``CITATION.cff`` file.

We highly recommend that you setup
`pre-commit hooks <https://pre-commit.com/>`__ to automatically run all the
above tools every time you make a git commit. This can be done by running::

   pre-commit install

from the root of the repository. You can skip the pre-commit checks with
``git commit --no-verify`` but note that the CI will fail if it
encounters any formatting errors.

You can also run the ``pre-commit`` step manually by invoking::

   pre-commit run --all-files


.. _fork: https://codebase.helmholtz.cloud/psyplot/psyplot/-/forks/new

.. _sphinx: https://www.sphinx-doc.org
.. _readthedocs: https://readthedocs.org


Updating the skeleton for this package
--------------------------------------

This package has been generated from the template
`https://codebase.helmholtz.cloud/hcdc/software-templates/python-package-template.git`__.

See the template repository for instructions on how to update the skeleton for
this package.
