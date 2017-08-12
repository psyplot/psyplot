.. _install:

.. highlight:: bash

Installation
============

How to install
--------------

.. _install-standalone:

Installation via standalone installers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. only:: html and not epub

    +--------------+--------------+----------------+
    | | |win-logo| | | |osx-logo| | | |linux-logo| |
    | | Windows    | | Mac OS X   | | Linux        |
    +==============+==============+================+
    | | |win-64|   | | |osx-pkg|  | |linux-64|     |
    | | |win-32|   | | |osx-64|   |                |
    +--------------+--------------+----------------+

    .. |win-logo| image:: windows.png

    .. |linux-logo| image:: linux.png

    .. |osx-logo| image:: apple.png

    .. |win-64| replace:: :psycon:`64-bit (.exe installer) <Windows-x86_64.exe>`

    .. |win-32| replace:: :psycon:`32-bit (.exe installer) <Windows-x86.exe>`

    .. |osx-pkg| replace:: :psycon:`64-bit (.pkg installer) <MacOSX-x86_64.pkg>`

    .. |osx-64| replace:: :psycon:`64-bit (bash installer) <MacOSX-x86_64.sh>`

    .. |linux-64| replace:: :psycon:`64-bit (bash installer) <Linux-x86_64.sh>`


This section contains the necessary informations to install psyplot-conda, a
standalone psyplot installation with the most important plugins and the
graphical user interface (GUI).

Executables can be downloaded from the links above. Older versions are also
available through the the releases_ page, nightly builds for Linux and OSX are
available here_.

The installer provided here contain all necessary dependencies for psyplot_,
psyplot-gui_, psy-simple_, psy-maps_ and psy-reg_ plus the conda package for
managing virtual environments. These installers have been created using using
the conda constructor_ package and the packages from the conda-forge_ channel.

.. only:: html and not epub

    The latest versions for the installers can be downloaded through the links
    at the top.

Files for all versions can be found in the psyplot-conda_ repository and
explicitly on the releases_ page.

.. _psyplot-conda: https://github.com/Chilipp/psyplot-conda
.. _releases: https://github.com/Chilipp/psyplot-conda/releases

.. note::

    Under Linux and MacOSX you can also use ``cURL`` and to download the latest
    installer. Just open a terminal and type

    .. code-block:: bash

        curl -o psyplot-conda.sh -LO `curl -s https://api.github.com/repos/Chilipp/psyplot-conda/releases/latest | grep browser_download_url | cut -d '"' -f 4 | grep OSNAME` | grep .sh

    where ``OSNAME`` is one of ``Linux`` or ``MacOSX``.

    Then install it simply via

    .. code-block:: bash

        bash psyplot-conda.sh


.. include:: <isonum.txt>

.. Contents::
    :local:

.. _install-standalone-linux:

Installation on Linux
~~~~~~~~~~~~~~~~~~~~~
Download the bash script (file ending on ``'.sh'`` for linux) from
the releases_ page and open a terminal window.

Type::

    bash '<path-to-the-downloaded-file.sh>'

and simply follow the instructions.

For more information on the command line options type::

    bash '<Path-to-the-downloaded-file.sh>' --help

It will ask you, whether you want to add a ``psyplot`` alias to your
``.bashrc``, such that you can easily start the terminal and type
``psyplot`` to start the GUI. You can avoid this by setting
``NO_PSYPLOT_ALIAS=1``. Hence, to install ``psyplot-conda`` without any
terminal interaction, run::

    NO_PSYPLOT_ALIAS=1 bash '<Path-to-the-downloaded-file.sh>' -b -p <target-path>


Installation on OS X
~~~~~~~~~~~~~~~~~~~~~
You can either install it from the terminal using a
:ref:`bash-script <install-standalone-osx-bash>` (``.sh`` file),
or you can install a standalone app using an
:ref:`installer <install-standalone-osx-pkg>` (``.pkg`` file).

The bash script will install a conda installation in your desired location.
Both will create a ``Psyplot.app`` (see below).

.. _install-standalone-osx-pkg:

Installation using the OS X package
+++++++++++++++++++++++++++++++++++
This should be straight-forward, however Apple does not provide free Developer
IDs for open-source developers. Therefore our installers are not signed and
you have to give the permissions to open the files manually. The 4 steps below
describe the process.

1. Just download the ``.pkg`` file
2. To open it, you have to

   Right-click on the file |rarr| ``Open With`` |rarr| ``Installer``. In the appearing
   window, click the ``Open`` button.

3. Follow the instructions. It will create a ``Psyplot.app`` in the specified
   location.
4. To open the app the first time, change to the chosen installation directory
   for the App (by default ``$HOME/Applications``), right-click the
   ``Psyplot`` app and click on ``Open``. In the appearing window, again click
   on ``Open``.

.. _install-standalone-osx-bash:

Installation using the bash script
+++++++++++++++++++++++++++++++++++
Download the bash script (file ending on ``'.sh'`` for MacOSX) from
the releases_ page and open a terminal window.

Type::

    bash '<path-to-the-downloaded-file.sh>'

and simply follow the instructions.

For more informations on the command line options type::

    bash '<Path-to-the-downloaded-file.sh>' --help

By default, the installer asks whether you want to install a ``Psyplot.app``
into your ``Applications`` directory. You can avoid this be setting
``NO_PSYPLOT_APP=1``.

Furthermore it will ask you, whether you want to add a ``psyplot`` alias to
your ``.bash_profile``, such that you can easily start the terminal and type
``psyplot`` to start the GUI. You can avoid this by setting
``NO_PSYPLOT_ALIAS=1``. Hence, to install ``psyplot-conda`` without any
terminal interaction, run::

    NO_PSYPLOT_APP=1 NO_PSYPLOT_ALIAS=1 bash '<Path-to-the-downloaded-file.sh>' -b -p <target-path>

.. _install-standalone-win:

Installation on Windows
~~~~~~~~~~~~~~~~~~~~~~~
Just double click the downloaded file and follow the instructions. The
installation will create an item in the windows menu
(Start -> Programs -> Psyplot) which you can use to open the GUI. You can,
however, also download installers that create no shortcut from the
releases_ page.

In any case, if you chose to modify your ``PATH`` variable during the
installation, you can open a command window (``cmd``) and type ``psyplot``.

.. _here: https://drive.switch.ch/index.php/s/lVwRVtFncOljb6y
.. _psyplot: https://psyplot.readthedocs.io
.. _psyplot-gui: https://psyplot.readthedocs.io/projects/psyplot-gui
.. _psy-simple: https://psyplot.readthedocs.io/projects/psy-simple
.. _psy-maps: https://psyplot.readthedocs.io/projects/psy-simple
.. _psy-reg: https://psyplot.readthedocs.io/projects/psy-reg
.. _constructor: https://github.com/conda/constructor
.. _conda-forge: http://conda-forge.github.io/

.. _install-conda:

Installation using conda
^^^^^^^^^^^^^^^^^^^^^^^^
We highly recommend to use conda_ for installing psyplot. Here you can install
it via manually via the :ref:`conda-forge <install-conda-man>` channel or you
can use one of our :ref:`preconfigured environment files <install-conda-env>`.

.. _install-conda-man:

Manual installation
~~~~~~~~~~~~~~~~~~~~
After downloading the installer from anaconda_, you can install psyplot simply
via::

    $ conda install -c conda-forge psyplot

However, this only installs the raw framework. For your specific task, you
should consider one of the below mentioned plugins (see  :ref:`optional_deps`).

If you want to be able to read and write netCDF files, you can use for example
the netCDF4_ package via::

    $ conda install netCDF4

If you want to be able to read GeoTiff Raster files, you will need to have
gdal_ installed::

    $ conda install gdal

Please also visit the `xarray installation notes`_
for more informations on how to best configure the `xarray`_
package for your needs.

.. _install-conda-env:

Preconfigured environments
~~~~~~~~~~~~~~~~~~~~~~~~~~
There are also some preconfigured environments that you can download which allow
an efficient handling of netCDF files and the visualization of data on a globe.

Those environments are

- :download:`psyplot and psy-maps with netCDF4, dask and bottleneck <psyplot_environment.yml>`.
  This environment contains the recommended modules to view geo-referenced netCDF
  files without a GUI

  .. only:: latex or epub

      .. literalinclude:: psyplot_environment.yml
          :language: yaml

- :download:`psyplot with graphical user interface and the above packages <psyplot-gui_environment.yml>`.
  The same environment as above plus graphical user interface

  .. only:: latex or epub

      .. literalinclude:: psyplot-gui_environment.yml
          :language: yaml

After you downloaded one of the files, you can create and activate the new
virtual environment via::

    $ conda env create -f <downloaded file>
    $ source activate psyplot

.. _install-pip:

Installation using pip
^^^^^^^^^^^^^^^^^^^^^^
If you do not want to use conda for managing your python packages, you can also
use the python package manager ``pip`` and install via::

    $ pip install psyplot

However to be on the save side, make sure you have the :ref:`dependencies`
installed.

.. _install-source:

Installation from source
^^^^^^^^^^^^^^^^^^^^^^^^
To install it from source, make sure you have the :ref:`dependencies`
installed, clone the github_ repository via::

    git clone https://github.com/Chilipp/psyplot.git

and install it via::

    python setup.py install

.. _dependencies:

Dependencies
------------
Required dependencies
^^^^^^^^^^^^^^^^^^^^^
Psyplot has been tested for python 2.7, 3.4, 3.5 and 3.6. Furthermore the
package is built upon multiple other packages, mainly

- xarray_>=0.8: Is used for the data management in the psyplot package
- matplotlib_>=1.4.3: **The** python visualiation
  package
- `PyYAML <http://pyyaml.org/>`__: Needed for the configuration of psyplot


.. _optional_deps:

Optional dependencies
^^^^^^^^^^^^^^^^^^^^^
We furthermore recommend to use

- :ref:`psyplot-gui <psyplot_gui:install>`: A graphical user interface to psyplot
- :ref:`psy-simple <psy_simple:install>`: A psyplot plugin to make simple plots
- :ref:`psy-maps <psy_maps:install>`: A psyplot plugin for visualizing data on a
  map
- :ref:`psy-reg <psy_reg:install>`: A psyplot plugin for visualizing fits to
  your data
- cdo_: The python bindings for cdos (see also the
  :ref:`cdo example <gallery_examples_example_cdo.ipynb>`)

.. _netCDF4: https://github.com/Unidata/netcdf4-python
.. _gdal: http://www.gdal.org/
.. _conda: http://conda.io/
.. _anaconda: https://www.continuum.io/downloads
.. _matplotlib: http://matplotlib.org
.. _xarray installation notes: http://xarray.pydata.org/en/stable/installing.html
.. _xarray: http://xarray.pydata.org/
.. _cdo: https://code.zmaw.de/projects/cdo/wiki/Anaconda


Running the tests
-----------------
We us pytest_ to run our tests. So you can either run clone out the github_
repository and run::

    $ python setup.py test

or install pytest_ by yourself and run

    $ py.test

To also test the plugin functionality, install the ``psyplot_test`` module in
``tests/test_plugin`` via::

    $ cd tests/test_plugin && python setup.py install

and run the tests via one of the above mentioned commands.


Building the docs
-----------------
To build the docs, check out the github_ repository and install the
requirements in ``'docs/environment.yml'``. The easiest way to do this is via
anaconda by typing::

    $ conda env create -f docs/environment.yml
    $ source activate psyplot_docs

Then build the docs via::

    $ cd docs
    $ make html

.. note::

    The building of the docs always preprocesses the examples. You might want to
    disable that by setting ``process_examples = False``. Otherwise please note
    that the examples are written as python3 notebooks. So if you are using
    python2, you may have to install the python3 kernel. Just create a new
    environment ``'py35'`` and install it for IPython via::

        conda create -n py35 python=3.5
        source activate py35
        conda install notebook ipykernel
        ipython kernel install --user

    You then have to install the necessary modules for each of the examples in
    the new ``'py35'`` environment.

.. _github: https://github.com/Chilipp/psyplot
.. _pytest: https://pytest.org/latest/contents.html


.. _uninstall:

Uninstallation
--------------
The uninstallation depends on the system you used to install psyplot. Either
you did it via the :ref:`standalone installers <install-standalone>` (see
:ref:`uninstall-standalone`), via :ref:`conda <install-conda>` (see
:ref:`uninstall-conda`), via :ref:`pip <install-pip>` or from the
:ref:`source files <install-source>` (see :ref:`uninstall-pip`).

Anyway, if you may want to remove the psyplot configuration files. If you did
not specify anything else (see :func:`psyplot.config.rcsetup.psyplot_fname`),
the configuration files for psyplot are located in the user home directory.
Under linux and OSX, this is ``$HOME/.config/psyplot``. On other platforms it
is in the ``.psyplot`` directory in the user home.

.. _uninstall-standalone:

Uninstalling standalone app
^^^^^^^^^^^^^^^^^^^^^^^^^^^
The complete uninstallation requires three steps:

1. Delete the files (see the OS specific steps below)
2. Unregister the locations from your ``PATH`` variable (see below)

.. Contents::
    :local:

.. _uninstall-standalone-linux:

Uninstallation on Linux
~~~~~~~~~~~~~~~~~~~~~~~
Just delete the folder where you installed ``psyplot-conda``. By default, this
is ``$HOME/psyplot-conda``, so just type::

    rm -rf $HOME/psyplot-conda

If you added a ``psyplot`` alias to your ``.bashrc`` (see
:ref:`installation instructions <install-standalone-linux>`) or chose to add the
``bin`` directory to your ``PATH`` variable during the installation, open your
``$HOME/.bashrc`` in an editor of your choice and delete those parts.


.. _uninstall-standalone-osx:

Uninstallation on OSX
~~~~~~~~~~~~~~~~~~~~~
The uninstallation depends on whether you have used the
:ref:`package installer <install-standalone-osx-pkg>` or the
:ref:`bash script <install-standalone-osx-bash>` for the installation.

.. _uninstall-standalone-osx-pkg:

Uninstall the App installed through the OS X package
++++++++++++++++++++++++++++++++++++++++++++++++++++
Just delete the app from your ``Applications`` folder. There have been no
changes made to your ``PATH`` variable.

.. _uninstall-standalone-osx-bash:

Uninstall the App installed via bash script
+++++++++++++++++++++++++++++++++++++++++
As for :ref:`linux <uninstall-standalone-linux>`, just delete the folder where you
installed ``psyplot-conda``. By default, this is ``$HOME/psyplot-conda``.
Open a terminal and just type::

    rm -rf $HOME/psyplot-conda

If you added a ``psyplot`` alias to your ``.bash_profile`` (see
:ref:`installation instructions <install-standalone-osx-bash>`) or chose to add the
``bin`` directory to your ``PATH`` variable during the installation, open your
``$HOME/.bash_profile`` in an editor of your choice and delete those parts.

If you chose to add a ``Psyplot`` app, just delete the symbolic link in
``/Applications`` or ``$HOME/Applications``.

.. _uninstall-standalone-win:

Uninstallation on Windows
~~~~~~~~~~~~~~~~~~~~~~~~~
Just double-click the ``Uninstall-Anaconda.exe`` file in the directory where
you installed ``psyplot-conda`` and follow the instructions.

This will also revert the changes in your ``PATH`` variable.


.. _uninstall-conda:

Uninstallation via conda
^^^^^^^^^^^^^^^^^^^^^^^^
If you installed psyplot via :ref:`conda <install-conda>`, simply run::

    conda remove psyplot

If you however installed it via a preconfigured environment (see
:ref:`install-conda-env`), you can simply remove the entire virtual environment
via::

    conda env remove -n psyplot

.. _uninstall-pip:

Uninstallation via pip
^^^^^^^^^^^^^^^^^^^^^^
Uninstalling via pip simply goes via::

    pip uninstall psyplot

Note, however, that you should use :ref:`conda <uninstall-conda>` if you also
installed it via conda.
