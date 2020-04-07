v1.2.2
======
Added
-----
* `psyplot.data.open_dataset` now decodes grid_mappings attributes,
see `#17 <https://github.com/psyplot/psyplot/pull/17>`__

Changed
-------
* psyplot has been moved from https://github.com/Chilipp/psyplot to https://github.com/psyplot/psyplot,
  see `#16 <https://github.com/psyplot/psyplot/pull/16>`__
* Specifying names in `x`, `y`, `t` and `z` attributes of the `CFDecoder` class
  now means that any other attribute (such as the `coordinates` or `axis` attribute)
  are ignored


v1.2.1
======
This patch fixes compatibility issues with xarray 0.12 and cdo 1.5. Additionally we now officially drop support for python 2.7.

v1.2.0
======

Added
-----
* The ``psyplot.plotter.Plotter.initialize_plot`` method now takes a
  *priority* keyword to only initialize only formatoptions of a certain
  priority

Removed
-------
* The installers from the `psyplot-conda <https://github.com/Chilipp/psyplot-conda>`__
  repositories have been depreceated. Instead, now download the latest
  `miniconda <https://conda.io/miniconda.html>`__ and install psyplot and the
  plugins via ``conda install -c conda-forge psy-maps psyplot-gui psy-reg``

Changed
-------
* We generalized the handling of unstructured data as lined out in
  `issue#6 <https://github.com/psyplot/psyplot/issues/6>`__. The new method
  ``psyplot.data.CFDecoder.get_cell_node_coord`` returns the coordinates of the
  nodes for a given grid cell. These informations are used by the
  psy-simple and psy-maps plugins for displaying any unstructured data. See
  also the example on the
  `visualization of unstructured grids <https://psyplot.readthedocs.io/projects/psy-maps/en/master/examples/example_ugrid.html#gallery-examples-example-ugrid-ipynb>`__
* We removed the inplace parameter for the CFDecoder methods since it is
  deprecated with xarray 0.12 (see
  `issue #8 <https://github.com/psyplot/psyplot/issues/8>`__). The
  ``CFDecoder.decode_ds`` method now always decodes inplace

v1.1.0
======
This new release mainly adds new xarray accossors (``psy``) for DataArrays
and Datasets. Additionally we provide methods to calculate the spatially
weighted mean, such as fldmean, fldstd and fldpctl.

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
* Added the ``chname`` parameter when loading a project. This parameter can
  be used to display another variable from the dataset than the one stored
  in the psyplot project file
* Added the ``gridweights``, ``fldmean``, ``fldstd`` and ``fldpctl`` methods
  to the ``psy`` DataArray accessor to calculate weighted means, standard
  deviations and percentiles over the spatial dimensions (x- and y).
* Added the ``additional_children`` and ``additional_dependencies`` parameters
  to the Formatoption intialization. These parameters can be used to provide
  additional children for a formatoption for one plotter class
* We added the ``psyplot.plotter.Formatoption.get_fmt_widget`` method which can
  be implemented to insert widgets in the formatoptions widget of the
  graphical user interface


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


.. _psy-simple: https://github.com/psyplot/psy-simple
.. _psy-maps: https://github.com/psyplot/psy-maps
.. _psy-reg: https://github.com/psyplot/psy-reg
