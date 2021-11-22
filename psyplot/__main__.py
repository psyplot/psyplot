# -*- coding: utf-8 -*-
"""Main commandline entrypoint for psyplot."""

# Disclaimer
# ----------
#
# Copyright (C) 2021 Helmholtz-Zentrum Hereon
# Copyright (C) 2020-2021 Helmholtz-Zentrum Geesthacht
# Copyright (C) 2016-2021 University of Lausanne
#
# This file is part of psyplot and is released under the GNU LGPL-3.O license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3.0 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU LGPL-3.0 license for more details.
#
# You should have received a copy of the GNU LGPL-3.0 license
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import os.path as osp
import sys
import argparse
import pickle
import six
import glob
from itertools import chain
from collections import defaultdict
import yaml
import xarray as xr
import psyplot
from psyplot.docstring import docstrings
from psyplot.warning import warn
from psyplot.compat.pycompat import get_default_value
from funcargparse import FuncArgParser
import logging

rcParams = psyplot.rcParams


logger = logging.getLogger(__name__)


def main(args=None):
    """Main function for usage of psyplot from the command line

    This function creates a parser that parses command lines to the
    :func:`make_plot` functions or (if the ``psyplot_gui`` module is
    present, to the :func:`psyplot_gui.start_app` function)

    Returns
    -------
    psyplot.parser.FuncArgParser
        The parser that has been used from the command line"""
    try:
        from psyplot_gui import get_parser as _get_parser
    except (ImportError, ModuleNotFoundError) as e:
        logger.debug('Failed to import gui', exc_info=True)
        parser = get_parser(create=False)
        parser.update_arg('output', required=True)
        parser.create_arguments()
        parser.parse2func(args)
    else:
        parser = _get_parser(create=False)
        parser.create_arguments()
        parser.parse_known2func(args)


@docstrings.get_sections(base='make_plot')
@docstrings.dedent
def make_plot(fnames=[], name=[], dims=None, plot_method=None,
              output=None, project=None, engine=None, formatoptions=None,
              tight=False, rc_file=None, encoding=None, enable_post=False,
              seaborn_style=None, output_project=None,
              concat_dim=get_default_value(xr.open_mfdataset, 'concat_dim'),
              chname={}, preset=None):
    """
    Eventually start the QApplication or only make a plot

    Parameters
    ----------
    fnames: list of str
        Either the filenames to show, or, if the `project` parameter is set,
        the a list of `,`-separated filenames to make a mapping from the
        original filename to a new one
    name: list of str
        The variable names to plot if the `output` parameter is set
    dims: dict
        A mapping from coordinate names to integers if the `project` is not
        given
    plot_method: str
        The name of the plot_method to use
    output: str or list of str
        If set, the data is loaded and the figures are saved to the specified
        filename and now graphical user interface is shown
    project: str
        If set, the project located at the given file name is loaded
    engine: str
        The engine to use for opening the dataset (see
        :func:`psyplot.data.open_dataset`)
    formatoptions: dict
        A dictionary of formatoption that is applied to the data visualized by
        the chosen `plot_method`
    tight: bool
        If True/set, it is tried to figure out the tight bbox of the figure and
        adjust the paper size of the `output` to it
    rc_file: str
        The path to a yaml configuration file that can be used to update  the
        :attr:`~psyplot.config.rcsetup.rcParams`
    encoding: str
        The encoding to use for loading the project. If None, it is
        automatically determined by pickle. Note: Set this to ``'latin1'``
        if using a project created with python2 on python3.
    enable_post: bool
        Enable the :attr:`~psyplot.plotter.Plotter.post` processing
        formatoption. If True/set, post processing scripts are enabled in the
        given `project`. Only set this if you are sure that you can trust the
        given project file because it may be a security vulnerability.
    seaborn_style: str
        The name of the style of the seaborn package that can be used for
        the :func:`seaborn.set_style` function
    output_project: str
        The name of a project file to save the project to
    concat_dim: str
        The concatenation dimension if multiple files in `fnames` are
        provided
    chname: dict
        A mapping from variable names in the project to variable names in the
        datasets that should be used instead
    preset: str
        The filename or identifier of a preset. If the given `preset` is
        the path to an existing yaml file, it will be loaded. Otherwise we
        look up the `preset` in the psyplot configuration directory (see
        :func:`~psyplot.config.rcsetup.get_configdir`).
    """
    if project is not None and (name != [] or dims is not None):
        warn('The `name` and `dims` parameter are ignored if the `project`'
             ' parameter is set!')
    if rc_file is not None:
        rcParams.load_from_file(rc_file)

    if dims is not None and not isinstance(dims, dict):
        dims = dict(chain(*map(six.iteritems, dims)))

    if len(output) == 1:
        output = output[0]
    if not fnames and not project:
        raise ValueError(
            "Either a filename or a project file must be provided if "
            "the output parameter is set!")
    elif project is None and plot_method is None:
        raise ValueError(
            "A plotting method must be provided if the output parameter "
            "is set and not the project!")
    if seaborn_style is not None:
        import seaborn as sns
        sns.set_style(seaborn_style)
    import psyplot.project as psy
    if project is not None:
        fnames = [s.split(',') for s in fnames]
        chname = dict(chname)
        single_files = (l[0] for l in fnames if len(l) == 1)
        alternative_paths = defaultdict(lambda: next(single_files, None))
        alternative_paths.update([l for l in fnames if len(l) == 2])
        p = psy.Project.load_project(
            project, alternative_paths=alternative_paths,
            engine=engine, encoding=encoding, enable_post=enable_post,
            chname=chname)
        if preset:
            p.load_preset(preset)
        if formatoptions is not None:
            p.update(fmt=formatoptions)
        p.export(output, tight=tight)
    else:
        pm = getattr(psy.plot, plot_method, None)
        if pm is None:
            raise ValueError("Unknown plot method %s!" % plot_method)
        kwargs = {'name': name} if name else {}
        p = pm(
            fnames, dims=dims or {}, engine=engine, preset=preset,
            fmt=formatoptions or {}, mf_mode=True, concat_dim=concat_dim,
            **kwargs)
        p.export(output, tight=tight)
    if output_project is not None:
        p.save_project(output_project)
    return


def get_parser(create=True):
    """Return a parser to make that can be used to make plots or open files
    from the command line

    Returns
    -------
    psyplot.parser.FuncArgParser
        The :class:`argparse.ArgumentParser` instance"""
    #: The parse that is used to parse arguments from the command line
    epilog = docstrings.get_sections(docstrings.dedent("""
        Examples
        --------

        Here are some examples on how to use psyplot from the command line.

        Plot the variable ``'t2m'`` in a netCDF file ``'myfile.nc'`` and save
        the plot to ``'plot.pdf'``::

            $ psyplot myfile.nc -n t2m -pm mapplot -o test.pdf

        Create two plots for ``'t2m'`` with the first and second timestep on
        the second vertical level::

            $ psyplot myfile.nc -n t2m  -pm mapplot -o test.pdf -d t,0,1 z,1

        If you have save a project using the
        :meth:`psyplot.project.Project.save_project` method into a file named
        ``'project.pkl'``, you can replot this via::

            $ psyplot -p project.pkl -o test.pdf

        If you use a different dataset than the one you used in the project
        (e.g. ``'other_ds.nc'``), you can replace it via::

            $ psyplot other_dataset.nc -p project.pkl -o test.pdf

        or explicitly via::

            $ psyplot old_ds.nc,other_ds.nc -p project.pkl -o test.pdf

        You can also load formatoptions from a configuration file, e.g.::

            $ echo 'title: my title' > fmt.yaml
            $ psyplot myfile.nc -n t2m  -pm mapplot -fmt fmt.yaml -o test.pdf
        """), 'parser', ['Examples'])

    epilog = '.. rubric:: Examples\n' + '\n'.join(epilog.splitlines()[2:])

    parser = FuncArgParser(
        description="""
        Load a dataset, make the plot and save the result to a file""",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    info_grp = parser.add_argument_group(
        'Info options',
        'Options that print informations and quit afterwards')

    parser.update_arg('version', short='V', long='version', action='version',
                      version=psyplot.__version__, if_existent=False,
                      group=info_grp)

    parser.update_arg('all_versions', short='aV', long='all-versions',
                      action=AllVersionsAction, if_existent=False,
                      group=info_grp)

    parser.update_arg('list_plugins', short='lp', long='list-plugins',
                      action=ListPluginsAction, if_existent=False,
                      group=info_grp)
    parser.update_arg(
        'list_plot_methods', short='lpm', long='list-plot-methods',
        action=ListPlotMethodsAction, if_existent=False, group=info_grp)
    parser.update_arg(
        'list_datasets', short='lds', long='list-datasets',
        action=ListDsNamesAction, if_existent=False, group=info_grp,
        help="""List the used dataset names in the given `project`.""")

    parser.update_arg(
        'list_presets', short='lps', long='list-presets',
        action=ListPresetsAction, if_existent=False, group=info_grp)

    parser.setup_args(make_plot)

    output_grp = parser.add_argument_group(
        'Output options',
        'Options that only have an effect if the `-o` option is set.')

    parser.update_arg('fnames', positional=True, nargs='*')

    parser.update_arg('name', short='n', nargs='*', metavar='variable_name',
                      const=None)

    parser.update_arg('dims', short='d', nargs='+', type=_load_dims,
                      metavar='dim,val1[,val2[,...]]')

    pm_choices = {pm for pm, d in filter(
                      lambda t: t[1].get('plot_func', True),
                      six.iteritems(rcParams['project.plotters']))}
    if psyplot._project_imported:
        import psyplot.project as psy
        pm_choices.update(set(psy.plot._plot_methods))
    parser.update_arg('plot_method', short='pm', choices=pm_choices,
                      metavar='{%s}' % ', '.join(map(repr, pm_choices)))

    parser.update_arg('output', short='o', group=output_grp)
    parser.update_arg('output_project', short='op', group=output_grp)

    parser.update_arg('project', short='p')

    parser.update_arg(
        'formatoptions', short='fmt', type=_load_dict, help="""
        The path to a yaml (``'.yml'`` or ``'.yaml'``) or pickle file
        defining a dictionary of formatoption that is applied to the data
        visualized by the chosen `plot_method`""", metavar='FILENAME')

    parser.update_arg(
        'chname', type=lambda s: s.split(','), nargs='*', help="""
        A mapping from variable names in the project to variable names in the
        datasets that should be used instead. Variable names should be
        separated by a comma.""", metavar='project-variable,variable-to-use')

    parser.update_arg('tight', short='t', group=output_grp)

    parser.update_arg('rc_file', short='rc')
    parser.pop_key('rc_file', 'metavar')

    parser.update_arg('encoding', short='e')

    parser.pop_key('enable_post', 'short')

    parser.update_arg('seaborn_style', short='sns')

    parser.update_arg('concat_dim', short='cd')

    if create:
        parser.create_arguments()

    return parser


def _load_dict(fname):
    with open(fname) as f:
        if fname.endswith('.yml') or fname.endswith('.yaml'):
            return yaml.load(f, Loader=yaml.SafeLoader)
        return pickle.load(f)


def _load_dims(s):
    s = s.split(',')
    if len(s) > 1:
        return {s[0]: list(map(int, s[1:]))}
    return {}


class AllVersionsAction(argparse.Action):

    def __init__(self, option_strings, dest=argparse.SUPPRESS, nargs=None,
                 default=argparse.SUPPRESS, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        kwargs['help'] = ("Print the versions of all plugins and requirements "
                          "and exit")
        kwargs['default'] = default
        super(AllVersionsAction, self).__init__(
            option_strings, nargs=0, dest=dest,
            **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        print(yaml.dump(psyplot.get_versions(), default_flow_style=False))
        sys.exit(0)


class ListPresetsAction(argparse.Action):

    def __init__(self, option_strings, dest=argparse.SUPPRESS, nargs=None,
                 default=argparse.SUPPRESS, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        kwargs['help'] = ("Print available presets and exit")
        kwargs['default'] = default
        super().__init__(option_strings, nargs=0, dest=dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        from psyplot.config.rcsetup import get_configdir
        presets_dir = osp.join(get_configdir(), 'presets')
        if not osp.exists(presets_dir):
            sys.exit(0)
        else:
            presets = {osp.splitext(osp.basename(fname))[0]: fname
                       for fname in glob.glob(osp.join(presets_dir, '*.yml'))}
            print('\n'.join(map(': '.join, presets.items())))
            sys.exit(0)

class ListPluginsAction(argparse.Action):

    def __init__(self, option_strings, dest=argparse.SUPPRESS, nargs=None,
                 default=argparse.SUPPRESS, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        kwargs['help'] = ("Print the names of the plugins and exit")
        kwargs['default'] = default
        super(ListPluginsAction, self).__init__(
            option_strings, nargs=0, dest=dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        print(yaml.dump(psyplot.rcParams._plugins, default_flow_style=False))
        sys.exit(0)


class ListPlotMethodsAction(argparse.Action):

    def __init__(self, option_strings, dest=argparse.SUPPRESS, nargs=None,
                 default=argparse.SUPPRESS, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        kwargs['help'] = "List the available plot methods and what they do"
        kwargs['default'] = default
        super(ListPlotMethodsAction, self).__init__(
            option_strings, nargs=0, dest=dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        pm_choices = {}
        for pm, d in filter(lambda t: t[1].get('plot_func', True),
                            six.iteritems(rcParams['project.plotters'])):
            pm_choices[pm] = d.get('summary') or (
                'Open and plot data via :class:`%s.%s` plotters' % (
                    d['module'], d['plotter_name']))
        if psyplot._project_imported:
            import psyplot.project as psy
            pm_choices.update(psy.plot._plot_methods)
        print(yaml.dump(pm_choices, default_flow_style=False))
        sys.exit(0)


class ListDsNamesAction(argparse.Action):
    """An action to list the used file names in a project"""

    def __init__(self, option_strings, dest=argparse.SUPPRESS, nargs=None,
                 default=argparse.SUPPRESS, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        kwargs['default'] = default
        super(ListDsNamesAction, self).__init__(
            option_strings, nargs=0, dest=dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if namespace.project is None:
            print('A project is required before this argument! Call syntax:\n'
                  '%s -p <project-file>.pkl %s' % (parser.prog, option_string))
            sys.exit(1)
        import psyplot.data as psyd
        import pickle
        with open(namespace.project, 'rb') as f:
            d = pickle.load(f)['arrays']
        names = list(filter(None, (
            t[0] for t in psyd.ArrayList._get_dsnames(d))))
        if names:
            print(yaml.dump(names, default_flow_style=False))
        sys.exit(0)


if __name__ == '__main__':
    main()
