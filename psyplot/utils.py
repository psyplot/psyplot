"""Miscallaneous utility functions for the psyplot package."""

# Disclaimer
# ----------
#
# Copyright (C) 2021 Helmholtz-Zentrum Hereon
# Copyright (C) 2020-2021 Helmholtz-Zentrum Geesthacht
# Copyright (C) 2016-2021 University of Lausanne
#
# This file is part of psyplot and is released under the GNU LGPL-3.O license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3.0 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU LGPL-3.0 license for more details.
#
# You should have received a copy of the GNU LGPL-3.0 license
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import re
import six
from difflib import get_close_matches
from itertools import chain
from psyplot.compat.pycompat import OrderedDict, filterfalse
from psyplot.docstring import dedent, docstrings


class DefaultOrderedDict(OrderedDict):
    """An ordered :class:`collections.defaultdict`

    Taken from http://stackoverflow.com/a/6190500/562769"""
    def __init__(self, default_factory=None, *a, **kw):
        if (default_factory is not None and
           not callable(default_factory)):
            raise TypeError('first argument must be callable')
        OrderedDict.__init__(self, *a, **kw)
        self.default_factory = default_factory

    def __getitem__(self, key):
        try:
            return OrderedDict.__getitem__(self, key)
        except KeyError:
            return self.__missing__(key)

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = value = self.default_factory()
        return value

    def __reduce__(self):
        if self.default_factory is None:
            args = tuple()
        else:
            args = self.default_factory,
        return type(self), args, None, None, self.items()

    def copy(self):
        """Return a shallow copy of the dictionary"""
        return self.__copy__()

    def __copy__(self):
        return type(self)(self.default_factory, self)

    def __deepcopy__(self, memo):
        import copy
        return type(self)(self.default_factory,
                          copy.deepcopy(self.items()))

    def __repr__(self):
        return 'DefaultOrderedDict(%s, %s)' % (self.default_factory,
                                               OrderedDict.__repr__(self))


class _TempBool(object):
    """Wrapper around a boolean defining an __enter__ and __exit__ method

    Notes
    -----
    If you want to use this class as an instance property, rather use the
    :func:`_temp_bool_prop` because this class as a descriptor is ment to be a
    class descriptor"""

    #: default boolean value for the :attr:`value` attribute
    default = False

    #: boolean value indicating whether there shall be a validation or not
    value = False

    def __init__(self, default=False):
        """
        Parameters
        ----------
        default: bool
            value of the object"""
        self.default = default
        self.value = default
        self._entered = []

    def __enter__(self):
        self.value = not self.default
        self._entered.append(1)

    def __exit__(self, type, value, tb):
        self._entered.pop(-1)
        if not self._entered:
            self.value = self.default

    if six.PY2:
        def __nonzero__(self):
            return self.value
    else:
        def __bool__(self):
            return self.value

    def __repr__(self):
        return repr(bool(self))

    def __str__(self):
        return str(bool(self))

    def __call__(self, value=None):
        """
        Parameters
        ----------
        value: bool or None
            If None, the current value will be negated. Otherwise the current
            value of this instance is set to the given `value`"""
        if value is None:
            self.value = not self.value
        else:
            self.value = value

    def __get__(self, instance, owner):
        return self

    def __set__(self, instance, value):
        self.value = value


def _temp_bool_prop(propname, doc="", default=False):
    """Creates a property that uses the :class:`_TempBool` class

    Parameters
    ----------
    propname: str
        The attribute name to use. The _TempBool instance will be stored in the
        ``'_' + propname`` attribute of the corresponding instance
    doc: str
        The documentation of the property
    default: bool
        The default value of the _TempBool class"""
    def getx(self):
        if getattr(self, '_' + propname, None) is not None:
            return getattr(self, '_' + propname)
        else:
            setattr(self, '_' + propname, _TempBool(default))
        return getattr(self, '_' + propname)

    def setx(self, value):
        getattr(self, propname).value = bool(value)

    def delx(self):
        getattr(self, propname).value = default

    return property(getx, setx, delx, doc)


def unique_everseen(iterable, key=None):
    """List unique elements, preserving order. Remember all elements ever seen.

    Function taken from https://docs.python.org/2/library/itertools.html"""
    # unique_everseen('AAAABBBCCDAABBB') --> A B C D
    # unique_everseen('ABBCcAD', str.lower) --> A B C D
    seen = set()
    seen_add = seen.add
    if key is None:
        for element in filterfalse(seen.__contains__, iterable):
            seen_add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen_add(k)
                yield element


def is_remote_url(path):
    patt = re.compile(r'^https?\://')
    if not isinstance(path, six.string_types):
        return all(map(patt.search, (s or '' for s in path)))
    return bool(re.search(r'^https?\://', path))


@docstrings.get_sections(base='check_key', sections=['Parameters', 'Returns',
                                                 'Raises'])
@dedent
def check_key(key, possible_keys, raise_error=True,
              name='formatoption keyword',
              msg=("See show_fmtkeys function for possible formatopion "
                   "keywords"),
              *args, **kwargs):
    """
    Checks whether the key is in a list of possible keys

    This function checks whether the given `key` is in `possible_keys` and if
    not looks for similar sounding keys

    Parameters
    ----------
    key: str
        Key to check
    possible_keys: list of strings
        a list of possible keys to use
    raise_error: bool
        If not True, a list of similar keys is returned
    name: str
        The name of the key that shall be used in the error message
    msg: str
        The additional message that shall be used if no close match to
        key is found
    *args, **kwargs
        They are passed to the :func:`difflib.get_close_matches` function
        (i.e. `n` to increase the number of returned similar keys and
        `cutoff` to change the sensibility)

    Returns
    -------
    str
        The `key` if it is a valid string, else an empty string
    list
        A list of similar formatoption strings (if found)
    str
        An error message which includes

    Raises
    ------
    KeyError
        If the key is not a valid formatoption and `raise_error` is True"""
    if key not in possible_keys:
        similarkeys = get_close_matches(key, possible_keys, *args, **kwargs)
        if similarkeys:
            msg = ('Unknown %s %s! Possible similiar '
                   'frasings are %s.') % (name, key, ', '.join(similarkeys))
        else:
            msg = ("Unknown %s %s! ") % (name, key) + msg
        if not raise_error:
            return '', similarkeys, msg
        raise KeyError(msg)
    else:
        return key, [key], ''


def sort_kwargs(kwargs, *param_lists):
    """Function to sort keyword arguments and sort them into dictionaries

    This function returns dictionaries that contain the keyword arguments
    from `kwargs` corresponding given iterables in ``*params``

    Parameters
    ----------
    kwargs: dict
        Original dictionary
    ``*param_lists``
        iterables of strings, each standing for a possible key in kwargs

    Returns
    -------
    list
        len(params) + 1 dictionaries. Each dictionary contains the items of
        `kwargs` corresponding to the specified list in ``*param_lists``. The
        last dictionary contains the remaining items"""
    return chain(
        ({key: kwargs.pop(key) for key in params.intersection(kwargs)}
         for params in map(set, param_lists)), [kwargs])


def hashable(val):
    """Test if `val` is hashable and if not, get it's string representation

    Parameters
    ----------
    val: object
        Any (possibly not hashable) python object

    Returns
    -------
    val or string
        The given `val` if it is hashable or it's string representation"""
    if val is None:
        return val
    try:
        hash(val)
    except TypeError:
        return repr(val)
    else:
        return val


@docstrings.get_sections(base='join_dicts')
def join_dicts(dicts, delimiter=None, keep_all=False):
    """Join multiple dictionaries into one

    Parameters
    ----------
    dicts: list of dict
        A list of dictionaries
    delimiter: str
        The string that shall be used as the delimiter in case that there
        are multiple values for one attribute in the arrays. If None, they
        will be returned as sets
    keep_all: bool
        If True, all formatoptions are kept. Otherwise only the intersection

    Returns
    -------
    dict
        The combined dictionary"""
    if not dicts:
        return {}
    if keep_all:
        all_keys = set(chain(*(d.keys() for d in dicts)))
    else:
        all_keys = set(dicts[0])
        for d in dicts[1:]:
            all_keys.intersection_update(d)
    ret = {}
    for key in all_keys:
        vals = {hashable(d.get(key, None)) for d in dicts} - {None}
        if len(vals) == 1:
            ret[key] = next(iter(vals))
        elif delimiter is None:
            ret[key] = vals
        else:
            ret[key] = delimiter.join(map(str, vals))
    return ret


def is_iterable(iterable):
    """Test if an object is iterable

    Parameters
    ----------
    iterable: object
        The object to test

    Returns
    -------
    bool
        True, if the object is an iterable object"""
    try:
        iter(iterable)
    except TypeError:
        return False
    else:
        return True
