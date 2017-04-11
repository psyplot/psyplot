v1.0.0
======

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
    to the psy-simple package
  - The psyplot.plotter.maps and boxes modules have been moved to the psy-maps
    package
  - The psyplot.plotter.linreg module has been moved to the psy-fit package
* The endings of the yaml configuration files are now all *.yml*. Hence,

  - the configuration file name is now *psyplotrc.yml* instead of
    *psyplotrc.yaml*
  - the default logging configuration file name is now *logging.yml* instead
    of *logging.yaml*
* Under osx, the configuration directory is now also expected to be in
  ``$HOME/.config/psyplot`` (as it is for linux)
