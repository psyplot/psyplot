.. _how-to-contribute:

Contributing to psyplot
=======================

First off, thanks for taking the time to contribute!

The following is a set of guidelines for contributing to psyplot and its
packages, which are hosted on GitHub. These are mostly guidelines, not
rules. Use your best judgment, and feel free to propose changes to this
document in a pull request.

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
    print(psy.plot.name-of-your-plot-method._plugin)

If you still don’t know, where to open the issue, just go for
`psyplot <https://github.com/psyplot/psyplot/issues>`__.

How Can I Contribute?
---------------------

Reporting Bugs
~~~~~~~~~~~~~~

This section guides you through submitting a bug report for psyplot.
Following these guidelines helps maintainers and the community
understand your report, reproduce the behavior, and find related
reports.

Before creating bug reports, please check existing issues and pull
requests as you might find out that you don’t need to create one. When
you are creating a bug report, please `include as many details as
possible <#how-do-i-submit-a-good-bug-report>`__. Fill out `the required
template <https://github.com/psyplot/psyplot/issues/new>`__, the information it asks for
helps us resolve issues faster.

    **Note:** If you find a **Closed** issue that seems like it is the
    same thing that you’re experiencing, open a new issue and include a
    link to the original issue in the body of your new one.

How Do I Submit A (Good) Bug Report?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Bugs are tracked as `GitHub
issues <https://guides.github.com/features/issues/>`__. After you’ve
determined `which repository <#the-psyplot-framework>`__ your bug is
related to, create an issue on that repository and provide the following
information by filling in `the template <https://github.com/psyplot/psyplot/issues/new>`__.

Explain the problem and include additional details to help maintainers
reproduce the problem:

-  **Use a clear and descriptive title** for the issue to identify the
   problem.
-  **Describe the exact steps which reproduce the problem** in as many
   details as possible. For example, start by explaining how you started
   psyplot, e.g. which command exactly you used in the terminal, or how
   you started psyplot otherwise. When listing steps, **don’t just say
   what you did, but explain how you did it**. For example, did you
   update via GUI or console and what?
-  **Provide specific examples to demonstrate the steps**. Include links
   to files or GitHub projects, or copy/pasteable snippets, which you
   use in those examples. If you’re providing snippets in the issue, use
   `Markdown code blocks
   <https://docs.github.com/en/github/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#quoting-code>`__.
-  **Describe the behavior you observed after following the steps** and
   point out what exactly is the problem with that behavior.
-  **Explain which behavior you expected to see instead and why.**
-  **Include screenshots and animated GIFs** which show you following
   the described steps and clearly demonstrate the problem.
-  **If the problem is related to your data structure**, include a small
   example how a similar data structure can be generated

Include details about your configuration and environment:

-  **Which version of psyplot are you using?** You can get the exact
   version by running ``psyplot -aV`` in your terminal, or by starting
   the psyplot-gui and open Help->Dependencies.
-  **What’s the name and version of the OS you’re using**?

Suggesting Enhancements
~~~~~~~~~~~~~~~~~~~~~~~

This section guides you through submitting an enhancement suggestion for
psyplot, including completely new features and minor improvements to
existing functionality.

If you want to change an existing feature, use the `change feature
template <https://github.com/psyplot/psyplot/issues/new?template=change_feature.md&title=CHANGE+FEATURE:>`__,
otherwise fill in the `new feature
template <https://github.com/psyplot/psyplot/issues/new?template=new_feature.md&title=NEW+FEATURE:>`__.

How Do I Submit A (Good) Enhancement Suggestion?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Enhancement suggestions are tracked as `GitHub
issues <https://guides.github.com/features/issues/>`__. After you’ve
determined `which repository <#the-psyplot-framework>`__ your
enhancement suggestion is related to, create an issue on that repository
and provide the following information:

-  **Use a clear and descriptive title** for the issue to identify the
   suggestion.
-  **Provide a step-by-step description of the suggested enhancement**
   in as many details as possible.
-  **Provide specific examples to demonstrate the steps**. Include
   copy/pasteable snippets which you use in those examples, as
   `Markdown code blocks
   <https://docs.github.com/en/github/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#quoting-code>`__.
-  **Describe the current behavior** and **explain which behavior you
   expected to see instead** and why.
-  **Include screenshots and animated GIFs** which help you demonstrate
   the steps or point out the part of psyplot which the suggestion is
   related to.
-  **Explain why this enhancement would be useful** to most psyplot
   users.
-  **List some other analysis software or applications where this
   enhancement exists.**
-  **Specify which version of psyplot you’re using.** You can get the
   exact version by running ``psyplot -aV`` in your terminal, or by
   starting the psyplot-gui and open Help->Dependencies.
-  **Specify the name and version of the OS you’re using.**

Pull Requests
~~~~~~~~~~~~~

-  Fill in `the required template <https://github.com/psyplot/psyplot/blob/master/.github/pull_request_template.md>`__
-  Do not include issue numbers in the PR title
-  Include screenshots and animated GIFs in your pull request whenever
   possible.
-  Document new code based on the `Documentation
   Styleguide <#documentation-styleguide>`__
-  End all files with a newline and follow the
   `PEP8 <https://www.python.org/dev/peps/pep-0008/>`__, e.g. by using
   `flake8 <https://pypi.org/project/flake8/>`__

Adding new examples
~~~~~~~~~~~~~~~~~~~

You have new examples? Great! If you want to add them to the
documentation, please just fork the correct github repository and add a
jupyter notebook in the `examples repository on GitHub`_, together with
all the necessary data files.

And we are always happy to help you finalizing incomplete pull requests.

.. _examples repository on GitHub: https://github.com/psyplot/examples

Styleguides
-----------

Git Commit Messages
~~~~~~~~~~~~~~~~~~~

-  Use the present tense (“Add feature” not “Added feature”)
-  Use the imperative mood (“Move cursor to…” not “Moves cursor to…”)
-  Limit the first line (summary) to 72 characters or less
-  Reference issues and pull requests liberally after the first line
-  When only changing documentation, include ``[ci skip]`` in the commit
   title

Documentation Styleguide
~~~~~~~~~~~~~~~~~~~~~~~~

-  Follow the `numpy documentation
   guidelines <https://github.com/numpy/numpy/blob/main/doc/HOWTO_DOCUMENT.rst.txt>`__.
-  Use
   `reStructuredText <http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`__.
-  Try to not repeat yourself and make use of the
   ``psyplot.docstring.docstrings``

Example
^^^^^^^

.. code:: python

    @docstrings.get_sections(base='new_function')
    def new_function(a=1):
        """Make some cool new feature

        This function implements a cool new feature

        Parameters
        ----------
        a: int
            First parameter

        Returns
        -------
        something awesome
            The result"""
        ...

    @docstrings.dedent
    def another_new_function(a=1, b=2):
        """Make another cool new feature

        Parameters
        ----------
        %(new_function.parameters)s
        b: int
            Another parameter

        Returns
        -------
        Something even more awesome"""
        ...

.. note::

    This document has been inspired by `the contribution guidelines of Atom <https://github.com/atom/atom/blob/master/CONTRIBUTING.md>`__
