v1.1.0
======
Added
-----
* The yaxis_inverted and xaxis_inverted is now considered when loading and
  saving a matplotlib axes
* Added the ``seaborn-style`` command line argument
* Added the ``concat_dim`` command line argument
* Added the plot attribute to the DataArray and Dataset accessors. It is now
  possible to plot directly from the dataset and the data array
* Added ``requires_replot`` attribute for the ``Formatoption`` class. If this
  attribute is True and the formatoption is contained in an update, it is the
  same as calling ``Plotter.update(replot=True))``.
* We added support for multifile datasets when saving a project.
  Multifile datasets are datasets that have been opened with, e.g.
  ``psyplot.data.open_mfdataset`` or
  ``psyplot.project.plot.<plotmethod>(..., mfmode=True)``. This however does
  not always work with datasets opened with ``xarray.open_mfdataset``. In these
  cases, you have to set the ``Dataset.psy._concat_dim`` attribute manually


v1.0.0
======
.. image:: https://zenodo.org/badge/87944102.svg
   :target: https://zenodo.org/badge/latestdoi/87944102

Added
-----
* Changelog

Changed
-------
* When creating new plots using the ``psyplot.project.Project.plot`` attribute,
  ``scp`` for the newly created subproject is only called when the
  corresponding ``Project`` is the current main project (``gcp(True)``)
* The ``alternate_paths`` keyword in the ``psyplot.project.Project.save_project``
  and ``psyplot.data.ArrayList.array_info`` methods has been changed to
  ``alternative_paths``
* The ``psyplot.project.Cdo`` class does not accept any of the keywords
  ``returnDA, returnMaps`` or ``returnLine`` anymore. Instead it takes
  the ``plot_method`` keyword and several others.
* The ``psyplot.project.close`` method by default now removes the data from
  the current project and closes attached datasets
* The modules in the psyplot.plotter modules have been moved to separate
  packages to make the debugging and testing easier

  - The psyplot.plotter.simple, baseplotter and colors modules have been moved
    to the psy-simple_ package
  - The psyplot.plotter.maps and boxes modules have been moved to the psy-maps_
    package
  - The psyplot.plotter.linreg module has been moved to the psy-reg_ package
* The endings of the yaml configuration files are now all *.yml*. Hence,

  - the configuration file name is now *psyplotrc.yml* instead of
    *psyplotrc.yaml*
  - the default logging configuration file name is now *logging.yml* instead
    of *logging.yaml*
* Under osx, the configuration directory is now also expected to be in
  ``$HOME/.config/psyplot`` (as it is for linux)


.. _psy-simple: https://github.com/Chilipp/psy-simple
.. _psy-maps: https://github.com/Chilipp/psy-maps
.. _psy-reg: https://github.com/Chilipp/psy-reg
