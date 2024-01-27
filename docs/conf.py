# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: LGPL-3.0-only

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import warnings
from itertools import product
from pathlib import Path

from sphinx.ext import apidoc

# make sure, psyplot from parent directory is used
sys.path.insert(0, os.path.abspath(".."))

# isort: off

import psyplot

# isort: on

from psyplot.plotter import Formatoption, Plotter

# automatically import all plotter classes
psyplot.rcParams["project.auto_import"] = True
# include links to the formatoptions in the documentation of the
# :attr:`psyplot.project.ProjectPlotter` methods
Plotter.include_links(True)

warnings.filterwarnings("ignore", message="axes.color_cycle is deprecated")
warnings.filterwarnings(
    "ignore", message=("This has been deprecated in mpl 1.5,")
)
warnings.filterwarnings("ignore", message="invalid value encountered in ")
warnings.filterwarnings("ignore", message=r"\s*examples.directory")
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings(
    "ignore", message="Using an implicitly registered datetime converter"
)
warnings.filterwarnings(
    "ignore", message=r"\s*The on_mappable_changed function"
)
warnings.filterwarnings(
    "ignore", message=r".+multi-part geometries is deprecated"
)
warnings.filterwarnings(
    "ignore", message=r"\s*The array interface is deprecated"
)


def generate_apidoc(app):
    appdir = Path(app.__file__).parent
    apidoc.main(
        ["-fMEeTo", str(api), str(appdir), str(appdir / "migrations" / "*")]
    )


api = Path("api")

if not api.exists():
    generate_apidoc(psyplot)

# -- Project information -----------------------------------------------------

project = "psyplot"
copyright = "2021-2024 Helmholtz-Zentrum hereon GmbH"
author = "Philipp S. Sommer"


linkcheck_ignore = [
    # we do not check link of the psyplot as the
    # badges might not yet work everywhere. Once psyplot
    # is settled, the following link should be removed
    r"https://.*psyplot"
    # HACK: SNF seems to have a temporary problem
    r"https://p3.snf.ch/project-\d+",
]

linkcheck_anchors_ignore = ["^install$"]


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "hereon_nc_sphinxext",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx_design",
    "sphinx.ext.autosummary",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.extlinks",
    "matplotlib.sphinxext.plot_directive",
    "IPython.sphinxext.ipython_console_highlighting",
    "IPython.sphinxext.ipython_directive",
    "sphinxarg.ext",
    "psyplot.sphinxext.extended_napoleon",
    "autodocsumm",
    "sphinx.ext.imgconverter",
]


# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

napoleon_use_admonition_for_examples = True


autodoc_default_options = {
    "show_inheritance": True,
    "members": True,
    "autosummary": True,
}

autoclass_content = "both"

not_document_data = [
    "psyplot.config.rcsetup.defaultParams",
    "psyplot.config.rcsetup.rcParams",
]

ipython_savefig_dir = "_static"

# fontawesome icons
html_css_files = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.1.1/css/all.min.css"
]

sd_fontawesome_latex = True

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"

html_theme_options = {
    "collapse_navigation": False,
    "includehidden": False,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = "_static/psyplot.png"

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "_static/psyplot.ico"

# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    # Additional stuff for the LaTeX preamble.
    "preamble": r"\setcounter{tocdepth}{10}"
}

intersphinx_mapping = {
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "seaborn": ("https://seaborn.pydata.org/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
    "xarray": ("https://xarray.pydata.org/en/stable/", None),
    "cartopy": ("https://scitools.org.uk/cartopy/docs/latest/", None),
    "psy_maps": ("https://psyplot.github.io/psy-maps/", None),
    "psy_simple": ("https://psyplot.github.io/psy-simple/", None),
    "psy_reg": ("https://psyplot.github.io/psy-reg/", None),
    "psyplot_gui": ("https://psyplot.github.io/psyplot-gui/", None),
    "psy_view": ("https://psyplot.github.io/psy-view/", None),
    "psyplot_examples": ("https://psyplot.github.io/examples/", None),
    "python": ("https://docs.python.org/3/", None),
}

replacements = {
    "`psyplot.rcParams`": "`~psyplot.config.rcsetup.rcParams`",
    "`psyplot.InteractiveList`": "`~psyplot.data.InteractiveList`",
    "`psyplot.InteractiveArray`": "`~psyplot.data.InteractiveArray`",
    "`psyplot.open_dataset`": "`~psyplot.data.open_dataset`",
    "`psyplot.open_mfdataset`": "`~psyplot.data.open_mfdataset`",
}


def link_aliases(app, what, name, obj, options, lines):
    for (key, val), (i, line) in product(
        replacements.items(), enumerate(lines)
    ):
        lines[i] = line.replace(key, val)


fmt_attrs_map = {
    "Interface to other formatoptions": [
        "children",
        "dependencies",
        "connections",
        "parents",
        "shared",
        "shared_by",
    ],
    "Formatoption intrinsic": [
        "value",
        "value2share",
        "value2pickle",
        "default",
        "validate",
    ],
    "Interface for the plotter": [
        "lock",
        "diff",
        "set_value",
        "check_and_set",
        "initialize_plot",
        "update",
        "share",
        "finish_update",
        "remove",
        "changed",
        "plotter",
        "priority",
        "key",
        "plot_fmt",
        "update_after_plot",
        "requires_clearing",
        "requires_replot",
    ],
    "Interface to the data": [
        "data_dependent",
        "index_in_list",
        "project",
        "ax",
        "raw_data",
        "decoder",
        "any_decoder",
        "data",
        "iter_data",
        "iter_raw_data",
        "set_data",
        "set_decoder",
    ],
    "Information attributes": ["group", "name", "groupname", "default_key"],
    "Miscellaneous": ["init_kwargs", "logger"],
}


def group_fmt_attributes(app, what, name, obj, section, parent):
    if parent is Formatoption:
        return next(
            (group for group, val in fmt_attrs_map.items() if name in val),
            None,
        )


def setup(app):
    app.connect("autodoc-process-docstring", link_aliases)
    app.connect("autodocsumm-grouper", group_fmt_attributes)
