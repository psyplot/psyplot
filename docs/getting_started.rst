.. _getting-started:

Getting startet
===============

.. include:: <isonum.txt>

.. currentmodule:: psyplot.project


Initialization and interactive usage
------------------------------------

This section shall introduce you how to read data from a netCDF file and
visualize it via psyplot. For this, you need to have netCDF4_ and and the to be
psy-maps_ psyplot plugin to be installed (see :ref:`install`).

Furthermore we use the :download:`demo.nc` netCDF file for our
demonstrations.

.. _netCDF4: https://github.com/Unidata/netcdf4-python
.. _psy-maps: https://psy-maps.readthedocs.io/en/latest

After you :ref:`installed psyplot <install>`, you can import the package via

.. ipython::

    In [1]: import psyplot

Psyplot has several modules and subpackages. The main module for the use of
psyplot is the :mod:`~psyplot.project` module.

.. ipython::

    In [2]: import psyplot.project as psy

Plots can be created using the attributes of the :attr:`plot` instance of
the :class:`ProjectPlotter`.

Each new plugin defines several plot methods. In case of the psy-maps_
package, those are

.. ipython::

    In [3]: psy.plot.show_plot_methods()

So to create a simple 2D plot of the temperature field ``'t2m'``, you can
type

.. ipython::

    @savefig docs_getting_started.png width=4in
    In [4]: p = psy.plot.mapplot('demo.nc', name='t2m')

Now you created your first project

.. ipython::

    In [5]: p

which contains the :class:`xarray.DataArray` that stores the data and the
corresponding plotter that visualizes it

.. ipython::

    In [6]: p[0]

    In [7]: type(p[0].psy.plotter)

The visualization and data handling within the psyplot framework is designed to
be as easy, flexible and interactive as possible. The appearance of a plot is
controlled by the formatoptions of the plotter. In our case, they are the
following:

.. ipython::

    In [8]: p.keys()

they can be investigated through the :meth:`Project.keys`,
:meth:`~Project.summaries` and :meth:`~Project.docs`, or the corresponding
low level methods of the :class:`~psyplot.plotter.Plotter` class,
:meth:`~psyplot.plotter.Plotter.show_keys`,
:meth:`~psyplot.plotter.Plotter.show_summaries` and
:meth:`~psyplot.plotter.Plotter.show_docs`.

Updating a formatoption is straight forward. Each formatoption accepts a certain
type of data. Let's say, we want to have a different projection. Then we can
look at the types this formatoption accepts using the :meth:`Project.docs`

.. ipython::

    In [9]: p.docs('projection')

Let's use an orthogonal projection. The update goes via the
:meth:`Project.update` method which goes all the way down to the
:meth:`psyplot.plotter.Plotter.update` and the
:meth:`psy_maps.plotters.Projection.update` method of the formatoption.

.. ipython::

    @savefig docs_getting_started_1.png width=4in
    In [10]: p.update(projection='ortho')

.. note::

    Actually, in this case an update of the projection requires that the entire
    axes is cleared and the plot is drawn again. If you want to know more about
    it, check the :attr:`~psyplot.plotter.Formatoption.requires_clearing`
    attribute of the formatoption.

Our framework also let's us update the dimensions of the data we show. For
example, if we want to display the field for february, we can type

.. ipython::

    # currently we are displaying january
    In [11]: p[0].time.values

    In [12]: p.update(time='1979-02', method='nearest')

    # now its february
    In [13]: p[0].time.values

which is in our case equivalent for choosing the second index in our time
coordinate via

.. ipython::
    :verbatim:

    In [14]: p.update(time=1)

So far for the first quick introduction. If you are interested you are welcomed
to visit our :ref:`example galleries <plugins>` or continue with this
guide.

In the end, don't forget to close the project in order to delete the data from
the memory and close the figures

.. ipython::

    In [15]: p.close(True, True, True)

.. _intro_dims:

Choosing the dimension
----------------------

As you saw already above, the scalar variable ``'t2m'`` has multiple time
steps and we can control what is shown via the :meth:`~Project.update`
method. By default, the :meth:`~psyplot.project.ProjectPlotter.mapplot`
plot method chooses the first time step and the first vertical level
(if those dimensions exist).

However, you can also specify the exact data slice for your visualization based
upon the dimensions in you dataset. When doing that, you basically do not have
to care about the exact dimension names in the netCDF files, because those are
decoded following the `CF Conventions <http://cfconventions.org/>`__. Hence
each of the above dimensions are assigned to one of the general dimensions
``'t'`` (time), ``'z'`` (vertical dimension), ``'y'`` (horizontal North-South
dimension) and ``'x'`` (horizontal East-West dimension). In our demo file,
the dimensions are therefore decoded as ``'time'`` |rarr| ``'t'``,
``'lev'`` |rarr| ``'z'``, ``'lon'`` |rarr| ``'x'``,
``'lat'`` |rarr| ``'y'``.

Hence it is equivalent if you type

.. ipython::

    In [7]: psy.plot.mapplot('demo.nc', name='t2m', t=1)

    @suppress
    In [8]: psy.close('all')

or

.. ipython::

    In [8]: psy.plot.mapplot('demo.nc', name='t2m', time=1)

    @suppress
    In [8]: psy.close('all')

Finally you can also be very specific using the `dims` keyword via

.. ipython::

    In [9]: psy.plot.mapplot('demo.nc', name='t2m', dims={'time': 1})

    @suppress
    In [8]: psy.close('all')

You can also use the `method` keyword from the plotting function to use the
advantages of the :meth:`xarray.DataArray.sel` method. E.g. to plot the data
corresponding to March 1979 you can use

.. ipython::

    In [10]: psy.plot.mapplot('demo.nc', name='t2m', t='1979-03',
       ....:                  method='nearest', z=100000)

    @suppress
    In [8]: psy.close('all')

.. note::

    If your netCDF file does (for whatever reason) not follow the CF Conventions,
    we interprete the last dimension as the *x*-dimension, the second
    last dimension (if existent) as the *y*-dimension, the third last dimension as
    the *z*-dimension. The time dimension however has to have the name
    ``'time'``. If that still does not fit your netCDF files, you can specify
    the correct names in the :attr:`~psyplot.config.rcsetup.rcParams`, namely

    .. ipython::

        In [11]: psy.rcParams.find_all('decoder.(x|y|z|t)')

.. _intro_fmt:

Configuring the appearance of the plot
--------------------------------------

psyplot is build upon the great and extensive features of the matplotlib
package. Hence, our framework can in principle be seen as a high-level
interface to the matplotlib functionalities. However you can always access
the basic matplotlib objects like figures and axes if you need.

In the psyplot framework, the communication to matplotlib is done via
*formatoptions* that control the appearence of a plot. Each plot method
(i.e. each attribute of :attr:`psyplot.project.plot`) has several a set of
them and they set up the corresponding plotter.

Formatoptions are all designed for an interactive usage and can usually be
controlled with very simple commands. They range from simple formatoptions
like :attr:`choosing the title <psy_simple.plotters.Simple2DPlotter.title>` to
:attr:`choosing the latitude-longitude box of the data <psy_maps.plotters.FieldPlotter.lonlatbox>`.

The formatoptions depend on the specific plotting method and can be seen via
the methods

.. autosummary::

    ~psyplot.project.PlotterInterface.keys
    ~psyplot.project.PlotterInterface.summaries
    ~psyplot.project.PlotterInterface.docs

For example to look at the formatoptions of the
:attr:`~psyplot.project.ProjectPlotter.mapplot` method in an interactive
session, type

.. ipython::

    In [24]: psy.plot.mapplot.keys(grouped=True)  # to see the fmt keys

    In [25]: psy.plot.mapplot.summaries(['title', 'cbar'])  # to see the fmt summaries

    In [26]: psy.plot.mapplot.docs('title')  # to see the full fmt docs

But of course you can also use the
:class:`online documentation <psyplot.project.ProjectPlotter>` of the
method your interested in.

To include a formatoption from the beginning, you can simply pass in the key
and the desired value as keyword argument, e.g.

.. ipython::

    In [27]: psy.plot.mapplot('demo.nc', name='t2m', title='my title',
       ....:                  cbar='r')

    @suppress
    In [28]: psy.close('all')

This works generally well as long as there are no dimensions in the desired
data with the same name as one of the passed in formatoptions. If you want to
be really sure, use the `fmt` keyword via

.. ipython::

    In [28]: p psy.plot.mapplot('demo.nc', name='t2m', fmt={'title': 'my title',
       ....:                                                'cbar': 'r'})

The same methodology works for the interactive usage, i.e. you can use

.. ipython::

    In [29]: p.update(title='my title', cbar='r')

    # or
    In [30]: p.update(fmt={'title': 'my title', 'cbar': 'r'})

    @suppress
    In [28]: psy.close('all')


.. _intro_update:

Controlling the update
----------------------

.. _intro_auto_updates:

Automatic update
^^^^^^^^^^^^^^^^

By default, a call of the :meth:`~psyplot.data.ArrayList.update` method
forces an automatic update and redrawing of all the plots. There are
however several ways to modify this behavior:

1. Changing the behavior of one single project

   1. in the initialization of a project using the `auto_update` keyword

      .. ipython::

        In [9]: p = psy.plot.mapplot('demo.nc', name='t2m', auto_update=False)

   2. setting the :attr:`~psyplot.data.ArrayList.no_auto_update` attribute

      .. ipython::

        In [10]: p.no_auto_update = True

2. Changing the default configuration in the ``'lists.auto_update'``
   key in the :attr:`~psyplot.config.rcsetup.rcParams`

    .. ipython::

        In [11]: psy.rcParams['lists.auto_update'] = False

        @suppress
        In [11]: psy.rcParams['lists.auto_update'] = True

3. Using the :attr:`~psyplot.data.ArrayList.no_auto_update` attribute as a
   context manager

   .. ipython::

        In [12]: with p.no_auto_update:
           ....:    p.update(title='test')

If you disabled the automatical update via one of the above methods, you have
to start the registered updates manually via

.. ipython::

    In [12]: p.update(auto_update=True)

    # or
    In [13]: p.start_update()

    @suppress
    In [28]: psy.close('all')


Direct control on formatoption update
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, when updating a formatoption, it is checked for each plot whether
the formatoption would change during the update or not. If not, the
formatoption is not updated. However, sometimes you may want to do that and
for this, you can use the *force* keyword in the
:meth:`~psyplot.data.ArrayList.update` method.


.. _intro_multiple:

Creating and managing multiple plots
------------------------------------

Creating multiple plots
^^^^^^^^^^^^^^^^^^^^^^^

One major advantage of the psyplot framework is the systematic management of
multiple plots at the same time. To create multiple plots, simply pass in a
list of dimension values and/or names. For example

.. ipython::

    In [12]: psy.plot.mapplot('demo.nc', name='t2m', time=[0, 1])

    @suppress
    In [12]: psy.close('all')

created two plots: one for the first and one for the second time step.

Furthermore

.. ipython::

    In [13]: psy.plot.mapplot('demo.nc', name=['t2m', 'u'], time=[0, 1])

    @suppress
    In [13]: psy.close('all')

created four plots. By default, each plot is made in an own figure but you can
also use the `ax` keyword to setup how the plots will be arranged. The `sort`
keyword allows you to sort the plots.

As an example we plot the variables ``'t2m'`` and ``'u'`` for the first and
second time step into one figure and sort by time. This will produce

.. ipython::

    @savefig docs_multiple_plots.png width=4in
    In [16]: psy.plot.mapplot(
       ....:     'demo.nc', name=['t2m', 'u'], time=[0, 1], ax=(2, 2), sort=['time'],
       ....:     title='%(long_name)s, %b')

    @suppress
    In [18]: psy.close('all')

.. warning::

    As the xarray package, the slicing is based upon positional indexing with
    lists (see `the xarray documentation on ositional indexing
    <http://xarray.pydata.org/en/stable/indexing.html#positional-indexing>`__).
    Hence you might think of choosing your data slice via
    ``psy.plot.mapplot(..., x=[1, 2, 3, 4, 5], ...)``. However this would result
    in 5 different plots! Instead you have to write
    ``psy.plot.mapplot(..., x=[[1, 2, 3, 4, 5]], ...)``. The same is true
    for plotting methods like the
    :attr:`~psyplot.project.ProjectPlotter.mapvector` method. Since this
    method needs two variables (one for the latitudinal and one for the
    longitudinal direction), typing

    .. ipython::
        :verbatim:

        In [18]:  psy.plot.mapvector('demo.nc', name=['u', 'v'])
        ValueError: Can only plot 3-dimensional data!

    results in a :class:`ValueError`. Instead you have to write

    .. ipython::

        In [19]: psy.plot.mapvector('demo.nc', name=[['u', 'v']])

        @suppress
        In [20]: psy.close('all')

    Please have a look into the documentations of the
    :attr:`~psyplot.project.ProjectPlotter.mapvector` and
    :attr:`~psyplot.project.ProjectPlotter.mapcombined` for getting examples
    on how to use this methods.

Slicing and filtering the project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Managing a whole lot of plots is basically the same as managing a single plot.
However, you can always get the single array and handle it separately.

You can either get it through the usual list slicing (the :class:`Project` class
actually is a simple :class:`list` subclass) or you can use meta attributes,
dimensions and the specific :attr:`~psyplot.data.InteractiveBase.arr_name`
attribute. For the latter one, just call the project with your filtering
attributes

.. ipython

    @suppress
    In [16]: p = psy.plot.mapplot(
       ....:     'demo.nc', name=['t2m', 'u'], time=[0, 1], ax=(2, 2), sort=['time'],
       ....:     title='%(long_name)s, %b')

    In [20]: p(t=0)

    In [21]: p(t='1979-01')

    In [22]: p(name='t2m')

    In [23]: p(long_name='Temperature')

This behavior is especially useful if you want to address only some arrays
with your update. For example, let's consider we want to choose a ``'winter'``
colormap for the zonal wind variable and a colormap ranging from blue to red
for the temperature. Then we could do this via

.. ipython::

    In [24]: p(name='t2m').update(cmap='RdBu_r')

    In [26]: p(name='u').update(cmap='winter')

.. note::

    When doing so, we recommend to temporarily disable the automatic update
    because then the figure will only be drawn once and the update will be
    done in parallel.

    Hence, it is better to use the context manager
    :attr:`~psyplot.data.ArrayList.no_auto_update` (see :ref:`intro_auto_updates`)

    .. ipython::

        In [27]: with p.no_auto_update:
           ....:     p(name='t2m').update(cmap='RdBu_r')
           ....:     p(name='u').update(cmap='winter')
           ....:     p.start_update()

        @suppress
        In [28]: p.close(True, True)

Finally you can access the plots created by a specific plotting method
through the corresponding attribute in the :class:`~psyplot.project.Project`
class. In this case this is of course useless because all plots in ``maps``
were created by the same plotting method, but it may be helpful when having
different plotters in one project (see :ref:`framework`). Anyway, the plots
created by the :attr:`~psyplot.project.ProjectPlotter.mapplot` method could be
accessed via

.. ipython::

    In [24]: p.mapplot



.. _save_and_load:

Saving and loading your project
-------------------------------

Within the psyplot framework, you can also save and restore your plots easily
and flexibel.

To save your project, use the :meth:`~psyplot.project.Project.save_project`
method:

.. ipython::

    @suppress
    In [28]: p = psy.plot.mapplot('demo.nc', name='t2m', time=[0, 1], ax=(1, 2))

    In [28]: p.save_project('my_project.pkl')

This saves the plot-settings into the file ``'my_project.pkl'``, a simple pickle
file that you could open by yourself using

.. ipython::

    In [29]: import pickle

    In [30]: with open('my_project.pkl', 'rb') as f:
       ....:     d = pickle.load(f)

    @ suppress
    In [31]: import os
       ....: os.remove('my_project.pkl')

In order to not avoid large project files, we do not store the data but only the
filenames of the datasets. Hence, if you want to load the project again, make
sure that the datasets are accessible through the path as they are listed in the
:attr:`~psyplot.project.Project.dsnames` attribute.

Otherwise you have several options to avoid wrong paths:

1. Use the `alternative_paths` parameter and provide for each filename a
   specific path when you *save* the project

   .. ipython::

       In [29]: p.dsnames

       @verbatim
       In [30]: p.save_project(
          ....:     'test.pkl', alternative_paths={'demo.nc': 'other_path.nc'})

2. pack the whole data to the place where you want to store the project file

   .. ipython::

       @verbatim
       In [31]: p.save_project('target-folder/test.pkl', pack=True)

3. specify where the datasets can be found when you *load* the project:

   .. ipython::

       @verbatim
       In [32]: p = psy.Project.load_project(
          ....:     'test.pkl', alternative_paths={'demo.nc': 'other_path.nc'})

4. Save the data in the pickle file, too

    .. ipython::

        @verbatim
        In [33]: p.save_project('test.pkl', ds_description={'arr'})

        @suppress
        In [33]: psy.close('all')

To restore your project, simply use the
:meth:`~psyplot.project.Project.load_project` method via

.. ipython::

    @verbatim
    In [33]: maps = psy.Project.load_project('test.pkl')

.. note::

    Saving a project stores the figure informations like axes positions,
    background colors, etc. However only the axes informations from from the
    axes within the project are stored. Other axes in the matplotlib figures are
    not considered and will not be restored. You can, however, use the
    `alternative_axes` keyword in the :meth:`Project.load_project` method if
    you want to restore your settings and/or customize your plot with the
    :attr:`~psyplot.plotter.Plotter.post` formatoption (see
    :ref:`own-scripts`)


.. _own-scripts:

Adding your own script: The :attr:`~psyplot.plotter.Plotter.post` formatoption
------------------------------------------------------------------------------
Very likely, you will face the problem that not all your needs are satisfied
by the formatoptions in one plotter. You then have two choices:

1. define your own plotter with new formatoptions (see :ref:`plugins_guide`)

   Pros
       - more structured approach
       - you can enhance the plotter with other formatoptions afterwards and
         reuse it
   Cons
       - more complicated
       - you always have to ship the module where you define your plotter when
         you want to :ref:`save and load <save_and_load>` your project
       - can get messy if you define a lot of different plotters
2. use the :attr:`~psyplot.plotter.Plotter.post` formatoption

   Pros
       - fast and easy
       - easy to :ref:`save and load <save_and_load>`
   Cons
       - may get complicated for large scripts
       - has to be enabled manually by the user

For most of the cases, the :attr:`~psyplot.plotter.Plotter.post` formatoptions
is probably what you are looking for (the first option is described in our
:ref:`developers guide <developers-guide>`).

This formatoption is designed for applying your own postprocessing script to
your plot. It accepts a string that is executed using the built-in :func:`exec`
function and is executed at the very end of the plotting. In this python
script, the formatoption itself (and therefore the
:attr:`~psyplot.plotter.Formatoption.plotter` and
:attr:`axes <psyplot.plotter.Formatoption.ax>` can be accessed inside the
script through the ``self`` variable. An example how to handle this
formatoption can be found in
:ref:`our example gallery <gallery_examples_example_post.ipynb>`.
