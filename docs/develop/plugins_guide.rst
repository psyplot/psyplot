.. _plugins_guide:

How to implement your own plotters and plugins
==============================================
New plotters and plugins to the psyplot framework are highly welcomed. In this
guide, we present :ref:`how to create new plotters <new_plotters>` and explain
to you how you can :ref:`include them as a plugin in psyplot <new_plugins>`.

.. _new_plotters:

Creating plotters
-----------------

.. currentmodule:: psyplot.plotter

Implementing new plotters can be very easy or quite an effort depending on how
sophisticated you want to do it. In principle, you only have to implement the
:meth:`Formatoption.update` method and a default value. I.e., one simple
formatoption would be


.. ipython::

    In [1]: from psyplot.plotter import Formatoption, Plotter

    In [2]: class MyFormatoption(Formatoption):
       ...:     default = 'my text'
       ...:     def update(self, value):
       ...:         self.ax.text(0.5, 0.5, value, fontsize='xx-large')

together with a plotter

.. ipython::

    In [3]: class MyPlotter(Plotter):
       ...:     my_fmt = MyFormatoption('my_fmt')

and your done. Now you can make a simple plot

.. ipython::

    In [4]: from psyplot import open_dataset

    In [5]: ds = open_dataset('demo.nc')

    @savefig docs_demo_MyPlotter_simple.png width=4in
    In [6]: plotter = MyPlotter(ds.t2m)

However, if you're using the psyplot framework, you probably will be a bit more
advanced so let's talk about attributes and methods of the :class:`Formatoption`
class.

If you look into the documentation of the :class:`Formatoption` class, you find
quite a lot of attributes and methods which probably is a bit depressing and
confusing. But in principle, we can group them into 4 categories, the interface
to the data, to the plotter and to other formatoptions. Plus an additional
category for some Formatoption internals you definitely have to care about.

Interface for the plotter
^^^^^^^^^^^^^^^^^^^^^^^^^
The first interface is the one, that interfaces to the plotter. The most
important attributes in this group are the :attr:`~Formatoption.key`,
:attr:`~Formatoption.priority`, :attr:`~Formatoption.plot_fmt`,
:meth:`~Formatoption.initialize_plot` and most important the
:meth:`~Formatoption.update` method.

The :attr:`~Formatoption.key` is the unique key for the formatoption inside the
plotter. In our example above, we assign the ``'my_fmt'`` key to the
``MyFormatoption`` class in ``MyPlotter``. Hence, this key is defined when the
plotter class is defined and will be automatically assigned to the formatoption.

The next important attribute is the :attr:`priority` attribute. There are three
stages in the update of a plotter:

1. The stage with data manipulation. If formatoptions manipulate the data that
   shall be visualized (the :attr:`~Formatoption.data` attribute), those
   formatoptions are updated first. They have the :attr:`psyplot.plotter.START`
   priority
2. The stage of the plot. Formatoptions that influence how the data is
   visualized are updated here (e.g. the colormap or formatoptions that do the
   plotting). They have the :attr:`psyplot.plotter.BEFOREPLOTTING` priority.
3. The stage of the plot where additional informations are inserted. Here all
   the labels are updated, e.g. the title, xlabel, etc.. This is the default
   priority of the :class:`Formatoption.priority` attribute, the
   :attr:`psyplot.plotter.END` priority.

If there is any formatoption updated within the first two groups, the plot of
the plotter is updated. This brings us to the third important attribute, the
:attr:`~Formatoption.plot_fmt`. This boolean tells the plotter, whether the
corresponding formatoption is assumed to make a plot at the end of the second
stage (the :attr:`~psyplot.plotter.BEFOREPLOTTING` stage). If this attribute is
``True``, then the plotter will call the :meth:`Formatoption.make_plot` method
of the formatoption instance.

Finally, the :meth:`~Formatoption.initialize_plot` and
:meth:`~Formatoption.update` methods, this is were your contribution really is
required. The :meth:`~Formatoption.initialize_plot` method is called when the
plot is created for the first time, the :meth:`~Formatoption.update` method
when it is updated (the default implementation of the
:meth:`~Formatoption.initialize_plot` simply calls the
:meth:`~Formatoption.update` method). Implement these methods in your
formatoption and thereby make use of the interface to the
:ref:`data <fmt_data_interface>` and other
:ref:`formatoptions <fmt_fmt_interface>`.

.. _fmt_data_interface:

Interface to the data
^^^^^^^^^^^^^^^^^^^^^
The next set of attributes help you to interface to the data. There are two
important parts in this section the interface to the data and the
interpretation of the data.

The first part is mainly represented to the :attr:`Formatoption.data` and
:attr:`Formatoption.raw_data` attributes. The plotter that contains the
formatoption often creates a copy of the data because the data for
the visualization might be modified (see for example the
:class:`psy_reg.plotter.LinRegPlotter`). This modified data can be accessed
through the :attr:`Formatoption.data` and should be the standard approach to
access the data within a formatoption. Nevertheless, the original data can be
accessed through the :attr:`Formatoption.raw_data` attribute. However, it only
makes sense to access this data for formatoption with :attr:`START`
:attr:`~Formatoption.priority`.

The result of these two attributes depend on the
:attr:`Formatoption.index_in_list` attribute. The data objects in the psyplot
framework are either a :class:`xarray.DataArray` or a list of those in a
:class:`psyplot.data.InteractiveList`. If the
:attr:`~Formatoption.index_in_list` attribute is not None, and the data object
is an :class:`~psyplot.data.InteractiveList`, then only the array at the
specified position is returned. To completely avoid this issue, you might also
use the :attr:`~Formatoption.iter_data` or :attr:`~Formatoption.iter_raw_data`
attributes.

The second part in this section is the interpretation of the data and here,
the formatoption can use the :attr:`Formatoption.decoder` attribute. This
subclass of the :class:`psyplot.data.CFDecoder` helps you to identify the
x- and y-variables in the data.


.. _fmt_fmt_interface:

Interfacing to other formatoptions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A formatoption is the lowest level in the psyplot framework. It is represented
at multiple levels:

1. at the lowest level through the subclass of the :class:`Formatoption` class
2. at the :class:`Plotter` class level which includes the formatoption class
   as a descriptor (in our example above it's ``MyPlotter.my_fmt``)
3. at the :class:`Plotter` instance level through

   i. a personalized instance of the corresponding :class:`Formatoption` class
      (i.e. ``plotter = MyPlotter(); plotter.my_fmt is not MyPlotter.my_fmt``)
   ii. an item in the plotter (i.e. ``plotter = MyPlotter(); plotter['my_fmt']``)
4. In the update methods of the :class:`Plotter`,
   :class:`psyplot.data.InteractiveBase` and :class:`psyplot.data.ArrayList`
   as a keyword (i.e.
   ``plotter = MyPlotter(); plotter.update(my_fmt='new value')``)

Hence, there is one big to the entire framework, that is: the functionality
of a new formatoption has to be completely defined through exactly one argument,
i.e. it must be possible to assign a value to the formatoption in the plotter.

For complex formatoption, this might indeed be quite a challenge for the
developer and there are two solutions to it:

1. The simple solution for the developer: Allow a dictionary as a formatoption,
   here we also have the :class:`psyplot.plotter.DictFormatoption` to help you
2. Interface to other formatoptions

First solution: Use a :class:`dict`
___________________________________
That said, to implement a formatoption that inserts a custom text and let the
user define the size of the text, you either create a formatoption that accepts
a text via

.. code-block:: python

    class CustomText(DictFormatoption):

        default = {'text': ''}

        text = None

        def validate(self, value):
            if not isinstance(value, dict):
                return {'text': value}
            return value

        def initialize_plot(self, value):
            self.text = self.ax.text(0.2, 0.2, value['text'],
                                     fontsize=value.get('size', 'large'))

        def update(self, value):
            self.text.set_text(value['text'])
            self.text.set_fontsize(value.get('size', 'large'))


    class MyPlotter(Plotter):

        my_fmt = CustomText('my_fmt')

and then you could create and update a plotter via

.. code-block:: python

    p = MyPlotter(xarray.DataArray([]))
    p.update(my_fmt='my text')  # updates the text
    p.update(my_fmt={'size': 14})  # updates the size
    p.update(my_fmt={'size': 14, 'text': 'Something'})  # updates text and size

This solution has the several advantages:

- The user does not get confused through too many formatoptions
- It is easy to allow more keywords for this formatoption

Indeed, the :class:`psy_simple.plotter.Legend` formatoption uses this framework
since the :func:`matplotlib.pyplot.legend` function accepts that many keywords
that it would be not informative to create a formatoption for each of them.

Otherwise you could of course avoid the :class:`DictFormatoption` and just
force the user to always provide a new dictionary.

Second solution: Interact with other formatoptions
__________________________________________________
Another possibility is to implement a second formatoption for the size of the
text. And here, the psyplot framework helps you with several attributes of the
:class:`Formatoption` class:

the :attr:`~Formatoption.children` attribute
    Forces the listed formatoptions in this list to be updated before the
    current formatoption is updated
the :attr:`~Formatoption.dependencies` attributes
    Same as :attr:`~Formatoption.children` but also forces an update if one
    of the named formatoptions are updated
the :attr:`~Formatoption.parents` attribute
    Skip the update if one of the :attr:`~Formatoption.parents` is updated
the :attr:`~Formatoption.connections` attribute
    just provides connections to the listed formatoptions

Each of those attributes accept a list of strings that represent the
formatoption keys of other formatoptions. Those formatoptions are then
accessible within the formatoption via the usual :func:`getattr`. I.e. if you
list a formatoption in the :attr:`~Formatoption.children` attribute, you can
access it inside the formatoption (``self``) via ``self.other_formatoption``.

In our example of the ``CustomText``, this could be implemented via

.. code-block:: python

    class CustomTextSize(Formatoption):
        """
        Set the fontsize of the custom text

        Possible types
        --------------
        int
            The fontsize of the text
        """

        default = int

        def validate(self, value):
            return int(value)

        # this text has not to be updated if the custom text is updated
        children = ['text']

        def update(self, value):
            self.text.text.set_fontsize(value)


    class CustomText(Formatoption):
        """
        Place a text

        Possible types
        --------------
        str
            The text to display""""

        def initialize_plot(self, value):
            self.text = self.ax.text(0.2, 0.2, value['text'])

        def update(self, value):
            self.text.set_text(value)


    class MyPlotter(Plotter):

        my_fmt = CustomText('my_fmt')
        my_fmtsize = CustomTextSize('my_fmtsize', text='my_fmt')

the update in that sense would be like

and then you could create and update a plotter via

.. code-block:: python

    p = MyPlotter(xarray.DataArray([]))
    p.update(my_fmt='my text')  # updates the text
    p.update(my_fmtsize=14)  # updates the size
    p.update(my_fmt='Something', my_fmtsize=14)  # updates text and size

The advantages of this methodology are basically:

- The user straight away sees two formatoptions that can be interpreted
  easiliy
- The formatoption that controls the font size could easily be subclassed and
  replaced in a subclass of ``MyPlotter``. In the first framework using the
  :class:`DictFormatoption`, this would mean that the entire process has to be
  rewritten.

  As you see in the above definition
  ``my_fmtsize = CustomTextSize('my_fmtsize', text='my_fmt')``, we provide an
  additional ``text`` keyword. That is because we explicitly named the
  ``text`` key in the ``children`` attribute of the ``CustomTextSize``
  formatoption. In that way we can tell the ``my_fmtsize`` formatoption how to
  find the necessary formatoption. That works for all keys listed in the
  :attr:`~Formatoption.children`, :attr:`~Formatoption.dependencies`,
  :attr:`~Formatoption.parents` and :attr:`~Formatoption.connections`
  attributes.


.. _new_plugins:

Creating new plugins
--------------------
Now that you have created your plotter, you may want to include it in the
plot methods of the :class:`~psyplot.project.Project` class such that you can
do something like

.. code-block:: python

    import psyplot.project as psy
    psy.plot.my_plotter('netcdf-file.nc', name='varname')

There are three possibilities how you can do this:

1. The easy and fast solution for one session: register the plotter using the
   :func:`psyplot.project.register_plotter` function
2. The easy and steady solution: Save the calls you used in step 1 in the
   ``'project.plotter.user'`` key of the
   :attr:`~psyplot.config.rcsetup.rcParams`
3. The steady and shareable solution: Create a new plugin

The third solution has been used for the psy-maps_ and psy-simple plugins. To
create a skeleton for your plugin, you can use the ``psyplot-plugin`` command
that is installed when you install psyplot.

For our demonstration, let's create a plugin named my-plugin. This is simply
done via

.. ipython::

    In [1]: !psyplot-plugin my-plugin

    In [2]: !tree my-plugin

The following files are created in a directory named ``'my-plugin'``:

``'setup.py'``
    The installation script
``'my-plugin/plugin.py'``
    The file that sets up the configuration of our plugin. This file should
    define the ``rcParams`` for the plugin
``'my-plugin/plotters.py'``
    The file in which we define the plotters. This file should define the
    plotters and formatoptions.

If you want to see more, look into the comments in the created files.

.. ipython::

    @suppress
    In [3]: !rm -r my-plugin
