.. _about:

About psyplot
=============

Why psyplot?
------------
When visualizing data, one always has to choose:

- Either create the plot with an intuitive graphical user interface (GUI)
  (e.g. panoply) but less options for customization and difficult to script
- or create the plot from the command line, e.g. via NCL, R or python with more
  possibilities for customization and scripting but also less intuitive

``psyplot`` wants to combine these two worlds: create a well-documented and
easy accessible framework to visualize data from a GUI and the command line
(and of course through a script).

There exists nothing like that. Of course you can also work with software like
Paraview_ via the built-in python shell. But, if you really want to explore your
data it is totally not straightforward to access and explore it from within
such a software using numeric functions from numpy, scipy, etc.

Therefore I developed this modular framework that can create and customize plots
efficiently with short and comprehensive commands, that can be accessed
through a GUI (see :ref:`projects`) and where you have always a comprehensive
API to access your data.

Different from the usual use with matplotlib, which in the end results most of
the time in copy-pasting parts of your code, this software is build on the
*don't repeat yourself* principle. Each of the small parts that make up a
visualization, whether it is part of the data evaluation or of the appearance
of the plot, psyplot puts it into a formatoption can be reused when it is
needed.

Nevertheless, it's again a new piece of software. Therefore, if you want to use
it, for sure you need a bit of time to get comfortable with the framework. I
promise to you, it's worth it. So :ref:`get started <getting-started>` and
please let me know if you have a different opinion.

.. _matplotlib: http://matplotlib.org


.. _what-it-is-and-what-it-is-not:

What it is, and what it is not
------------------------------
.. note::

    First of all, it's open source! So please, if you don't agree with the
    points below, `edit this document`_ and click on *Propose File Change* and
    *Create pull request*. We can then discuss your changes.

.. _edit this document: https://github.com/psyplot/psyplot/edit/master/docs/about.rst

There are tons of software tools around for visualization, so what is special
about psyplot? The following list should hopefully provide you some guidance.

What it is
**********
- It is fast. Not necessarily when it comes down to being the fastest
  interactive visualization software, but for sure when it comes down to
  development time, as it is very user-friendly from the command line. There are
  no other software packages that provide a simple and intuitive visualization
  such as

  .. code-block:: python

      psy.plot.mapplot('my-netcdf-file.nc', lonlatbox='Germany')

  while still providing a very high range of flexible options to adjust the
  visualization. No GUI, independent of it's intuitiveness, can ever beat the
  speed of a scientist that knows a bit of coding and how to use the different
  formatoptions in psyplot.
- it visualizes :ref:`unstructured grids <psyplot_examples:/maps/example_ugrid.ipynb>`,
  such as ICON_ or UGRID_ model data
- it automatically decodes CF-conventions
- it intuitively integrates the structure of netCDF files. So if you often
  work with netCDF files, psyplot might be a good option
- it is pythonic. If you are using python anyway, psyplot is worth a try and we
  are always keen to help new users getting started.
- it is very flexible (I think we made this point already), from command-line
  and GUI.

  * We can implement tons of new visualization and data analysis techniques and
    :ref:`you can implement your own <plugins_guide>`.
  * they are automatically implemented in the GUI
  * the user can do his statistical and numerical computations with software
    like xarray, numpy, scipy, etc. and then use the psyplot visualization
    methods in the same script
  * its modular framework allows to tackle new scientific questions and handle
    them in separate psyplot plugins with it's own formatoptions and
    plotting methods
- it will always be free and open-source under the LGPL License.

.. _ICON: https://mpimet.mpg.de/en/science/modeling-with-icon/icon-configurations
.. _UGRID: https://ugrid-conventions.github.io/ugrid-conventions/


What it is not
**************
No software can do everything, neither can psyplot. Our main focus on
flexibility, easy command-line usage and the GUI integration inevitably comes
with a few downsides.

- it is not the fastest, because we use matplotlib to be flexible in our
  visualization, and this runs on the CPU, rather than the GPU. But if
  matplotlib or the standard visualization utilities from R, NCL, etc. are
  sufficient for you, you can go with psyplot.
- it is not the best for interactive web-applications. Although it would be
  pretty simple to set up a backend server with psyplot and tornado_ or Flask_,
  for instance, it's limited to sending rastered image data around, due to the
  `options provided by matplotlib`_.
- it is not as fast as ncview_. psyplot (and psy-view_ in particular) are
  written in the dynamically interpreted python language (which allows the
  combination of GUI and command-line, and the high flexibility). But we will
  never beat the speed of the (compiled but less flexible) ncview software.
- our GUI is not the most interactive one. psyplot is a `command-line-first`
  software, i.e. we put the most effort in making the usage from command-line
  and scripts as easy as possible. The GUI is something on top and is limited by
  the speed and functionalities of matplotlib (which is, nevertheless, pretty
  rich). But we are constantly improving the GUI, see psy-view_ for instance.
- it is not made for statistical visualizations. We will never beat the
  possibilities by packages like seaborn_ or R_. The only advantage of psy-reg_
  over these other software tools, is the possibility to adapt everything using
  the full power of matplotlib artists within and outside of the psyplot
  framework
- it is not the best software for manipulating shapefiles, although some support
  of this might come in the future.

.. _Paraview: https://www.paraview.org
.. _tornado: https://www.tornadoweb.org
.. _flask: https://flask.palletsprojects.com
.. _options provided by matplotlib: https://matplotlib.org/3.1.1/faq/howto_faq.html#how-to-use-matplotlib-in-a-web-application-server
.. _other visualization backends: https://github.com/psyplot/psy-vtk
.. _psy-view: https://github.com/psyplot/psy-view
.. _ncview: http://meteora.ucsd.edu/~pierce/ncview_home_page.html
.. _psy-reg: https://psyplot.github.io/psy-reg
.. _seaborn: https://seaborn.pydata.org
.. _R: https://www.r-project.org/


About the author
----------------
I, (`Philipp Sommer`_), work as a Data Scientist at the
`Helmholtz-Zentrum Hereon`_ (Germany) in the
`Helmholtz Coastal Data Center (HCDC)`_.

.. _Helmholtz Coastal Data Center (HCDC): https://hcdc.hereon.de
.. _Helmholtz-Zentrum Hereon: https://www.hereon.de
.. _Philipp Sommer: https://www.philipp-s-sommer.de


License
-------
Copyright © 2021 Helmholtz-Zentrum Hereon, 2020-2021 Helmholtz-Zentrum
Geesthacht, 2016-2021 University of Lausanne

psyplot is released under the GNU LGPL-3.O license.
See COPYING and COPYING.LESSER in the root of the repository for full
licensing details.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License version 3.0 as
published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU LGPL-3.0 license for more details.

You should have received a copy of the GNU LGPL-3.0 license
along with this program.  If not, see https://www.gnu.org/licenses/.
