"""Core package for interactive visualization in the psyplot package

This package defines the :class:`Plotter` and :class:`Formatoption` classes,
the core of the visualization in the :mod:`psyplot` package. Each
:class:`Plotter` combines a set of formatoption keys where each formatoption
key is represented by a :class:`Formatoption` subclass."""

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

import six
import weakref
from abc import ABCMeta, abstractmethod
from textwrap import TextWrapper
import logging
from itertools import chain, groupby, tee, repeat, starmap
from collections import defaultdict
from threading import RLock
from datetime import datetime, timedelta
from numpy import datetime64, timedelta64, ndarray, inf
from xarray.core.formatting import format_timestamp, format_timedelta
from psyplot import rcParams
from psyplot.warning import warn, critical, PsyPlotRuntimeWarning
from psyplot.compat.pycompat import map, filter, zip, range
from psyplot.config.rcsetup import SubDict
from psyplot.docstring import docstrings, dedent
from psyplot.data import (
    InteractiveList, _no_auto_update_getter, CFDecoder)
from psyplot.utils import (DefaultOrderedDict, _TempBool, _temp_bool_prop,
                           unique_everseen, check_key)

#: the default function to use when printing formatoption infos (the default is
#: use print or in the gui, use the help explorer)
default_print_func = six.print_


#: :class:`dict`. Mapping from group to group names
groups = {
    'data': 'Data manipulation formatoptions',
    'axes': 'Axes formatoptions',
    'labels': 'Label formatoptions',
    'plotting': 'Plot formatoptions',
    'post_processing': 'Post processing formatoptions',
    'colors': 'Color coding formatoptions',
    'misc': 'Miscallaneous formatoptions',
    'ticks': 'Axis tick formatoptions',
    'vector': 'Vector plot formatoptions',
    'masking': 'Masking formatoptions',
    'regression': 'Fitting formatoptions',
    }


def _identity(*args):
    """identity function to make no validation

    Returns
    -------
    object
        just return the last argument in ``*args``"""
    return args[-1]


def format_time(x):
    """Formats date values

    This function formats :class:`datetime.datetime` and
    :class:`datetime.timedelta` objects (and the corresponding numpy objects)
    using the :func:`xarray.core.formatting.format_timestamp` and the
    :func:`xarray.core.formatting.format_timedelta` functions.

    Parameters
    ----------
    x: object
        The value to format. If not a time object, the value is returned

    Returns
    -------
    str or `x`
        Either the formatted time object or the initial `x`"""
    if isinstance(x, (datetime64, datetime)):
        return format_timestamp(x)
    elif isinstance(x, (timedelta64, timedelta)):
        return format_timedelta(x)
    elif isinstance(x, ndarray):
        return list(x) if x.ndim else x[()]
    return x


def is_data_dependent(fmto, data):
    """Check whether a formatoption is data dependent

    Parameters
    ----------
    fmto: Formatoption
        The :class:`Formatoption` instance to check
    data: xarray.DataArray
        The data array to use if the :attr:`~Formatoption.data_dependent`
        attribute is a callable

    Returns
    -------
    bool
        True, if the formatoption depends on the data"""
    if callable(fmto.data_dependent):
        return fmto.data_dependent(data)
    return fmto.data_dependent


def _child_property(childname):
    def get_x(self):
        return getattr(self.plotter, self._child_mapping[childname])

    return property(
        get_x, doc=childname + " Formatoption instance in the plotter")


class FormatoptionMeta(ABCMeta):
    """Meta class for formatoptions

    This class serves as a meta class for formatoptions and allows a more
    efficient docstring generation by using the
    :attr:`psyplot.docstring.docstrings` when creating a new formatoption
    class"""
    def __new__(cls, clsname, bases, dct):
        """Assign an automatic documentation to the formatoption"""
        doc = dct.get('__doc__')
        if doc is not None:
            dct['__doc__'] = docstrings.dedent(doc)
        new_cls = super(FormatoptionMeta, cls).__new__(cls, clsname, bases,
                                                       dct)
        for childname in chain(new_cls.children, new_cls.dependencies,
                               new_cls.connections, new_cls.parents):
            setattr(new_cls, childname, _child_property(childname))
        if new_cls.plot_fmt:
            new_cls.data_dependent = True
        return new_cls


# priority values

#: Priority value of formatoptions that are updated before the data is loaded.
START = 30
#: Priority value of formatoptions that are updated before the plot it made.
BEFOREPLOTTING = 20
#: Priority value of formatoptions that are updated at the end.
END = 10


@six.add_metaclass(FormatoptionMeta)
class Formatoption(object):
    """Abstract formatoption

    This class serves as an abstract version of an formatoption descriptor
    that can be used by :class:`~psyplot.plotter.Plotter` instances."""

    priority = END
    """:class:`int`. Priority value of the the formatoption determining when
    the formatoption is updated.

    - 10: at the end (for labels, etc.)
    - 20: before the plotting (e.g. for colormaps, etc.)
    - 30: before loading the data (e.g. for lonlatbox)"""

    #: :class:`str`. Formatoption key of this class in the
    #: :class:`~psyplot.plotter.Plotter` class
    key = None

    _plotter = None

    @property
    def plotter(self):
        """:class:`~psyplot.plotter.Plotter`. Plotter instance this
        formatoption belongs to"""
        if self._plotter is None:
            return
        return self._plotter()

    @plotter.setter
    def plotter(self, value):
        if value is not None:
            self._plotter = weakref.ref(value)
        else:
            self._plotter = value

    #: `list of str`. List of formatoptions that have to be updated before this
    #: one is updated. Those formatoptions are only updated if they exist in
    #: the update parameters.
    children = []

    #: `list of str`. List of formatoptions that force an update of this
    #: formatoption if they are updated.
    dependencies = []

    #: `list of str`. Connections to other formatoptions that are (different
    #: from :attr:`dependencies` and :attr:`children`) not important for the
    #: update process
    connections = []

    #: `list of str`. List of formatoptions that, if included in the update,
    #: prevent the update of this formatoption.
    parents = []

    #: :class:`bool`. Has to be True if the formatoption has a ``make_plot``
    #: method to make the plot.
    plot_fmt = False

    #: :class:`bool`. True if an update of this formatoption requires a
    #: clearing of the axes and reinitialization of the plot
    requires_clearing = False

    #: :class:`str`. Key of the group name in :data:`groups` of this
    #: formatoption keyword
    group = 'misc'

    #: :class:`bool` or a callable. This attribute indicates whether this
    #: :class:`Formatoption` depends on the data and should be updated if the
    #: data changes. If it is a callable, it must accept one argument: the
    #: new data. (Note: This is automatically set to True for plot
    #: formatoptions)
    data_dependent = False

    #: :class:`bool`. True if this formatoption needs an update after the plot
    #: has changed
    update_after_plot = False

    #: :class:`set` of the :class:`Formatoption` instance that are shared
    #: with this instance.
    shared = set()

    #: int or None. Index that is used in case the plotting data is a
    #: :class:`psyplot.InteractiveList`
    index_in_list = 0

    #: :class:`str`. A bit more verbose name than the formatoption key to be
    #: included in the gui. If None, the key is used in the gui
    name = None

    #: Boolean that is True if an update of the formatoption requires a replot
    requires_replot = False

    @property
    def init_kwargs(self):
        """:class:`dict` key word arguments that are passed to the
        initialization of a new instance when accessed from the descriptor"""
        return self._child_mapping

    @property
    def project(self):
        """Project of the plotter of this instance"""
        return self.plotter.project

    @property
    def ax(self):
        """The axes this Formatoption plots on"""
        return self.plotter.ax

    @property
    def lock(self):
        """A :class:`threading.Rlock` instance to lock while updating

        This lock is used when multiple :class:`plotter` instances are
        updated at the same time while sharing formatoptions."""
        try:
            return self._lock
        except AttributeError:
            self._lock = RLock()
            return self._lock

    @property
    def logger(self):
        """Logger of the plotter"""
        return self.plotter.logger.getChild(self.key)

    @property
    def groupname(self):
        """Long name of the group this formatoption belongs too."""
        try:
            return groups[self.group]
        except KeyError:
            warn("Unknown formatoption group " + str(self.group),
                 PsyPlotRuntimeWarning)
            return self.group

    @property
    def raw_data(self):
        """The original data of the plotter of this formatoption"""
        if self.index_in_list is not None and isinstance(
                self.plotter.data, InteractiveList):
            return self.plotter.data[self.index_in_list]
        else:
            return self.plotter.data

    @property
    def decoder(self):
        """The :class:`~psyplot.data.CFDecoder` instance that decodes the
        :attr:`raw_data`"""
        # If the decoder is modified by one of the formatoptions, use this one
        if self.plotter.plot_data_decoder is not None:
            if self.index_in_list is not None and isinstance(
                    self.plotter.plot_data, InteractiveList):
                ret = self.plotter.plot_data_decoder[self.index_in_list]
                if ret is not None:
                    return ret
            else:
                return self.plotter.plot_data_decoder
        data = self.raw_data
        check = isinstance(data, InteractiveList)
        while check:
            data = data[0]
            check = isinstance(data, InteractiveList)
        return data.psy.decoder

    @decoder.setter
    def decoder(self, value):
        self.set_decoder(value, self.index_in_list)

    @property
    def any_decoder(self):
        """Return the first possible decoder"""
        ret = self.decoder
        while not isinstance(ret, CFDecoder):
            ret = ret[0]
        return ret

    @property
    def data(self):
        """The data that is plotted"""
        if self.index_in_list is not None and isinstance(
                self.plotter.plot_data, InteractiveList):
            return self.plotter.plot_data[self.index_in_list]
        else:
            return self.plotter.plot_data

    @data.setter
    def data(self, value):
        self.set_data(value, self.index_in_list)

    @property
    def iter_data(self):
        """Returns an iterator over the plot data arrays"""
        data = self.data
        if isinstance(data, InteractiveList):
            return iter(data)
        return iter([data])

    @property
    def iter_raw_data(self):
        """Returns an iterator over the original data arrays"""
        data = self.raw_data
        if isinstance(data, InteractiveList):
            return iter(data)
        return iter([data])

    @property
    def validate(self):
        """Validation method of the formatoption"""
        try:
            return self._validate
        except AttributeError:
            try:
                self._validate = self.plotter.get_vfunc(self.key)
            except KeyError:
                warn("Could not find a validation function for %s "
                     "formatoption keyword! No validation will be made!" % (
                         self.key), PsyPlotRuntimeWarning, logger=self.logger)
                self._validate = _identity
        return self._validate

    @validate.setter
    def validate(self, value):
        self._validate = value

    @property
    def default(self):
        """Default value of this formatoption"""
        return self.plotter.rc[self.key]

    @property
    def default_key(self):
        """The key of this formatoption in the :attr:`psyplot.rcParams`"""
        return self.plotter.rc._get_val_and_base(self.key)[0]

    @property
    def shared_by(self):
        """None if the formatoption is not controlled by another formatoption
        of another plotter, otherwise the corresponding :class:`Formatoption`
        instance"""
        return self.plotter._shared.get(self.key)

    @property
    def value(self):
        """Value of the formatoption in the corresponding :attr:`plotter` or
        the shared value"""
        shared_by = self.shared_by
        if shared_by:
            return shared_by.value2share
        return self.plotter[self.key]

    @property
    @dedent
    def changed(self):
        """
        :class:`bool` indicating whether the value changed compared to the
        default or not."""
        return self.diff(self.default)

    @property
    @dedent
    def value2share(self):
        """
        The value that is passed to shared formatoptions (by default, the
        :attr:`value` attribute)"""
        return self.value

    @property
    @dedent
    def value2pickle(self):
        """
        The value that can be used when pickling the information of the project
        """
        return self.value

    @docstrings.get_sections(base='Formatoption')
    @dedent
    def __init__(self, key, plotter=None, index_in_list=None,
                 additional_children=[], additional_dependencies=[],
                 **kwargs):
        """
        Parameters
        ----------
        key: str
            formatoption key in the `plotter`
        plotter: psyplot.plotter.Plotter
            Plotter instance that holds this formatoption. If None, it is
            assumed that this instance serves as a descriptor.
        index_in_list: int or None
            The index that shall be used if the data is a
            :class:`psyplot.InteractiveList`
        additional_children: list or str
            Additional children to use (see the :attr:`children` attribute)
        additional_dependencies: list or str
            Additional dependencies to use (see the :attr:`dependencies`
            attribute)
        ``**kwargs``
            Further keywords may be used to specify different names for
            children, dependencies and connection formatoptions that match the
            setup of the plotter. Hence, keywords may be anything of the
            :attr:`children`, :attr:`dependencies` and :attr:`connections`
            attributes, with values being the name of the new formatoption in
            this plotter."""
        self.key = key
        self.plotter = plotter
        self.index_in_list = index_in_list
        self.shared = set()
        self.additional_children = additional_children
        self.additional_dependencies = additional_dependencies
        self.children = self.children + additional_children
        self.dependencies = self.dependencies + additional_dependencies
        self._child_mapping = dict(zip(*tee(chain(
            self.children, self.dependencies, self.connections,
            self.parents), 2)))
        # check kwargs
        for key in (key for key in kwargs if key not in self._child_mapping):
            raise TypeError(
                '%s.__init__() got an unexpected keyword argument %r' % (
                    self.__class__.__name__, key))
        # set up child mapping
        self._child_mapping.update(kwargs)
        # reset the dependency lists to match the current plotter setup
        for attr in ['children', 'dependencies', 'connections', 'parents']:
            setattr(self, attr,
                    [self._child_mapping[key] for key in getattr(self, attr)])

    def __set__(self, instance, value):
        if isinstance(value, Formatoption):
            setattr(instance, '_' + self.key, value)
        else:
            fmto = getattr(instance, self.key)
            fmto.set_value(value)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        try:
            return getattr(instance, '_' + self.key)
        except AttributeError:
            fmto = self.__class__(
                self.key, instance, self.index_in_list,
                additional_children=self.additional_children,
                additional_dependencies=self.additional_dependencies,
                **self.init_kwargs)
            setattr(instance, '_' + self.key, fmto)
            return fmto

    def __delete__(self, instance, owner):
        fmto = getattr(instance, '_' + self.key)
        with instance.no_validation:
            instance[self.key] = fmto.default

    @docstrings.get_sections(base='Formatoption.set_value')
    @dedent
    def set_value(self, value, validate=True, todefault=False):
        """
        Set (and validate) the value in the plotter. This method is called by
        the plotter when it attempts to change the value of the formatoption.

        Parameters
        ----------
        value
            Value to set
        validate: bool
            if True, validate the `value` before it is set
        todefault: bool
            True if the value is updated to the default value"""
        # do nothing if the key is shared
        if self.key in self.plotter._shared:
            return
        with self.plotter.no_validation:
            self.plotter[self.key] = value if not validate else \
                self.validate(value)

    def set_data(self, data, i=None):
        """
        Replace the data to plot

        This method may be used to replace the data that is visualized by the
        plotter. It changes it's behaviour depending on whether an
        :class:`psyplot.data.InteractiveList` is visualized or a single
        :class:`pysplot.data.InteractiveArray`

        Parameters
        ----------
        data: psyplot.data.InteractiveBase
            The data to insert
        i: int
            The position in the InteractiveList where to insert the data (if
            the plotter visualizes a list anyway)

        Notes
        -----
        This method uses the :attr:`Formatoption.data` attribute
        """
        if self.index_in_list is not None:
            i = self.index_in_list
        if i is not None and isinstance(self.plotter.plot_data,
                                        InteractiveList):
            self.plotter.plot_data[i] = data
        else:
            self.plotter.plot_data = data

    def set_decoder(self, decoder, i=None):
        """
        Replace the data to plot

        This method may be used to replace the data that is visualized by the
        plotter. It changes it's behaviour depending on whether an
        :class:`psyplot.data.InteractiveList` is visualized or a single
        :class:`pysplot.data.InteractiveArray`

        Parameters
        ----------
        decoder: psyplot.data.CFDecoder
            The decoder to insert
        i: int
            The position in the InteractiveList where to insert the data (if
            the plotter visualizes a list anyway)
        """
        # we do not modify the raw data but instead set it on the plotter
        # TODO: This is not safe for encapsulated InteractiveList instances!
        if i is not None and isinstance(
                self.plotter.plot_data, InteractiveList):
            n = len(self.plotter.plot_data)
            decoders = self.plotter.plot_data_decoder or [None] * n
            decoders[i] = decoder
            self.plotter.plot_data_decoder = decoders
        else:
            if (isinstance(self.plotter.plot_data, InteractiveList) and
                    isinstance(decoder, CFDecoder)):
                decoder = [decoder] * len(self.plotter.plot_data)
            self.plotter.plot_data_decoder = decoder

    def get_decoder(self, i=None):
        # we do not modify the raw data but instead set it on the plotter
        # TODO: This is not safe for encapsulated InteractiveList instances!
        if i is not None and isinstance(
                self.plotter.plot_data, InteractiveList):
            n = len(self.plotter.plot_data)
            decoders = self.plotter.plot_data_decoder or [None] * n
            return decoders[i] or self.plotter.plot_data[i].psy.decoder
        else:
            return self.decoder

    def check_and_set(self, value, todefault=False, validate=True):
        """Checks the value and sets the value if it changed

        This method checks the value and sets it only if the :meth:`diff`
        method result of the given `value` is True

        Parameters
        ----------
        value
            A possible value to set
        todefault: bool
            True if the value is updated to the default value

        Returns
        -------
        bool
            A boolean to indicate whether it has been set or not"""
        if validate:
            value = self.validate(value)
        if self.diff(value):
            self.set_value(value, validate=False, todefault=todefault)
            return True
        return False

    def diff(self, value):
        """Checks whether the given value differs from what is currently set

        Parameters
        ----------
        value
            A possible value to set (make sure that it has been validate via
            the :attr:`validate` attribute before)

        Returns
        -------
        bool
            True if the value differs from what is currently set"""
        return value != self.value

    def initialize_plot(self, value, *args, **kwargs):
        """Method that is called when the plot is made the first time

        Parameters
        ----------
        value
            The value to use for the initialization"""
        self.update(value, *args, **kwargs)

    @abstractmethod
    def update(self, value):
        """Method that is call to update the formatoption on the axes

        Parameters
        ----------
        value
            Value to update"""
        pass

    def get_fmt_widget(self, parent, project):
        """Get a widget to update the formatoption in the GUI

        This method should return a QWidget that is loaded by the psyplot-gui
        when the formatoption is selected in the
        :attr:`psyplot_gui.main.Mainwindow.fmt_widget`. It should call the
        :meth:`~psyplot_gui.fmt_widget.FormatoptionWidget.insert_text` method
        when the update text for the formatoption should be changed.

        Parameters
        ----------
        parent: psyplot_gui.fmt_widget.FormatoptionWidget
            The parent widget that contains the returned QWidget
        project: psyplot.project.Project
            The current subproject (see :func:`psyplot.project.gcp`)

        Returns
        -------
        PyQt5.QtWidgets.QWidget
            The widget to control the formatoption"""
        return None

    def share(self, fmto, initializing=False, **kwargs):
        """Share the settings of this formatoption with other data objects

        Parameters
        ----------
        fmto: Formatoption
            The :class:`Formatoption` instance to share the attributes with
        ``**kwargs``
            Any other keyword argument that shall be passed to the update
            method of `fmto`"""
        # lock all  the childrens and the formatoption itself
        self.lock.acquire()
        fmto._lock_children()
        fmto.lock.acquire()
        # update the other plotter
        if initializing:
            fmto.initialize_plot(self.value2share, **kwargs)
        else:
            fmto.update(self.value2share, **kwargs)
        self.shared.add(fmto)
        # release the locks
        fmto.lock.release()
        fmto._release_children()
        self.lock.release()

    def _lock_children(self):
        """acquire the locks of the children"""
        plotter = self.plotter
        for key in self.children + self.dependencies:
            try:
                getattr(plotter, key).lock.acquire()
            except AttributeError:
                pass

    def _release_children(self):
        """release the locks of the children"""
        plotter = self.plotter
        for key in self.children + self.dependencies:
            try:
                getattr(plotter, key).lock.release()
            except AttributeError:
                pass

    def finish_update(self):
        """Finish the update, initialization and sharing process

        This function is called at the end of the :meth:`Plotter.start_update`,
        :meth:`Plotter.initialize_plot` or the :meth:`Plotter.share` methods.
        """
        pass

    @dedent
    def remove(self):
        """
        Method to remove the effects of this formatoption

        This method is called when the axes is cleared due to a
        formatoption with :attr:`requires_clearing` set to True. You don't
        necessarily have to implement this formatoption if your plot results
        are removed by the usual :meth:`matplotlib.axes.Axes.clear` method."""
        pass

    @docstrings.get_extended_summary(base="Formatoption.convert_coordinate")
    @docstrings.get_sections(
        base="Formatoption.convert_coordinate",
        sections=["Parameters", "Returns"]
    )
    def convert_coordinate(self, coord, *variables):
        """Convert a coordinate to units necessary for the plot.

        This method takes a single coordinate variable (e.g. the `bounds` of a
        coordinate, or the coordinate itself) and transforms the units that the
        plotter requires.

        One might also provide additional `variables` that are supposed to be
        on the same unit, in case the given `coord` does not specify a `units`
        attribute. `coord` might be a CF-conform `bounds` variable, and one of
        the variables might be the corresponding `coordinate`.

        Parameters
        ----------
        coord: xr.Variable
            The variable to transform
        ``*variables``
            The variables that are on the same unit as `coord`

        Returns
        -------
        xr.Variable
            The transformed `coord`

        Notes
        -----
        By default, this method uses the :meth:`~Plotter.convert_coordinate`
        method of the :attr:`plotter`.
        """
        return self.plotter.convert_coordinate(coord, *variables)


class DictFormatoption(Formatoption):
    """
    Base formatoption class defining an alternative set_value that works for
    dictionaries."""

    @docstrings.dedent
    def set_value(self, value, validate=True, todefault=False):
        """
        Set (and validate) the value in the plotter

        Parameters
        ----------
        %(Formatoption.set_value.parameters)s

        Notes
        -----
        - If the current value in the plotter is None, then it will be set with
          the given `value`, otherwise the current value in the plotter is
          updated
        - If the value is an empty dictionary, the value in the plotter is
          cleared"""
        value = value if not validate else self.validate(value)
        # if the key in the plotter is not already set (i.e. it is initialized
        # with None, we set it)
        if self.plotter[self.key] is None:
            with self.plotter.no_validation:
                self.plotter[self.key] = value.copy()
        # in case of an empty dict, clear the value
        elif not value:
            self.plotter[self.key].clear()
        # otherwhise we update the dictionary
        else:
            if todefault:
                self.plotter[self.key].clear()
            self.plotter[self.key].update(value)


class PostTiming(Formatoption):
    """
    Determine when to run the :attr:`post` formatoption

    This formatoption determines, whether the :attr:`post` formatoption
    should be run never, after replot or after every update.

    Possible types
    --------------
    'never'
        Never run post processing scripts
    'always'
        Always run post processing scripts
    'replot'
        Only run post processing scripts when the data changes or a replot
        is necessary

    See Also
    --------
    post: The post processing formatoption"""

    default = 'never'

    priority = -inf

    group = 'post_processing'

    name = 'Timing of the post processing'

    @staticmethod
    def validate(value):
        value = six.text_type(value)
        possible_values = ['never', 'always', 'replot']
        if value not in possible_values:
            raise ValueError('String must be one of %s, not %r' % (
                possible_values, value))
        return value

    def update(self, value):
        pass

    def get_fmt_widget(self, parent, project):
        from psyplot_gui.compat.qtcompat import QComboBox
        combo = QComboBox(parent)
        combo.addItems(['never', 'always', 'replot'])
        combo.setCurrentText(
            next((plotter[self.key] for plotter in project.plotters), 'never'))
        combo.currentTextChanged.connect(parent.set_obj)
        return combo


class PostProcDependencies(object):
    """The dependencies of this formatoption"""

    def __get__(self, instance, owner):
        if (instance is None or instance.plotter is None or
                not instance.plotter._initialized):
            return []
        elif instance.post_timing.value == 'always':
            return list(set(instance.plotter) - {instance.key})
        else:
            return []

    def __set__(self, instance, value):
        pass


class PostProcessing(Formatoption):
    """
    Apply your own postprocessing script

    This formatoption let's you apply your own post processing script. Just
    enter the script as a string and it will be executed. The formatoption
    will be made available via the ``self`` variable

    Possible types
    --------------
    None
        Don't do anything
    str
        The post processing script as string

    Note
    ----
    This formatoption uses the built-in :func:`exec` function to compile the
    script. Since this poses a security risk when loading psyplot projects,
    it is by default disabled through the :attr:`Plotter.enable_post`
    attribute. If you are sure that you can trust the script in this
    formatoption, set this attribute of the corresponding :class:`Plotter` to
    ``True``

    Examples
    --------
    Assume, you want to manually add the mean of the data to the title of the
    matplotlib axes. You can simply do this via

    .. code-block:: python

        from psyplot.plotter import Plotter
        from xarray import DataArray
        plotter = Plotter(DataArray([1, 2, 3]))
        # enable the post formatoption
        plotter.enable_post = True
        plotter.update(post="self.ax.set_title(str(self.data.mean()))")
        plotter.ax.get_title()
        '2.0'

    By default, the ``post`` formatoption is only ran, when it is explicitly
    updated. However, you can use the :attr:`post_timing` formatoption, to
    run it automatically. E.g. for running it after every update of the
    plotter, you can set

    .. code-block:: python

        plotter.update(post_timing='always')

    See Also
    --------
    post_timing: Determine the timing of this formatoption"""

    children = ['post_timing']

    default = None

    priority = -inf

    group = 'post_processing'

    name = 'Custom post processing script'

    @staticmethod
    def validate(value):
        if value is None:
            return value
        elif not isinstance(value, six.string_types):
            raise ValueError("Expected a string, not %s" % (type(value), ))
        else:
            return six.text_type(value)

    @property
    def data_dependent(self):
        """True if the corresponding :class:`post_timing <PostTiming>`
        formatoption is set to ``'replot'`` to run the post processing script
        after every change of the data"""
        return self.post_timing.value == 'replot'

    dependencies = PostProcDependencies()

    def update(self, value):
        if value is None:
            return
        if not self.plotter.enable_post:
            warn(
                "Post processing is disabled. Set the ``enable_post`` "
                "attribute to True to run the script")
        else:
            exec(value, {'self': self})


class Plotter(dict):
    """Interactive plotting object for one or more data arrays

    This class is the base for the interactive plotting with the psyplot
    module. It capabilities are determined by it's descriptor classes that are
    derived from the :class:`Formatoption` class"""

    #: List of base strings in the :attr:`psyplot.rcParams` dictionary
    _rcparams_string = []

    post_timing = PostTiming('post_timing')
    post = PostProcessing('post')

    no_validation = _temp_bool_prop('no_validation', """
        Temporarily disable the validation

        Examples
        --------
        Although it is not recommended to set a value with disabled validation,
        you can disable it via::

            >>> with plotter.no_validation:
            ...     plotter['ticksize'] = 'x'

        To permanently disable the validation, simply set

            >>> plotter.no_validation = True
            >>> plotter['ticksize'] = 'x'
            >>> plotter.no_validation = False  # reenable validation""")

    #: Temporarily include links in the key descriptions from
    #: :meth:`show_keys`, :meth:`show_docs` and :meth:`show_summaries`.
    #: Note that this is a class attribute, so each change to the value of this
    #: attribute will affect all instances and subclasses
    include_links = _TempBool()

    @property
    def ax(self):
        """Axes instance of the plot"""
        if self._ax is None:
            import matplotlib.pyplot as plt
            plt.figure()
            self._ax = plt.axes(projection=self._get_sample_projection())
        return self._ax

    @ax.setter
    def ax(self, value):
        self._ax = value

    #: The :class:`psyplot.project.Project` instance this plotter belongs to
    _project = None

    @property
    def project(self):
        """:class:`psyplot.project.Project` instance this plotter belongs to"""
        if self._project is None:
            return
        return self._project()

    @project.setter
    def project(self, value):
        if value is not None:
            self._project = weakref.ref(value)
        else:
            self._project = value

    @property
    @dedent
    def rc(self):
        """
        Default values for this plotter

        This :class:`~psyplot.config.rcsetup.SubDict` stores the default values
        for this plotter. A modification of the dictionary does not affect
        other plotter instances unless you set the
        :attr:`~psyplot.config.rcsetup.SubDict.trace` attribute to True"""
        try:
            return self._rc
        except AttributeError:
            self._set_rc()
            return self._rc

    @property
    def base_variables(self):
        """A mapping from the base_variable names to the variables"""
        if isinstance(self.data, InteractiveList):
            return dict(chain(*map(
                lambda arr: six.iteritems(arr.psy.base_variables),
                self.data)))
        else:
            return self.data.psy.base_variables

    @property
    def iter_base_variables(self):
        """A mapping from the base_variable names to the variables"""
        if isinstance(self.data, InteractiveList):
            return chain(*(arr.psy.iter_base_variables for arr in self.data))
        else:
            return self.data.psy.iter_base_variables

    no_auto_update = property(_no_auto_update_getter,
                              doc=_no_auto_update_getter.__doc__)

    @no_auto_update.setter
    def no_auto_update(self, value):
        self.no_auto_update.value = bool(value)

    @property
    def changed(self):
        """:class:`dict` containing the key value pairs that are not the
        default"""
        return {key: value for key, value in six.iteritems(self)
                if getattr(self, key).changed}

    @property
    def figs2draw(self):
        """All figures that have been manipulated through sharing and the own
        figure.

        Notes
        -----
        Using this property set will reset the figures too draw"""
        return self._figs2draw.union([self.ax.get_figure()])

    @property
    @docstrings
    def _njobs(self):
        """%(InteractiveBase._njobs)s"""
        if self.disabled:
            return [0]
        return [1, 1]

    @property
    def _fmtos(self):
        """Iterator over the formatoptions"""
        return (getattr(self, key) for key in self)

    @property
    def _fmto_groups(self):
        """Mapping from group to a set of formatoptions"""
        ret = defaultdict(set)
        for key in self:
            ret[getattr(self, key).group].add(getattr(self, key))
        return dict(ret)

    @property
    def fmt_groups(self):
        """A mapping from the formatoption group to the formatoptions"""
        ret = defaultdict(set)
        for key in self:
            ret[getattr(self, key).group].add(key)
        return dict(ret)

    @property
    def groups(self):
        """A mapping from the group short name to the group description"""
        return {group: groups[group] for group in self.fmt_groups}

    @property
    def data(self):
        """The :class:`psyplot.InteractiveBase` instance of this plotter"""
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    @property
    def plot_data(self):
        """The data that is used for plotting"""
        return getattr(self, '_plot_data', self.data)

    @plot_data.setter
    def plot_data(self, value):
        self._set_data(value)

    #: The decoder to use for the formatoptions. If None, the decoder of the
    #: raw data is used
    plot_data_decoder = None

    #: :class:`bool` that has to be ``True`` if the post processing script in
    #: the :attr:`post` formatoption should be enabled
    enable_post = False

    def _set_data(self, value):
        if isinstance(value, InteractiveList):
            self._plot_data = value.copy()
        else:
            self._plot_data = value

    @property
    def logger(self):
        """:class:`logging.Logger` of this plotter"""
        try:
            return self.data.psy.logger.getChild(self.__class__.__name__)
        except AttributeError:
            name = '%s.%s' % (self.__module__, self.__class__.__name__)
            return logging.getLogger(name)

    docstrings.keep_params('InteractiveBase.parameters', 'auto_update')

    @docstrings.get_sections(base='Plotter')
    @docstrings.dedent
    def __init__(self, data=None, ax=None, auto_update=None, project=None,
                 draw=False, make_plot=True, clear=False,
                 enable_post=False, **kwargs):
        """
        Parameters
        ----------
        data: InteractiveArray or ArrayList, optional
            Data object that shall be visualized. If given and `plot` is True,
            the :meth:`initialize_plot` method is called at the end. Otherwise
            you can call this method later by yourself
        ax: matplotlib.axes.Axes
            Matplotlib Axes to plot on. If None, a new one will be created as
            soon as the :meth:`initialize_plot` method is called
        %(InteractiveBase.parameters.auto_update)s
        %(InteractiveBase.start_update.parameters.draw)s
        make_plot: bool
            If True, and `data` is not None, the plot is initialized. Otherwise
            only the framework between plotter and data is set up
        clear: bool
            If True, the axes is cleared first
        enable_post: bool
            If True, the :attr:`post` formatoption is enabled and post
            processing scripts are allowed
        ``**kwargs``
            Any formatoption key from the :attr:`formatoptions` attribute that
            shall be used"""
        self.project = project
        self.ax = ax
        self.data = data
        self.enable_post = enable_post
        if auto_update is None:
            auto_update = rcParams['lists.auto_update']
        self.no_auto_update = not bool(auto_update)
        self._registered_updates = {}
        self._todefault = False
        self._old_fmt = []
        self._figs2draw = set()
        #: formatoptions that have to be updated by other plotters that share
        #: the given formatoption with this Plotter. :attr:`_to_update` is a
        #: mapping from the formatoptions in this plotter to the corresponding
        #: other plotter
        self._to_update = {}
        self.disabled = False
        #: Dictionary holding the Formatoption instances of other plotters
        #: if their value shall be used instead of the one in this instance
        self._shared = {}
        #: list of str. Formatoption keys that were changed during the last
        #: update
        self._last_update = []
        #: The set of formatoptions that shall be updated even if they did not
        #: change
        self._force = set()
        self.replot = True
        self.cleared = clear
        self._updating = False
        # will be set to True when the plot is first initialized
        self._initialized = False

        # first we initialize all keys with None. This is necessary in order
        # to make the validation functioning
        with self.no_validation:
            for key in self._get_formatoptions():
                self[key] = None
        for key in self:  # then we set the default values
            fmto = getattr(self, key)
            self._try2set(fmto, fmto.default, validate=False)
        self._set_rc()
        for key, value in six.iteritems(kwargs):  # then the user values
            self[key] = value
        self.initialize_plot(data, ax=ax, draw=draw, clear=clear,
                             make_plot=make_plot)

    def _try2set(self, fmto, *args, **kwargs):
        """Sets the value in `fmto` and gives additional informations when fail

        Parameters
        ----------
        fmto: Formatoption
        ``*args`` and ``**kwargs``
            Anything that is passed to `fmto`s :meth:`~Formatoption.set_value`
            method"""
        fmto.set_value(*args, **kwargs)

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            self.check_key(key)

    def __setitem__(self, key, value):
        if not self.no_validation:
            self.check_key(key)
            self._try2set(getattr(self, key), value)
            return
        # prevent from setting during an update process
        getattr(self, key).lock.acquire()
        dict.__setitem__(self, key, value)
        getattr(self, key).lock.release()

    def __delitem__(self, key):
        self[key] = getattr(self, key).default

    docstrings.delete_params('check_key.parameters', 'possible_keys', 'name')

    @docstrings.dedent
    def check_key(self, key, raise_error=True, *args, **kwargs):
        """
        Checks whether the key is a valid formatoption

        Parameters
        ----------
        %(check_key.parameters.no_possible_keys|name)s

        Returns
        -------
        %(check_key.returns)s

        Raises
        ------
        %(check_key.raises)s"""
        return check_key(
            key, possible_keys=list(self), raise_error=raise_error,
            name='formatoption keyword', *args, **kwargs)

    @classmethod
    @docstrings.get_sections(base='Plotter.check_data', sections=['Parameters',
                                                              'Returns'])
    @dedent
    def check_data(cls, name, dims, is_unstructured):
        """
        A validation method for the data shape

        The default method does nothing and should be subclassed to validate
        the results. If the plotter accepts a :class:`InteractiveList`, it
        should accept a list for name and dims

        Parameters
        ----------
        name: str or list of str
            The variable name(s) of the data
        dims: list of str or list of lists of str
            The dimension name(s) of the data
        is_unstructured: bool or list of bool
            True if the corresponding array is unstructured

        Returns
        -------
        list of bool or None
            True, if everything is okay, False in case of a serious error,
            None if it is intermediate. Each object in this list corresponds to
            one in the given `name`
        list of str
            The message giving more information on the reason. Each object in
            this list corresponds to one in the given `name`"""
        if isinstance(name, six.string_types):
            name = [name]
            dims = [dims]
            is_unstructured = [is_unstructured]
        N = len(name)
        if len(dims) != N or len(is_unstructured) != N:
            return [False] * N, [
                'Number of provided names (%i) and dimensions '
                '(%i) or unstructured information (%i) are not the same' % (
                    N, len(dims), len(is_unstructured))] * N
        return [True] * N, [''] * N

    docstrings.keep_params('Plotter.parameters', 'ax', 'make_plot', 'clear')

    @docstrings.dedent
    def initialize_plot(self, data=None, ax=None, make_plot=True, clear=False,
                        draw=False, remove=False, priority=None):
        """
        Initialize the plot for a data array

        Parameters
        ----------
        data: InteractiveArray or ArrayList, optional
            Data object that shall be visualized.

            - If not None and `plot` is True, the given data is visualized.
            - If None and the :attr:`data` attribute is not None, the data in
              the :attr:`data` attribute is visualized
            - If both are None, nothing is done.
        %(Plotter.parameters.ax|make_plot|clear)s
        %(InteractiveBase.start_update.parameters.draw)s
        remove: bool
            If True, old effects by the formatoptions in this plotter are
            undone first
        priority: int
            If given, initialize only the formatoption with the given priority.
            This value must be out of :data:`START`, :data:`BEFOREPLOTTING` or
            :data:`END`
        """
        if data is None and self.data is not None:
            data = self.data
        else:
            self.data = data
        self.ax = ax
        if data is None:  # nothing to do if no data is given
            return
        self.no_auto_update = not (
            not self.no_auto_update or not data.psy.no_auto_update)
        data.psy.plotter = self
        if not make_plot:  # stop here if we shall not plot
            return
        self.logger.debug("Initializing plot...")
        if remove:
            self.logger.debug("    Removing old formatoptions...")
            for fmto in self._fmtos:
                try:
                    fmto.remove()
                except Exception:
                    self.logger.debug(
                        "Could not remove %s while initializing", fmto.key,
                        exc_info=True)
        if clear:
            self.logger.debug("    Clearing axes...")
            self.ax.clear()
            self.cleared = True
        # get the formatoptions. We sort them here by key to make sure that the
        # order always stays the same (easier for debugging)
        fmto_groups = self._grouped_fmtos(self._sorted_by_priority(
            sorted(self._fmtos, key=lambda fmto: fmto.key)))
        self.plot_data = self.data
        self._updating = True
        for fmto_priority, grouper in fmto_groups:
            if priority is None or fmto_priority == priority:
                self._plot_by_priority(fmto_priority, grouper,
                                       initializing=True)
        self._release_all(True)  # finish the update
        self.cleared = False
        self.replot = False
        self._initialized = True
        self._updating = False

        if draw is None:
            draw = rcParams['auto_draw']
        if draw:
            self.draw()
            if rcParams['auto_show']:
                self.show()

    docstrings.keep_params('InteractiveBase._register_update.parameters',
                           'force', 'todefault')

    @docstrings.get_sections(base='Plotter._register_update')
    @docstrings.dedent
    def _register_update(self, fmt={}, replot=False, force=False,
                         todefault=False):
        """
        Register formatoptions for the update

        Parameters
        ----------
        fmt: dict
            Keys can be any valid formatoptions with the corresponding values
            (see the :attr:`formatoptions` attribute)
        replot: bool
            Boolean that determines whether the data specific formatoptions
            shall be updated in any case or not.
        %(InteractiveBase._register_update.parameters.force|todefault)s"""
        if self.disabled:
            return
        self.replot = self.replot or replot
        self._todefault = self._todefault or todefault
        if force is True:
            force = list(fmt)
        self._force.update(
            [ret[0] for ret in map(self.check_key, force or [])])
        # check the keys
        list(map(self.check_key, fmt))
        self._registered_updates.update(fmt)

    def make_plot(self):
        """Method for making the plot

        This method is called at the end of the :attr:`BEFOREPLOTTING` stage if
        and only if the :attr:`plot_fmt` attribute is set to ``True``"""
        pass

    @docstrings.dedent
    def start_update(self, draw=None, queues=None, update_shared=True):
        """
        Conduct the registered plot updates

        This method starts the updates from what has been registered by the
        :meth:`update` method. You can call this method if you did not set the
        `auto_update` parameter to True when calling the :meth:`update` method
        and when the :attr:`no_auto_update` attribute is True.

        Parameters
        ----------
        %(InteractiveBase.start_update.parameters)s

        Returns
        -------
        %(InteractiveBase.start_update.returns)s

        See Also
        --------
        :attr:`no_auto_update`, update"""
        def update_the_others():
            for fmto in fmtos:
                for other_fmto in fmto.shared:
                    if not other_fmto.plotter._updating:
                        other_fmto.plotter._register_update(
                            force=[other_fmto.key])
            for fmto in fmtos:
                for other_fmto in fmto.shared:
                    if not other_fmto.plotter._updating:
                        other_draw = other_fmto.plotter.start_update(
                            draw=False, update_shared=False)
                        if other_draw:
                            self._figs2draw.add(
                                other_fmto.plotter.ax.get_figure())
        if self.disabled:
            return False

        if queues is not None:
            queues[0].get()
        self.logger.debug("Starting update of %r",
                          self._registered_updates.keys())
        # update the formatoptions
        self._save_state()
        try:
            # get the formatoptions. We sort them here by key to make sure that
            # the order always stays the same (easier for debugging)
            fmtos = sorted(self._set_and_filter(), key=lambda fmto: fmto.key)
        except Exception:
            # restore last (working) state
            last_state = self._old_fmt.pop(-1)
            with self.no_validation:
                for key in self:
                    self[key] = last_state.get(key, getattr(self, key).default)
            if queues is not None:
                queues[0].task_done()
            self._release_all(queue=None if queues is None else queues[1])
            # raise the error
            raise
        for fmto in fmtos:
            for fmto2 in fmto.shared:
                fmto2.plotter._to_update[fmto2] = self
        if queues is not None:
            self._updating = True
            queues[0].task_done()
            # wait for the other tasks to finish
            queues[0].join()
            queues[1].get()
        fmtos.extend([fmto for fmto in self._insert_additionals(list(
            self._to_update)) if fmto not in fmtos])
        self._to_update.clear()

        fmto_groups = self._grouped_fmtos(self._sorted_by_priority(fmtos[:]))
        # if any formatoption requires a clearing of the axes is updated,
        # we reinitialize the plot
        try:
            if self.cleared:
                self.reinit(draw=draw)
                update_the_others()
                arr_draw = True
            else:
                # otherwise we update it
                arr_draw = False
                for priority, grouper in fmto_groups:
                    arr_draw = True
                    self._plot_by_priority(priority, grouper)
                update_the_others()
        except Exception:
            raise
        finally:
            # make sure that all locks are released
            self._release_all(finish=True,
                              queue=None if queues is None else queues[1])
        if draw is None:
            draw = rcParams['auto_draw']
        if draw and arr_draw:
            self.draw()
            if rcParams['auto_show']:
                self.show()
        self.replot = False
        return arr_draw

    def _release_all(self, finish=False, queue=None):
        # make sure that all locks are released
        try:
            for fmto in self._fmtos:
                if finish:
                    fmto.finish_update()
                try:
                    fmto.lock.release()
                except RuntimeError:
                    pass
        except:
            raise
        finally:
            if queue is not None:
                queue.task_done()
                queue.join()
            self._updating = False

    def _plot_by_priority(self, priority, fmtos, initializing=False):
        def update(fmto):
            other_fmto = self._shared.get(fmto.key)
            if other_fmto:
                self.logger.debug("%s is shared with %s", fmto.key,
                                  other_fmto.plotter.logger.name)
                other_fmto.share(fmto, initializing=initializing)
            # but if not, share them
            else:
                if initializing:
                    self.logger.debug("Initializing %s", fmto.key)
                    fmto.initialize_plot(fmto.value)
                else:
                    self.logger.debug("Updating %s", fmto.key)
                    fmto.update(fmto.value)
            try:
                fmto.lock.release()
            except RuntimeError:
                pass

        self._initializing = initializing

        self.logger.debug(
            "%s formatoptions with priority %i",
            "Initializing" if initializing else "Updating", priority)

        if priority >= START or priority == END:
            for fmto in fmtos:
                update(fmto)
        elif priority == BEFOREPLOTTING:
            for fmto in fmtos:
                update(fmto)
            self._make_plot()

        self._initializing = False

    @docstrings.dedent
    def reinit(self, draw=None, clear=False):
        """
        Reinitializes the plot with the same data and on the same axes.

        Parameters
        ----------
        %(InteractiveBase.start_update.parameters.draw)s
        clear: bool
            Whether to clear the axes or not

        Warnings
        --------
        The axes may be cleared when calling this method (even if `clear` is
        set to False)!"""
        # call the initialize_plot method. Note that clear can be set to
        # False if any fmto has requires_clearing attribute set to True,
        # because this then has been cleared before
        self.initialize_plot(
            self.data, self._ax, draw=draw, clear=clear or any(
                fmto.requires_clearing for fmto in self._fmtos),
            remove=True)

    def draw(self):
        """Draw the figures and those that are shared and have been changed"""
        for fig in self.figs2draw:
            fig.canvas.draw()
        self._figs2draw.clear()

    def _grouped_fmtos(self, fmtos):
        def key_func(fmto):
            if fmto.priority >= START:
                return START
            elif fmto.priority >= BEFOREPLOTTING:
                return BEFOREPLOTTING
            else:
                return END
        return groupby(fmtos, key_func)

    def _set_and_filter(self):
        """Filters the registered updates and sort out what is not needed

        This method filters out the formatoptions that have not changed, sets
        the new value and returns an iterable that is sorted by the priority
        (highest priority comes first) and dependencies

        Returns
        -------
        list
            list of :class:`Formatoption` objects that have to be updated"""
        fmtos = []
        seen = set()
        for key in self._force:
            self._registered_updates.setdefault(key, getattr(self, key).value)
        for key, value in chain(
                six.iteritems(self._registered_updates),
                six.iteritems(
                    {key: getattr(self, key).default for key in self})
                if self._todefault else ()):
            if key in seen:
                continue
            seen.add(key)
            fmto = getattr(self, key)
            # if the key is shared, a warning will be printed as long as
            # this plotter is not also updating (for example due to a whole
            # project update)
            if key in self._shared and key not in self._force:
                if not self._shared[key].plotter._updating:
                    warn(("%s formatoption is shared with another plotter."
                          " Use the unshare method to enable the updating") % (
                              fmto.key),
                         logger=self.logger)
                changed = False
            else:
                try:
                    changed = fmto.check_and_set(
                        value, todefault=self._todefault,
                        validate=not self.no_validation)
                except Exception as e:
                    self._registered_updates.pop(key, None)
                    self.logger.debug('Failed to set %s', key)
                    raise e
            changed = changed or key in self._force
            if changed:
                fmtos.append(fmto)
        fmtos = self._insert_additionals(fmtos, seen)
        for fmto in fmtos:
            fmto.lock.acquire()
        self._todefault = False
        self._registered_updates.clear()
        self._force.clear()
        return fmtos

    def _insert_additionals(self, fmtos, seen=None):
        """
        Insert additional formatoptions into `fmtos`.

        This method inserts those formatoptions into `fmtos` that are required
        because one of the following criteria is fullfilled:

        1. The :attr:`replot` attribute is True
        2. Any formatoption with START priority is in `fmtos`
        3. A dependency of one formatoption is in `fmtos`

        Parameters
        ----------
        fmtos: list
            The list of formatoptions that shall be updated
        seen: set
            The formatoption keys that shall not be included. If None, all
            formatoptions in `fmtos` are used

        Returns
        -------
        fmtos
            The initial `fmtos` plus further formatoptions

        Notes
        -----
        `fmtos` and `seen` are modified in place (except that any formatoption
        in the initial `fmtos` has :attr:`~Formatoption.requires_clearing`
        attribute set to True)"""
        def get_dependencies(fmto):
            if fmto is None:
                return []
            return fmto.dependencies + list(chain(*map(
                lambda key: get_dependencies(getattr(self, key, None)),
                fmto.dependencies)))
        seen = seen or {fmto.key for fmto in fmtos}
        keys = {fmto.key for fmto in fmtos}
        self.replot = self.replot or any(
            fmto.requires_replot for fmto in fmtos)
        if self.replot or any(fmto.priority >= START for fmto in fmtos):
            self.replot = True
            self.plot_data = self.data
            new_fmtos = dict((f.key, f) for f in self._fmtos
                             if ((f not in fmtos and is_data_dependent(
                                 f, self.data))))
            seen.update(new_fmtos)
            keys.update(new_fmtos)
            fmtos += list(new_fmtos.values())

        # insert the formatoptions that have to be updated if the plot is
        # changed
        if any(fmto.priority >= BEFOREPLOTTING for fmto in fmtos):
            new_fmtos = dict((f.key, f) for f in self._fmtos
                             if ((f not in fmtos and f.update_after_plot)))
            fmtos += list(new_fmtos.values())
        for fmto in set(self._fmtos).difference(fmtos):
            all_dependencies = get_dependencies(fmto)
            if keys.intersection(all_dependencies):
                fmtos.append(fmto)
        if any(fmto.requires_clearing for fmto in fmtos):
            self.cleared = True
            return list(self._fmtos)
        return fmtos

    def _sorted_by_priority(self, fmtos, changed=None):
        """Sort the formatoption objects by their priority and dependency

        Parameters
        ----------
        fmtos: list
            list of :class:`Formatoption` instances
        changed: list
            the list of formatoption keys that have changed

        Yields
        ------
        Formatoption
            The next formatoption as it comes by the sorting

        Warnings
        --------
        The list `fmtos` is cleared by this method!"""
        def pop_fmto(key):
            idx = fmtos_keys.index(key)
            del fmtos_keys[idx]
            return fmtos.pop(idx)

        def get_children(fmto, parents_keys):
            all_fmtos = fmtos_keys + parents_keys
            for key in fmto.children + fmto.dependencies:
                if key not in fmtos_keys:
                    continue
                child_fmto = pop_fmto(key)
                for childs_child in get_children(
                        child_fmto, parents_keys + [child_fmto.key]):
                    yield childs_child
                # filter out if parent is in update list
                if (any(key in all_fmtos for key in child_fmto.parents) or
                        fmto.key in child_fmto.parents):
                    continue
                yield child_fmto

        fmtos.sort(key=lambda fmto: fmto.priority, reverse=True)
        fmtos_keys = [fmto.key for fmto in fmtos]
        self._last_update = changed or fmtos_keys[:]
        self.logger.debug("Update the formatoptions %s", fmtos_keys)
        while fmtos:
            del fmtos_keys[0]
            fmto = fmtos.pop(0)
            # first update children
            for child_fmto in get_children(fmto, [fmto.key]):
                yield child_fmto
            # filter out if parent is in update list
            if any(key in fmtos_keys for key in fmto.parents):
                continue
            yield fmto

    @classmethod
    def _get_formatoptions(cls, include_bases=True):
        """
        Iterator over formatoptions

        This class method returns an iterator that contains all the
        formatoption keys that are in this class and that are defined
        in the base classes

        Notes
        -----
        There is absolutely no need to call this method besides the plotter
        initialization, since all formatoptions are in the plotter itself.
        Just type::

            >>> list(plotter)

        to get the formatoptions.

        See Also
        --------
        _format_keys"""
        def base_fmtos(base):
            return filter(
                lambda key: isinstance(getattr(cls, key), Formatoption),
                getattr(base, '_get_formatoptions', empty)(False))

        def empty(*args, **kwargs):
            return list()
        fmtos = (attr for attr, obj in six.iteritems(cls.__dict__)
                 if isinstance(obj, Formatoption))
        if not include_bases:
            return fmtos
        return unique_everseen(chain(fmtos, *map(base_fmtos, cls.__mro__)))

    docstrings.keep_types('check_key.parameters', 'kwargs',
                          r'``\*args,\*\*kwargs``')

    @classmethod
    @docstrings.get_sections(base='Plotter._enhance_keys')
    @docstrings.dedent
    def _enhance_keys(cls, keys=None, *args, **kwargs):
        """
        Enhance the given keys by groups

        Parameters
        ----------
        keys: list of str or None
            If None, the all formatoptions of the given class are used. Group
            names from the :attr:`psyplot.plotter.groups` mapping are replaced
            by the formatoptions

        Other Parameters
        ----------------
        %(check_key.parameters.kwargs)s

        Returns
        -------
        list of str
            The enhanced list of the formatoptions"""
        all_keys = list(cls._get_formatoptions())
        if isinstance(keys, six.string_types):
            keys = [keys]
        else:
            keys = list(keys or sorted(all_keys))
        fmto_groups = defaultdict(list)
        for key in all_keys:
            fmto_groups[getattr(cls, key).group].append(key)
        new_i = 0
        for i, key in enumerate(keys[:]):

            if key in fmto_groups:
                del keys[new_i]
                for key2 in fmto_groups[key]:
                    if key2 not in keys:
                        keys.insert(new_i, key2)
                        new_i += 1
            else:
                valid, similar, message = check_key(
                    key, all_keys, False, 'formatoption keyword', *args,
                    **kwargs)
                if not valid:
                    keys.remove(key)
                    new_i -= 1
                    warn(message)
            new_i += 1
        return keys

    @classmethod
    @docstrings.get_sections(base=
        'Plotter.show_keys', sections=['Parameters', 'Returns',
                                       'Other Parameters'])
    @docstrings.dedent
    def show_keys(cls, keys=None, indent=0, grouped=False, func=None,
                  include_links=False, *args, **kwargs):
        """
        Classmethod to return a nice looking table with the given formatoptions

        Parameters
        ----------
        %(Plotter._enhance_keys.parameters)s
        indent: int
            The indentation of the table
        grouped: bool, optional
            If True, the formatoptions are grouped corresponding to the
            :attr:`Formatoption.groupname` attribute

        Other Parameters
        ----------------
        func: function or None
            The function the is used for returning (by default it is printed
            via the :func:`print` function or (when using the gui) in the
            help explorer). The given function must take a string as argument
        include_links: bool or None, optional
            Default False. If True, links (in restructured formats) are
            included in the description. If None, the behaviour is determined
            by the :attr:`psyplot.plotter.Plotter.include_links` attribute.
        %(Plotter._enhance_keys.other_parameters)s

        Returns
        -------
        results of `func`
            None if `func` is the print function, otherwise anything else

        See Also
        --------
        show_summaries, show_docs"""
        def titled_group(groupname):
            bars = str_indent + '*' * len(groupname) + '\n'
            return bars + str_indent + groupname + '\n' + bars

        keys = cls._enhance_keys(keys, *args, **kwargs)
        str_indent = " " * indent
        func = func or default_print_func
        # call this function recursively when grouped is True
        if grouped:
            grouped_keys = DefaultOrderedDict(list)
            for fmto in map(lambda key: getattr(cls, key), keys):
                grouped_keys[fmto.groupname].append(fmto.key)
            text = ""
            for group, keys in six.iteritems(grouped_keys):
                text += titled_group(group) + cls.show_keys(
                    keys, indent=indent, grouped=False, func=six.text_type,
                    include_links=include_links) + '\n\n'
            return func(text.rstrip())

        if not keys:
            return
        n = len(keys)
        ncols = min([4, n])  # number of columns
        # The number of cells in the table is one of the following cases:
        #     1. The number of columns and equal to the number of keys
        #     2. The number of keys
        #     3. The number of keys plus the empty cells in the last column
        ncells = n + ((ncols - (n % ncols)) if n != ncols else 0)
        if include_links or (include_links is None and cls.include_links):
            long_keys = list(map(lambda key: ':attr:`~%s.%s.%s`' % (
                cls.__module__, cls.__name__, key), keys))
        else:
            long_keys = keys
        maxn = max(map(len, long_keys))  # maximal lenght of the keys
        # extend with empty cells
        long_keys.extend([' ' * maxn] * (ncells - n))
        bars = (str_indent + '+-' + ("-"*(maxn) + "-+-")*ncols)[:-1]
        lines = ('| %s |\n%s' % (' | '.join(
            key.ljust(maxn) for key in long_keys[i:i+ncols]), bars)
            for i in range(0, n, ncols))
        text = bars + "\n" + str_indent + ("\n" + str_indent).join(
            lines)
        if six.PY2:
            text = text.encode('utf-8')

        return func(text)

    @classmethod
    @docstrings.dedent
    def _show_doc(cls, fmt_func, keys=None, indent=0, grouped=False,
                  func=None, include_links=False, *args, **kwargs):
        """
        Classmethod to print the formatoptions and their documentation

        This function is the basis for the :meth:`show_summaries` and
        :meth:`show_docs` methods

        Parameters
        ----------
        fmt_func: function
            A function that takes the key, the key as it is printed, and the
            documentation of a formatoption as argument and returns what shall
            be printed
        %(Plotter.show_keys.parameters)s

        Other Parameters
        ----------------
        %(Plotter.show_keys.other_parameters)s

        Returns
        -------
        %(Plotter.show_keys.returns)s

        See Also
        --------
        show_summaries, show_docs"""
        def titled_group(groupname):
            bars = str_indent + '*' * len(groupname) + '\n'
            return bars + str_indent + groupname + '\n' + bars

        func = func or default_print_func

        keys = cls._enhance_keys(keys, *args, **kwargs)
        str_indent = " " * indent
        if grouped:
            grouped_keys = DefaultOrderedDict(list)
            for fmto in map(lambda key: getattr(cls, key), keys):
                grouped_keys[fmto.groupname].append(fmto.key)
            text = "\n\n".join(
                titled_group(group) + cls._show_doc(
                    fmt_func, keys, indent=indent, grouped=False,
                    func=str, include_links=include_links)
                for group, keys in six.iteritems(grouped_keys))
            return func(text.rstrip())

        if include_links or (include_links is None and cls.include_links):
            long_keys = list(map(lambda key: ':attr:`~%s.%s.%s`' % (
                cls.__module__, cls.__name__, key), keys))
        else:
            long_keys = keys

        text = '\n'.join(str_indent + long_key + '\n' + fmt_func(
            key, long_key, getattr(cls, key).__doc__) for long_key, key in zip(
                long_keys, keys))
        return func(text)

    @classmethod
    @docstrings.dedent
    def show_summaries(cls, keys=None, indent=0, *args, **kwargs):
        """
        Classmethod to print the summaries of the formatoptions

        Parameters
        ----------
        %(Plotter.show_keys.parameters)s

        Other Parameters
        ----------------
        %(Plotter.show_keys.other_parameters)s

        Returns
        -------
        %(Plotter.show_keys.returns)s

        See Also
        --------
        show_keys, show_docs"""
        def find_summary(key, key_txt, doc):
            return '\n'.join(wrapper.wrap(doc[:doc.find('\n\n')]))
        str_indent = " " * indent
        wrapper = TextWrapper(width=80, initial_indent=str_indent + ' ' * 4,
                              subsequent_indent=str_indent + ' ' * 4)
        return cls._show_doc(find_summary, keys=keys, indent=indent,
                             *args, **kwargs)

    @classmethod
    @docstrings.dedent
    def show_docs(cls, keys=None, indent=0, *args, **kwargs):
        """
        Classmethod to print the full documentations of the formatoptions

        Parameters
        ----------
        %(Plotter.show_keys.parameters)s

        Other Parameters
        ----------------
        %(Plotter.show_keys.other_parameters)s

        Returns
        -------
        %(Plotter.show_keys.returns)s

        See Also
        --------
        show_keys, show_docs"""
        def full_doc(key, key_txt, doc):
            return ('=' * len(key_txt)) + '\n' + doc + '\n'
        return cls._show_doc(full_doc, keys=keys, indent=indent,
                             *args, **kwargs)

    @classmethod
    def _get_rc_strings(cls):
        """
        Recursive method to get the base strings in the rcParams dictionary.

        This method takes the :attr:`_rcparams_string` attribute from the given
        `class` and combines it with the :attr:`_rcparams_string` attributes
        from the base classes.
        The returned frozenset can be used as base strings for the
        :meth:`psyplot.config.rcsetup.RcParams.find_and_replace` method.

        Returns
        -------
        list
            The first entry is the :attr:`_rcparams_string` of this class,
            the following the :attr:`_rcparams_string` attributes of the
            base classes according to the method resolution order of this
            class"""
        return list(unique_everseen(chain(
            *map(lambda base: getattr(base, '_rcparams_string', []),
                 cls.__mro__))))

    def _set_rc(self):
        """Method to set the rcparams and defaultParams for this plotter"""
        base_str = self._get_rc_strings()
        # to make sure that the '.' is not interpreted as a regex pattern,
        # we specify the pattern_base by ourselves
        pattern_base = map(lambda s: s.replace('.', r'\.'), base_str)
        # pattern for valid keys being all formatoptions in this plotter
        pattern = '(%s)(?=$)' % '|'.join(self._get_formatoptions())
        self._rc = rcParams.find_and_replace(base_str, pattern=pattern,
                                             pattern_base=pattern_base)
        user_rc = SubDict(rcParams['plotter.user'], base_str, pattern=pattern,
                          pattern_base=pattern_base)
        self._rc.update(user_rc.data)

        self._defaultParams = SubDict(rcParams.defaultParams, base_str,
                                      pattern=pattern,
                                      pattern_base=pattern_base)

    docstrings.keep_params('InteractiveBase.update.parameters', 'auto_update')

    @docstrings.dedent
    def update(self, fmt={}, replot=False, auto_update=False, draw=None,
               force=False, todefault=False, **kwargs):
        """
        Update the formatoptions and the plot

        If the :attr:`data` attribute of this plotter is None, the plotter is
        updated like a usual dictionary (see :meth:`dict.update`). Otherwise
        the update is registered and the plot is updated if `auto_update` is
        True or if the :meth:`start_update` method is called (see below).

        Parameters
        ----------
        %(Plotter._register_update.parameters)s
        %(InteractiveBase.start_update.parameters)s
        %(InteractiveBase.update.parameters.auto_update)s
        ``**kwargs``
            Any other formatoption that shall be updated (additionally to those
            in `fmt`)

        Notes
        -----
        %(InteractiveBase.update.notes)s"""
        if self.disabled:
            return
        fmt = dict(fmt)
        if kwargs:
            fmt.update(kwargs)
        # if the data is None, update like a usual dictionary (but with
        # validation)
        if not self._initialized:
            for key, val in six.iteritems(fmt):
                self[key] = val
            return

        self._register_update(fmt=fmt, replot=replot, force=force,
                              todefault=todefault)
        if not self.no_auto_update or auto_update:
            self.start_update(draw=draw)

    def _set_sharing_keys(self, keys):
        """
        Set the keys to share or unshare

        Parameters
        ----------
        keys: string or iterable of strings
            The iterable may contain formatoptions that shall be shared (or
            unshared), or group names of formatoptions to share all
            formatoptions of that group (see the :attr:`fmt_groups` property).
            If None, all formatoptions of this plotter are inserted.

        Returns
        -------
        set
            The set of formatoptions to share (or unshare)"""
        if isinstance(keys, str):
            keys = {keys}
        keys = set(self) if keys is None else set(keys)
        fmto_groups = self._fmto_groups
        keys.update(chain(*(map(lambda fmto: fmto.key, fmto_groups[key])
                            for key in keys.intersection(fmto_groups))))
        keys.difference_update(fmto_groups)
        return keys

    @docstrings.get_sections(base='Plotter.share')
    @docstrings.dedent
    def share(self, plotters, keys=None, draw=None, auto_update=False):
        """
        Share the formatoptions of this plotter with others

        This method shares the formatoptions of this :class:`Plotter` instance
        with others to make sure that, if the formatoption of this changes,
        those of the others change as well

        Parameters
        ----------
        plotters: list of :class:`Plotter` instances or a :class:`Plotter`
            The plotters to share the formatoptions with
        keys: string or iterable of strings
            The formatoptions to share, or group names of formatoptions to
            share all formatoptions of that group (see the
            :attr:`fmt_groups` property). If None, all formatoptions of this
            plotter are unshared.
        %(InteractiveBase.start_update.parameters.draw)s
        %(InteractiveBase.update.parameters.auto_update)s

        See Also
        --------
        unshare, unshare_me"""
        auto_update = auto_update or not self.no_auto_update
        if isinstance(plotters, Plotter):
            plotters = [plotters]
        keys = self._set_sharing_keys(keys)
        for plotter in plotters:
            for key in keys:
                fmto = self._shared.get(key, getattr(self, key))
                if not getattr(plotter, key) == fmto:
                    plotter._shared[key] = getattr(self, key)
                    fmto.shared.add(getattr(plotter, key))
        # now exit if we are not initialized
        if self._initialized:
            self.update(force=keys, auto_update=auto_update, draw=draw)
        for plotter in plotters:
            if not plotter._initialized:
                continue
            old_registered = plotter._registered_updates.copy()
            plotter._registered_updates.clear()
            try:
                plotter.update(force=keys, auto_update=auto_update, draw=draw)
            except:
                raise
            finally:
                plotter._registered_updates.clear()
                plotter._registered_updates.update(old_registered)
        if draw is None:
            draw = rcParams['auto_draw']
        if draw:
            self.draw()
            if rcParams['auto_show']:
                self.show()

    @docstrings.dedent
    def unshare(self, plotters, keys=None, auto_update=False, draw=None):
        """
        Close the sharing connection of this plotter with others

        This method undoes the sharing connections made by the :meth:`share`
        method and releases the given `plotters` again, such that the
        formatoptions in this plotter may be updated again to values different
        from this one.

        Parameters
        ----------
        plotters: list of :class:`Plotter` instances or a :class:`Plotter`
            The plotters to release
        keys: string or iterable of strings
            The formatoptions to unshare, or group names of formatoptions to
            unshare all formatoptions of that group (see the
            :attr:`fmt_groups` property). If None, all formatoptions of this
            plotter are unshared.
        %(InteractiveBase.start_update.parameters.draw)s
        %(InteractiveBase.update.parameters.auto_update)s

        See Also
        --------
        share, unshare_me"""
        auto_update = auto_update or not self.no_auto_update
        if isinstance(plotters, Plotter):
            plotters = [plotters]
        keys = self._set_sharing_keys(keys)
        for plotter in plotters:
            plotter.unshare_me(keys, auto_update=auto_update, draw=draw,
                               update_other=False)
        self.update(force=keys, auto_update=auto_update, draw=draw)

    @docstrings.get_sections(base='Plotter.unshare_me')
    @docstrings.dedent
    def unshare_me(self, keys=None, auto_update=False, draw=None,
                   update_other=True):
        """
        Close the sharing connection of this plotter with others

        This method undoes the sharing connections made by the :meth:`share`
        method and release this plotter again.

        Parameters
        ----------
        keys: string or iterable of strings
            The formatoptions to unshare, or group names of formatoptions to
            unshare all formatoptions of that group (see the
            :attr:`fmt_groups` property). If None, all formatoptions of this
            plotter are unshared.
        %(InteractiveBase.start_update.parameters.draw)s
        %(InteractiveBase.update.parameters.auto_update)s

        See Also
        --------
        share, unshare"""
        auto_update = auto_update or not self.no_auto_update
        keys = self._set_sharing_keys(keys)
        to_update = []
        for key in keys:
            fmto = getattr(self, key)
            try:
                other_fmto = self._shared.pop(key)
            except KeyError:
                pass
            else:
                other_fmto.shared.remove(fmto)
                if update_other:
                    other_fmto.plotter._register_update(
                        force=[other_fmto.key])
                    to_update.append(other_fmto.plotter)
        self.update(force=keys, draw=draw, auto_update=auto_update)
        if update_other and auto_update:
            for plotter in to_update:
                plotter.start_update(draw=draw)

    def get_vfunc(self, key):
        """Return the validation function for a specified formatoption

        Parameters
        ----------
        key: str
            Formatoption key in the :attr:`rc` dictionary

        Returns
        -------
        function
            Validation function for this formatoption"""
        return self._defaultParams[key][1]

    def _save_state(self):
        """Saves the current formatoptions"""
        self._old_fmt.append(self.changed)

    def show(self):
        """Shows all open figures"""
        import matplotlib.pyplot as plt
        plt.show(block=False)

    @dedent
    def has_changed(self, key, include_last=True):
        """
        Determine whether a formatoption changed in the last update

        Parameters
        ----------
        key: str
            A formatoption key contained in this plotter
        include_last: bool
            if True and the formatoption has been included in the last update,
            the return value will not be None. Otherwise the return value will
            only be not None if it changed during the last update

        Returns
        -------
        None or list
            - None, if the value has not been changed during the last update or
              `key` is not a valid formatoption key
            - a list of length two with the old value in the first place and
              the given `value` at the second"""
        if self._initializing or key not in self:
            return
        fmto = getattr(self, key)
        if self._old_fmt and key in self._old_fmt[-1]:
            old_val = self._old_fmt[-1][key]
        else:
            old_val = fmto.default
        if (fmto.diff(old_val) or (include_last and
                                   fmto.key in self._last_update)):
            return [old_val, fmto.value]

    def get_enhanced_attrs(self, arr, axes=['x', 'y', 't', 'z']):
        if isinstance(arr, InteractiveList):
            all_attrs = list(starmap(self.get_enhanced_attrs, zip(
                arr, repeat(axes))))
            attrs = {key: val for key, val in six.iteritems(all_attrs[0])
                     if all(key in attrs and attrs[key] == val
                            for attrs in all_attrs[1:])}
            attrs.update(arr.attrs)
        else:
            attrs = arr.attrs.copy()
            base_variables = self.base_variables
            if len(base_variables) > 1:  # multiple variables
                for name, base_var in six.iteritems(base_variables):
                    attrs.update(
                        {six.text_type(name)+key: value
                         for key, value in six.iteritems(base_var.attrs)})
            else:
                base_var = next(six.itervalues(base_variables))
            attrs['name'] = arr.name
            for dim, coord in six.iteritems(getattr(arr, 'coords', {})):
                if coord.size == 1:
                    attrs[dim] = format_time(coord.values)
            if isinstance(self.data, InteractiveList):
                decoder = self.data[0].psy.decoder
            else:
                decoder = self.data.psy.decoder
            for dim in axes:
                for obj in [base_var, arr]:
                    coord = getattr(decoder, 'get_' + dim)(
                        obj, coords=getattr(arr, 'coords', None))
                    if coord is None:
                        continue
                    if coord.size == 1:
                        attrs[dim] = format_time(coord.values)
                    attrs[dim + 'name'] = coord.name
                    for key, val in six.iteritems(coord.attrs):
                        attrs[dim + key] = val
        self._enhanced_attrs = attrs
        return attrs

    def _make_plot(self):
        plot_fmtos = [fmto for fmto in self._fmtos if fmto.plot_fmt]
        plot_fmtos.sort(key=lambda fmto: fmto.priority, reverse=True)
        for fmto in plot_fmtos:
            self.logger.debug("Making plot with %s formatoption", fmto.key)
            fmto.make_plot()

    @classmethod
    def _get_sample_projection(cls):
        """Returns None. May be subclassed to return a projection that
        can be used when creating a subplot"""
        pass

    @docstrings.dedent
    def convert_coordinate(self, coord, *variables):
        """Convert a coordinate to units necessary for the plot.

        %(Formatoption.convert_coordinate.summary_ext)s

        Parameters
        ----------
        %(Formatoption.convert_coordinate.parameters)s

        Returns
        -------
        %(Formatoption.convert_coordinate.returns)s

        Notes
        -----
        This method is supposed to be implemented by subclasses. The default
        implementation by the :class:`Plotter` class does nothing.
        """
        return coord
