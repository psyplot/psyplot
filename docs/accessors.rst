.. _accessors:

.. currentmodule:: psyplot.data

xarray Accessors
================
psyplot defines a :class:`~xarray.DataArray` and a :class:`~xarray.Dataset`
accessor. You can use these accessors (see :ref:`xarray:internals`) to
visualize your data and to update your plots.

.. _dataset-accessor:

The :class:`DatasetAccessor` dataset accessor
---------------------------------------------
Importing the psyplot package registers a new dataset accessor (see
:func:`xarray.register_dataset_accessor`), the
:class:`DatasetAccessor`. You can access it via the ``psy``
attribute of the :class:`~xarray.Dataset` class, i.e.

.. autosummary::

    xarray.Dataset.psy

It can be used to visualize the variables in the dataset directly from the
dataset itself, e.g.

.. ipython::

    In [1]: import psyplot

    In [2]: ds = psyplot.open_dataset('demo.nc')

    @savefig docs_dataset_accessor.png width=4in
    In [3]: sp = ds.psy.plot.mapplot(name='t2m', cmap='Reds')

The variable ``sp`` is a psyplot subproject of the current main project.

.. ipython::

    In [4]: print(sp)

    @suppress
    In [4]: import psyplot.project as psy
       ...: psy.close('all')

Hence, it would be completely equivalent if you type

.. ipython::
    :verbatim:

    In [5]: import psyplot.project as psyplot

    In [6]: sp = psy.plot.mapplot(ds, name='t2m', cmap='Reds')

Note that the :attr:`DatasetAccessor.plot` attribute has the
same plotmethods as the :attr:`psyplot.project.plot` instance.


.. _dataarray-accessor:

The :class:`InteractiveArray` dataarray accessor
------------------------------------------------
More advanced then the :ref:`dataset accessor <dataset-accessor>` is the
registered DataArray accessor, the :class:`InteractiveArray`.

As well as the :class:`DatasetAccessor`, it is registered as the ``'psy'``
attribute of any :class:`~xarray.DataArray`, i.e.

.. autosummary::

    xarray.DataArray.psy

You can use it for two things:

1. create plots of the array
2. update the plots and the array

.. _dataarray-accessor-plot:

Creating plots with the dataarray accessor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Just use the :attr:`~psyplot.data.InteractiveBase.plot` attribute the accessor.

.. ipython::

    In [1]: import psyplot

    In [2]: ds = psyplot.open_dataset('demo.nc')

    In [3]: da = ds.t2m[0, 0]

    # this is a two dimensional array
    In [4]: print(da)

    # and we can plot it using the mapplot plot method
    @savefig docs_dataarray_accessor_1.png width=4in
    In [5]: plotter = da.psy.plot.mapplot()

    @suppress
    In [6]: import matplotlib.pyplot as plt
       ...: plt.close('all', ds=False)

The resulting plotter, an instance of the :class:`psyplot.plotter.Plotter`
class, is the object that visualizes the data array. It can also
be accessed via the ``da.psy.plotter`` attribute. Note that the creation of
such a plotter overwrites any previous plotter in the ``da.psy.plotter``
attribute.

This methodology does not only work for :class:`DataArrays <xarray.DataArray>`,
but also for multiple DataArrays in a :class:`InteractiveList`. This data
structure is, for example, used by the
:attr:`psy_simple:psyplot.project.plot.lineplot` plot method to visualize
multiple lines. Consider the following example:

.. ipython::

    In [7]: ds0 = ds.isel(lev=0)  # select a subset of the dataset

    # create a list of arrays at different longitudes
    In [8]: l = psyplot.InteractiveList([
       ...:     ds0.t2m.sel(lon=2.35, lat=48.86, method='nearest'),  # Paris
       ...:     ds0.t2m.sel(lon=13.39, lat=52.52, method='nearest'),  # Berlin
       ...:     ds0.t2m.sel(lon=-74.01, lat=40.71, method='nearest'),  # NYC
       ...:     ])

    In [9]: l.arr_names = ['Paris', 'Berlin', 'NYC']

    # plot the list
    @savefig docs_dataarray_accessor_2.png width=4in
    In [10]: plotter = l.psy.plot.lineplot(xticks='data', xticklabels='%B')

    @suppress
    In [10]: import matplotlib.pyplot as plt
       ....: plt.close('all')

Note that for the :class:`InteractiveList`, the :attr:`~InteractiveList.psy`
attribute is just the list it self. So it would have been equivalent to call

.. ipython::
    :verbatim:

    In [11]: l.plot.lineplot()

.. _dataarray-accessor-update:

Updating plots and arrays with the dataarray accessor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The :class:`InteractiveArray` accessor is designed for interactive usage of,
not only the matplotlib figures, but also of the data. If you selected a
subset of a dataset, e.g. via

.. ipython::

    In [1]: da = ds.t2m[0, 0]
       ...: print(da.time) # January 1979

You can change to a different slice using the :meth:`InteractiveArray.update`
method.

.. ipython::

    In [2]: da.psy.base = ds   # tell psyplot the source of the dataarray

    In [3]: da.psy.update(time=2)
       ...: print(da.time)  # changed to March 1979

The ``da.psy.base = ds`` command hereby tells the dataarray, where it is
coming from, since this information is not known in the standard
xarray framework.

.. hint::

    You can avoid this, using the :meth:`DatasetAccessor.create_list` method
    of the dataset accessor

    .. ipython::

        In [4]: da = ds.psy.create_list(time=0, lev=0, name='t2m')[0]
           ...: print(da.psy.base is ds)

If you plotted the data, you can also change the formatoptions using the
:meth:`~InteractiveArray.update` method, e.g.

.. ipython::

    # create plot
    @savefig docs_dataarray_accessor_3.png width=4in
    In [5]: da.psy.plot.mapplot();

.. ipython::

    @savefig docs_dataarray_accessor_4.png width=4in
    In [6]: da.psy.update(cmap='Reds')

    @suppress
    In [6]: import matplotlib.pyplot as plt
       ...: plt.close('all')

The same holds for the Interactive list

.. ipython::

    @suppress
    In [6]: plotter = l.psy.plot.lineplot(xticks='data', xticklabels='%B')

    @savefig docs_dataarray_accessor_5.png width=4in
    In [7]: l.update(time=slice(1, 4),  # change the data by selecting a subset of the timeslice
       ...:          title='Subset',    # change a formatoption, the title of the plot
       ...:          )
