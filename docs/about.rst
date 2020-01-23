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
Paraview via the built-in python shell. But, if you really want to explore your
data it is totally not straightforward to access and explore it from within
such a software using numeric functions from numpy, scipy, etc.

Therefore I developed this modular framework that can create and customize plots
efficiently with short and comprehensive commands, that can be accessed
through a GUI (see :ref:`projects`) and where you have always a comprehensive
API to access your data.

Different from the usual use with matplotlib, which in the end most of the time
results in copy-pasting parts of your code, this software is build on the
*don't repeat yourself* principle. Each of the small parts that make up a
visualization, whether it is part of the data evaluation or of the appearance
of the plot, psyplot puts it into a formatoption can be reused when it is
needed.

Nevertheless, it's again a new piece of software. Therefore, if you want to use
it, for sure you need a bit of time to get comfortable with the framework. I
promise to you, it's worth it. So :ref:`get started <getting-started>` and
please let me know if you have a different opinion.

.. _matplotlib: http://matplotlib.org


About the author
----------------
I, (`Philipp Sommer`_), work as a Data Scientist at the Helmholtz-Zentrum
Geesthacht (Germany) in the Helmholtz Coastal Data Center. Checkout my homepage
if you want to know more at philipp-s-sommer.de_

.. _Philipp Sommer: http://www.philipp-s-sommer.de
.. _philipp-s-sommer.de: http://www.philipp-s-sommer.de


License
-------
psyplot is published under the
`GNU General Public License v2.0 <http://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html>`__
