About psyplot
=============

Why psyplot?
------------
When visualizing data, one always has to choose:

- create the plot with an intuitive graphical user interface (GUI)
  (e.g. panoply) but less options for customization and difficult to script
- create the plot from the command line, e.g. via NCL, R or python with more
  possibilities for customization and scripting but also less intuitive

``psyplot`` wants to combine these two worlds: create a well-documented and
easy accessible framework to visualize data from a GUI and the command line. We
want something that can be accessed through the command line and that is fully
and easy scriptable and something that can be accessed through a GUI.

Hence, I provide a modular framework that can create and customize plots
efficiently with short and comprehensive commands and that can be accessed
through a GUI (see :ref:`projects`).

To be honest, I love matplotlib_ and it's capabilities. But, I hate
copy-and-paste. Not only that I and prefer the *don't repeat yourself*
principle, it is also harder to maintain the code when new versions of
matplotlib or other libraries are released. However, if you do plots from the
command line, no matter if it's python, R or NCL, you almost always end up with
copy and paste. Therefore I put each of the small parts that make up a
visualization in a formatoption that I can reuse when I need it.

Nevertheless, it's again a new piece of software. Therefore, if you want to use
it, for sure you need a bit of time to get comfortable with the framework. I
promise to you, it's worth it. So :ref:`get started <getting-started>` and
please let me know if you have a different opinion.

.. _matplotlib: http://matplotlib.org


About the author
----------------
I (`Philipp Sommer`_) work as a PhD student for climate modeling in the
Atmosphere-Regolith-Vegetation (ARVE) group in the Institute of Earth Surface
Dynamics (IDYST) at the University of Lausanne. During my time at the
`Max-Planck-Institute for Meteorology`_ I worked a lot with the
`Max-Planck-Institute Earth-System-Model (MPI-ESM)`_ and the `ICON model`_
in the working group on Terrestrial Hydrology of Stefan Hagemann. This
included a lot of evaluation of climate model data. It finally gave the
motivation for the visualization framework ``psyplot``.

.. _Philipp Sommer: http://arve.unil.ch/people/philipp-sommer
.. _Max-Planck-Institute for Meteorology: http://www.mpimet.mpg.de
.. _Max-Planck-Institute Earth-System-Model (MPI-ESM): http://www.mpimet.mpg.de/en/science/models/mpi-esm.html
.. _ICON model: http://www.mpimet.mpg.de/en/science/models/icon.html


License
-------
psyplot is published under the
`GNU General Public License v2.0 <http://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html>`__
