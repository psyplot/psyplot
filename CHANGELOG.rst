v1.4.3
======
Minor fix for grid files (`#53 <https://github.com/psyplot/psyplot/pull/53>__`)

v1.4.2
======
Fix for compatibility with python 3.7

Changed
-------
- plugin entrypoint compatibility fix for python 3.7 (`#47 <https://github.com/psyplot/psyplot/pull/47>`__)
- ignore SNF links in linkcheck (`#49 <https://github.com/psyplot/psyplot/pull/49>`__)
- Replace gitter with mattermost (`#45 <https://github.com/psyplot/psyplot/pull/45>`__)


v1.4.1
======
Compatibility fixes and minor improvements

Added
-----
- An abstract ``convert_coordinate`` method has been implemented for the
  ``Plotter`` and ``Formatoption`` class that can be used in subclasses to
  convert coordinates for the required visualization. The default
  implementation does nothing (see
  `#39 <https://github.com/psyplot/psyplot/pull/39>`__)

Fixed
-----
- the update method now only takes the coordinates that are dimensions in the
  dataset see `#39 <https://github.com/psyplot/psyplot/pull/39>`__
- psyplot is now compatible with matplotlib 3.5 and python 3.10

Changed
-------
- loading more than one variables into a ``DataArray`` now first selects the
  corresponding dimensions, then puts it into a single ``DataArray``. This
  avoids loading the entire data (see
  `#39 <https://github.com/psyplot/psyplot/pull/39>`__)


v1.4.0
======
Compatibility fixes and LGPL license

Fixed
-----
- psyplot is now compatible with 0.18

Added
-----
- psyplot does now have a CITATION.cff file, see https://citation-file-format.github.io

Changed
-------
- psyplot is now officially licensed under LGPL-3.0-only,
  see `#33 <https://github.com/psyplot/psyplot/pull/33>`__
- the lower bound for supported xarray versions is now 0.17.
- project files do not store the Store anymore as this information cannot be
  gathered from xarray 0.18. We now rely on xarray to automatically find the
  engine to open the files.
- Documentation is now hosted with Github Pages at https://psyplot.github.io/psyplot.
  Redirects from the old documentation at `https://psyplot.readthedocs.io` have
  been configured.
- Examples have been removed from the psyplot repository as they now live in a
  central place at https://github.com/psyplot/examples
- We use CicleCI now for a standardized CI/CD pipeline to build and test
  the code and docs all at one place, see `#32 <https://github.com/psyplot/psyplot/pull/32>`__

v1.3.2
======
Fixed
-----
- The ``get_xname``-like methods of the decoder have been fixed if they get a
  variable without any dimensions. See `#30 <https://github.com/psyplot/psyplot/pull/30>`__

v1.3.1
======

Fixed
-----
- 3D bounds of coordinate are not interpreted as unstructured anymore (see
  `660c703 <https://github.com/psyplot/psyplot/commit/660c70303ae3181c03d78a6f984d07fe6e886c07>`__

v1.3.0
======
New repository, presets and compatibility fixes

Added
-----
* You can now save and load presets for the formatoptions of a project which
  applies the formatoptions that you stored in a file to a specific plot method,
  see `#24 <https://github.com/psyplot/psyplot/pull/24>`__
* the ``rcParams`` do now have a ``catch`` method that allows a temporary change
  of formatoptions.

  Usage::

    rcParams['some_key'] = 0
    with rcParams.catch():
        rcParams['some_key'] = 1
        assert rcParams['some_key'] == 1
    assert rcParams['some_key'] == 0

* ``ArrayList.from_dataset`` (and consecutively all plotmethods) now support
  different input types for the decoder. You can pass an instance of the
  ``CFDecoder`` class, a sub class of ``CFDecoder``, or keyword arguments
  that are used to initialize the decoder,
  see `#20 <https://github.com/psyplot/psyplot/pull/20>`__. Furthermore, the
  `check_data` method of the various plotmethods now also accept a `decoder`
  parameter, see `#22 <https://github.com/psyplot/psyplot/pull/22>`__
* ``psyplot.data.open_dataset`` now decodes grid_mappings attributes,
  see `#17 <https://github.com/psyplot/psyplot/pull/17>`__
* psyplot projects now support the with syntax, e.g. something like::

      with psy.plot.mapplot('file.nc') as sp:
          sp.export('output.png')

  sp will be closed automatically (see `#18 <https://github.com/psyplot/psyplot/pull/18>`__)
* the update to variables with other dimensions works now as well
  (see `#22 <https://github.com/psyplot/psyplot/pull/22>`__)
* a ``psyplot.project.Project`` now has a new ``format_string`` method to
  format a string with the meta attributes of the data in the projects
* The ``ArrayList`` class now supports filtering by formatoption keys. You can
  filter for plotters that have a ``cmap`` formatoption via::

    sp1 = psy.plot.mapplot(ds)
    sp2 = psy.plot.lineplot(ds)
    full_sp = sp1 + sp2
    full_sp(fmts='cmap')  # gives equivalent results as addressing sp1 directly

Changed
-------
* psyplot has been moved from https://github.com/Chilipp/psyplot to https://github.com/psyplot/psyplot,
  see `#16 <https://github.com/psyplot/psyplot/pull/16>`__
* Specifying names in `x`, `y`, `t` and `z` attributes of the `CFDecoder` class
  now means that any other attribute (such as the `coordinates` or `axis` attribute)
  are ignored
* If a given variable cannot be found in the provided coords to ``CFDecoder.get_variable_by_axis``,
  we fall back to the ``CFDecoder.ds.coords`` attribute, see `#19 <https://github.com/psyplot/psyplot/pull/19>`__
* A bug has been fixed for initializing a ``CFDecoder`` with ``x, y, z`` and
  ``t`` parameters (see `#20 <https://github.com/psyplot/psyplot/pull/20>`__)


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
  `visualization of unstructured grids <https://psyplot.github.io/examples/maps/example_ugrid.html>`__
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
