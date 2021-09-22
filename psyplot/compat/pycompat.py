"""Compatibility module for different python versions"""

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

import os
import six
import inspect

if six.PY3:

    class DictMethods(object):

        @staticmethod
        def iteritems(d):
            return iter(dict.items(d))

        @staticmethod
        def itervalues(d):
            return iter(dict.values(d))

        @staticmethod
        def iterkeys(d):
            return iter(dict.keys(d))

    def getcwd(*args, **kwargs):
        return os.getcwd(*args, **kwargs)

    def get_default_value(func, arg):
        argspec = inspect.getfullargspec(func)
        return next(default for a, default in zip(reversed(argspec[0]),
                                                  reversed(argspec.defaults))
                    if a == arg)

    basestring = str
    unicode_type = str
    bytes_type = bytes
    range = range
    zip = zip
    filter = filter
    map = map
    from functools import reduce
    from itertools import filterfalse
    import builtins
    from queue import Queue

elif six.PY2:
    # Python 2

    class DictMethods(object):
        """okay"""
        @staticmethod
        def iteritems(d):
            "checked"
            return dict.iteritems(d)

        @staticmethod
        def itervalues(d):
            return dict.itervalues(d)

        @staticmethod
        def iterkeys(d):
            return dict.iterkeys(d)

    def getcwd(*args, **kwargs):
        return os.getcwdu(*args, **kwargs)

    def get_default_value(func, arg):
        argspec = inspect.getargspec(func)
        return next(default for a, default in zip(reversed(argspec[0]),
                                                  reversed(argspec.defaults))
                    if a == arg)

    basestring = basestring
    unicode_type = unicode
    bytes_type = str
    range = xrange
    from itertools import (izip as zip, imap as map, ifilter as filter,
                           ifilterfalse as filterfalse)
    reduce = reduce
    import __builtin__ as builtins
    from Queue import Queue

try:
    from cyordereddict import OrderedDict
except ImportError:
    try:
        from collections import OrderedDict
    except ImportError:
        from ordereddict import OrderedDict

try:
    from collections import UserDict
except ImportError:
    from UserDict import IterableUserDict as UserDict


def isstring(s):
    return isinstance(s, six.string_types)
