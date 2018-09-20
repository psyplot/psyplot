.. _configuration:

Configuration
=============

The ``rcParams``
----------------

.. hint::

    If you are using the :ref:`psyplot-gui <psyplot_gui:psyplot-gui>` module,
    you can also use the preferences widget to modify the configuration. See
    :ref:`psyplot_gui:configuration`.

Psyplot, and especially it's plugins have a lot of configuration values.
Our rcParams handling is motivated by
:ref:`matplotlib <matplotlib:matplotlibrc-sample>` although we extended the
possibilities of it's :class:`matplotlib.RcParams` class. Our rcParams
are stored in the :attr:`psyplot.rcParams <psyplot.config.rcsetup.rcParams>`
object. Without any plugins, this looks like

.. ipython::

    @verbatim
    In [1]: from psyplot import rcParams

    @suppress
    In [1]: # is not shown because we have to disable the plugins
       ...: from psyplot.config.rcsetup import RcParams, defaultParams_orig
       ...: rcParams = RcParams(defaultParams=defaultParams_orig)
       ...: rcParams.update_from_defaultParams()

    In [2]: print(rcParams.dump(exclude_keys=[]))

You can use this object like a dictionary and modify the default values. For
example, if you do not want, that the seaborn_ package is imported when the
:mod:`psyplot.project` module is imported, you can simply do this via:

.. ipython::

    In [3]: rcParams['project.import_seaborn'] = False

Additionally, you can make these changes permanent. At every first import of
the ``psyplot`` module, the rcParams are updated from a yaml configuration
file. On Linux and OS X, this is stored under
``$HOME/.config/psyplot/psyplotrc.yml``, under Windows it is stored at
``$HOME/.psyplot/psyplotrc.yml``. But use the
:func:`psyplot.config.rcsetup.psyplot_fname` function, to get the correct
location.

To make our changes from above permanent, we could just do:

.. ipython::

    In [4]: import yaml
       ...: from psyplot.config.rcsetup import psyplot_fname

    In [5]: with open(psyplot_fname(if_exists=False), 'w') as f:
       ...:     yaml.dump({'project.import_seaborn': False}, f)

    # or we use the dump method
    In [6]: rcParams.dump(psyplot_fname(if_exists=False),
       ...:               overwrite=True,  # update the existing file
       ...:               include_keys=['project.import_seaborn'])

Default formatoptions
---------------------

The psyplot plugins, (:mod:`psy_simple.plugin`, :mod:`psy_maps.plugin`, etc.)
define their own :data:`~psy_simple.plugin.rcParams` instance. When the plugins
are loaded at the first import of ``psyplot``, these instances update
:attr:`psyplot.rcParams <psyplot.config.rcsetup.rcParams>`.

The update mainly defines the default values for the plotters defined by that
plugin. However, it is not always obvious, which key in the
:attr:`psyplot.rcParams <psyplot.config.rcsetup.rcParams>` belongs to which
formatoption. For this purpose, however, you can use the
:attr:`~psyplot.plotter.Formatoption.default_key` attribute. For example,
the :attr:`title <psy_simple.plotters.LinePlotter.title>` formatoption has the
default_key

.. ipython::

    In [7]: import psyplot.project as psy

    In [8]: plotter = psy.plot.lineplot.plotter_cls()
       ...: plotter.title.default_key

As our plotters are based on inheritance, the default values use it, too.
Therefore, the :class:`~psy_maps.plotters.FieldPlotter`, the underlying plotter
for the :attr:`~psyplot.Project.ProjectPlotter.mapplot` plot method, uses the
same configuration value in the
:attr:`psyplot.rcParams <psyplot.config.rcsetup.rcParams>`:

.. ipython::

    In [9]: plotter = psy.plot.mapplot.plotter_cls()
       ...: plotter.title.default_key

.. _seaborn: http://seaborn.pydata.org/
