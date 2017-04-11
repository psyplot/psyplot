.. _plugins:

Psyplot plugins
===============
psyplot only provides the abstract framework on how to make the interactive
visualization and data analysis. The real work is implemented in
:ref:`plugins to this framework <plugins_guide>`. Each
plugin is a separate package that has to be installed independent of psyplot and
each plugin registers new plot methods for :attr:`psyplot.project.plot`.

.. _existing_plugins:

Existing plugins
----------------

:mod:`psy_simple.plugin`
    A psyplot plugin for simple visualization tasks. This plugin provides a
    bases for all the other plugins

    - :ref:`Examples Gallery <psy_simple:gallery_examples>`
    - plot methods

      :attr:`psy_simple:psyplot.project.plot.density`
          Make a density plot of point data
      :attr:`psy_simple:psyplot.project.plot.plot2d`
          Make a simple plot of a 2D scalar field
      :attr:`psy_simple:psyplot.project.plot.combined`
          Plot a 2D scalar field with an overlying vector field
      :attr:`psy_simple:psyplot.project.plot.violinplot`
          Make a violin plot of your data
      :attr:`psy_simple:psyplot.project.plot.lineplot`
          Make a line plot of one-dimensional data
      :attr:`psy_simple:psyplot.project.plot.vector`
          Make a simple plot of a 2D vector field
      :attr:`psy_simple:psyplot.project.plot.barplot`
          Make a bar plot of one-dimensional data
:mod:`psy_maps.plugin`
    A psyplot plugin for visualizing data on a map

    - :ref:`Examples Gallery <psy_maps:gallery_examples>`
    - plot methods

      :attr:`psy_maps:psyplot.project.plot.mapplot`
          Plot a 2D scalar field on a map
      :attr:`psy_maps:psyplot.project.plot.mapvector`
          Plot a 2D vector field on a map
      :attr:`psy_maps:psyplot.project.plot.mapcombined`
          Plot a 2D scalar field with an overlying vector field on a map
:mod:`psy_reg.plugin`
    A psyplot plugin for visualizing and calculating regression fits

    - :ref:`Examples Gallery <psy_reg:gallery_examples>`
    - plot methods

      :attr:`psy_reg:psyplot.project.plot.densityreg`
          Make a density plot and draw a fit from x to y of points
      :attr:`psy_reg:psyplot.project.plot.linreg`
          Draw a fit from x to y

If you have new plugins that you think should be included in this list, please
do not hesitate to open an issue on the `github project page of psyplot`_.

.. note::

    Because psyplot plugins are imported right at the startup time of psyplot
    but nevertheless use the :class:`psyplot.config.rcsetup.RcParams` class,
    you always have to import psyplot first if you want to load a psyplot
    plugin. In other words, if you want to import one of the above mentiond
    modules manually, you always have to type

    .. code-block:: python

        import psyplot
        import PLUGIN_NAME.plugin

    instead of

    .. code-block:: python

        import PLUGIN_NAME.plugin
        import psyplot

    where ``PLUGIN_NAME`` is any of ``psy_simple, psy_maps``, etc.

.. _github project page of psyplot: https://github.com/Chilipp/psyplot


.. _excluding_plugins:

How to exclude plugins
----------------------
The psyplot package loads all plugins right when the `psyplot` is imported. In
other words,  the statement

.. code-block:: python

    import psyplot

already includes that all the psyplot plugin packages are loaded.

You can however exclude plugins from the automatic loading via the
``PSYPLOT_PLUGINS`` environment variable and exclude specific plot methods of a
plugin via the ``PSYPLOT_PLOTMETHODS`` variable.

.. _plugins_env:

The ``PSYPLOT_PLUGINS`` environment variable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This environment variable is a ``::`` separated string with plugin names. If a
plugin name is preceded by a ``no:``, this plugin is excluded. Otherwise, only
this plugin is included.

To show this behaviour, we can use ``psyplot --list-plugins`` which shows the
plugins that are used. By default, all plugins are included

.. ipython::

    In [1]: !psyplot --list-plugins

Excluding psy-maps works via

.. ipython::

    In [2]: !PSYPLOT_PLUGINS=no:psy_maps.plugin psyplot --list-plugins

Including only psy-maps works via

.. ipython::

    In [3]: !PSYPLOT_PLUGINS='yes:psy_maps.plugin' psyplot --list-plugins


.. _plot_methods_env:

The ``PSYPLOT_PLOTMETHODS`` environment variable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The same principle is used when the plot methods are loaded from the plugins.
If you want to manually exclude a plot method from loading, you include it via
``no:<plugin-module>:<plotmethod>``. For example, to exclude the
:attr:``mapplot <psy_maps:psyplot.project.plot.mapplot>`` plot method from the
psy-maps plugin, you can use

.. ipython::

    In [4]: !PSYPLOT_PLOTMETHODS=no:psy_maps.plugin:mapplot psyplot --list-plot-methods

and the same if you only want to include the
:attr:``mapplot <psy_maps:psyplot.project.plot.mapplot>`` and the
:attr:``lineplot <psy_simple:psyplot.project.plot.lineplot>`` methods

.. ipython::

    In [4]: !PSYPLOT_PLOTMETHODS='yes:psy_maps.plugin:mapplot::yes:psy_simple.plugin:lineplot' psyplot --list-plot-methods
