.. _install:

.. highlight:: bash

Installation
============

How to install
--------------
There basically three different methodologies for the installation. You should
choose the one, which is the most appropriate solution concerning your skills
and your usage:

The recommended installation
    We recommend to use anaconda for installing python and psyplot (see
    :ref:`install-conda`). If you however already have python installed on
    your system, you can also use pip (see :ref:`install-pip`).
The developer installation
    Install it from source (see :ref:`install-source`)


.. _install-conda:

Installation using conda
^^^^^^^^^^^^^^^^^^^^^^^^
We highly recommend to use conda_ for installing psyplot. After having
downloaded the installer from anaconda_ or miniconda_, you can install psyplot
and the optional plugins (see  :ref:`optional_deps`) via::

    $ conda install -c conda-forge psy-maps psyplot-gui psy-reg netCDF4

If you only want to install the core, i.e. the raw framework, run::

    $ conda install -c conda-forge psyplot

If you want to be able to read GeoTiff Raster files, you will need to have
gdal_ installed::

    $ conda install gdal

Please also visit the `xarray installation notes`_
for more informations on how to best configure the `xarray`_
package for your needs.

.. _install-pip:

Installation using pip
^^^^^^^^^^^^^^^^^^^^^^
If you do not want to use conda for managing your python packages, you can also
use the python package manager ``pip`` and install via::

    $ pip install psyplot

However to be on the safe side, make sure you have the :ref:`dependencies`
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
.. _conda: https://conda.io/docs/
.. _anaconda: https://www.anaconda.com/download/
.. _miniconda: https://conda.io/miniconda.html
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
you did it via :ref:`conda <install-conda>` (see
:ref:`uninstall-conda`), via :ref:`pip <install-pip>` or from the
:ref:`source files <install-source>` (see :ref:`uninstall-pip`).

Anyway, if you may want to remove the psyplot configuration files. If you did
not specify anything else (see :func:`psyplot.config.rcsetup.psyplot_fname`),
the configuration files for psyplot are located in the user home directory.
Under linux and OSX, this is ``$HOME/.config/psyplot``. On other platforms it
is in the ``.psyplot`` directory in the user home.

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
