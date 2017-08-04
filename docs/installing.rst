.. _install:

.. highlight:: bash

Installation
============

How to install
--------------

Installation using single executable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. only:: html and not epub

    +--------------+--------------+----------------+
    | | |win-logo| | | |osx-logo| | | |linux-logo| |
    | | Windows    | | Mac OS X   | | Linux        |
    +==============+==============+================+
    | | |win-64|   | |osx-64|     | |linux-64|     |
    | | |win-32|   |              |                |
    +--------------+--------------+----------------+

    .. |win-logo| image:: windows.png

    .. |linux-logo| image:: linux.png

    .. |osx-logo| image:: apple.png

    .. |win-64| replace:: :psycon:`64-bit (.exe installer) <Windows-x86_64.exe>`

    .. |win-32| replace:: :psycon:`32-bit (.exe installer) <Windows-x86.exe>`

    .. |osx-64| replace:: :psycon:`64-bit (bash installer) <MacOSX-x86_64.sh>`

    .. |linux-64| replace:: :psycon:`64-bit (bash installer) <Linux-x86_64.sh>`

The easiest way for the installation comes via the psyplot-conda_ project.
Here we provide ready-to-go installers for psyplot for all
platforms. Those installers include conda, psyplot, the
`graphical user interface`_, several plugins (psy-simple_,
psy-maps_ and psy-reg_) and their dependencies.

.. only:: html and not epub

    The latest versions for the installers can be downloaded through the links
    at the top.

Files for all versions can be found in the psyplot-conda_ repository and
explicitly on the releases_ page.

Installation on MacOSX and Linux
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Download the bash script (file ending on ``'.sh'`` for linux or MacOSX) from
above or the releases_ page and open a terminal window.

Type::

    bash '<path-to-the-downloaded-file.sh>'

and simply follow the instructions.

For more informations on the command line options type

Type::

    bash '<Path-to-the-downloaded-file.sh>' --help

On MaxOSX, the installation will create the ``Psyplot.app`` in the
``/Applications`` folder (or alternatively the``~/Applications`` folder) which
you can use to open the psyplot GUI. Otherwise type ``psyplot`` in the
terminal.


Installation on Windows
~~~~~~~~~~~~~~~~~~~~~~~
Download the executable script (file ending on ``'.exe'``) for your platform
from above or the releases_ page.

Just double click the downloaded file and follow the instructions. The
installation will create an item in the windows menu
(Start -> Programs -> Psyplot) which you can use to open the GUI. Otherwise,
open a command window (``cmd``) and type ``psyplot``.

.. note::

    Under Linux and MacOSX you can also use ``cURL`` and to download the latest
    installer. Just open a terminal and type

    .. code-block:: bash

        curl -o psyplot-conda.sh -LO `curl -s https://api.github.com/repos/Chilipp/psyplot-conda/releases/latest | grep browser_download_url | cut -d '"' -f 4 | grep OSNAME`

    where ``OSNAME`` is one of ``Linux`` or ``MacOSX``.

    Then install it simply via

    .. code-block:: bash

        bash psyplot-conda.sh

.. _psyplot-conda: https://github.com/Chilipp/psyplot-conda
.. _releases: https://github.com/Chilipp/psyplot-conda/releases
.. _graphical user interface: https://github.com/Chilipp/psyplot-gui
.. _psy-simple: https://github.com/Chilipp/psy-simple
.. _psy-maps: https://github.com/Chilipp/psy-maps
.. _psy-reg: https://github.com/Chilipp/psy-reg

Installation using conda
^^^^^^^^^^^^^^^^^^^^^^^^
We highly recommend to use conda_ for installing psyplot. After downloading
the installer from anaconda_, you can install psyplot simply via::

    $ conda install -c chilipp psyplot

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

Installation using pip
^^^^^^^^^^^^^^^^^^^^^^
If you do not want to use conda for managing your python packages, you can also
use the python package manager ``pip`` and install via::

    $ pip install psyplot


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

Preconfigured environments
^^^^^^^^^^^^^^^^^^^^^^^^^^
There are also some preconfigured environments that you can download which allow
an efficient handling of netCDF files and the visualization of data on a globe.

Those environments are

- :download:`psyplot and psy-maps with netCDF4, dask and bottleneck <psyplot_environment.yml>`.
  This environment contains the recommended modules to view geo-referenced netCDF
  files without a GUI
- :download:`psyplot with graphical user interface and the above packages <psyplot-gui_environment.yml>`.
  The same environment as above plus graphical user interface

After you downloaded one of the files, you can create and activate the new
virtual environment via::

    $ conda env create -f <downloaded file>
    $ source activate psyplot


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
