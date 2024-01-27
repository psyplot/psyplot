"""Docstring module of the psyplot package

We use the docrep_ package for managing our docstrings

.. _docrep: http://docrep.readthedocs.io/en/latest/
"""

# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht

# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: LGPL-3.0-only

import inspect
import types

import six
from docrep import DocstringProcessor, safe_modulo  # noqa: F401


def dedent(func):
    """
    Dedent the docstring of a function and substitute with :attr:`params`

    Parameters
    ----------
    func: function
        function with the documentation to dedent"""
    if isinstance(func, types.MethodType) and not six.PY3:
        func = func.im_func
    func.__doc__ = func.__doc__ and inspect.cleandoc(func.__doc__)
    return func


def indent(text, num=4):
    """Indet the given string"""
    str_indent = " " * num
    return str_indent + ("\n" + str_indent).join(text.splitlines())


def append_original_doc(parent, num=0):
    """Return an iterator that append the docstring of the given `parent`
    function to the applied function"""

    def func(func):
        func.__doc__ = func.__doc__ and func.__doc__ + indent(
            parent.__doc__, num
        )
        return func

    return func


_docstrings = DocstringProcessor()

_docstrings.get_sections(base="DocstringProcessor.get_sections")(
    dedent(DocstringProcessor.get_sections)
)


class PsyplotDocstringProcessor(DocstringProcessor):
    """
    A :class:`docrep.DocstringProcessor` subclass with possible types section
    """

    param_like_sections = DocstringProcessor.param_like_sections + [
        "Possible types"
    ]

    @_docstrings.dedent
    def get_sections(
        self,
        s=None,
        base=None,
        sections=["Parameters", "Other Parameters", "Possible types"],
    ):
        """
        Extract the specified sections out of the given string

        The same as the :meth:`docrep.DocstringProcessor.get_sections` method
        but uses the ``'Possible types'`` section by default, too

        Parameters
        ----------
        %(DocstringProcessor.get_sections.parameters)s

        Returns
        -------
        str
            The replaced string
        """
        return super(PsyplotDocstringProcessor, self).get_sections(
            s, base, sections
        )


del _docstrings

#: :class:`docrep.PsyplotDocstringProcessor` instance that simplifies the reuse
#: of docstrings from between different python objects.
docstrings = PsyplotDocstringProcessor()
