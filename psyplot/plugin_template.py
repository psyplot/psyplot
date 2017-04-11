"""Module for creating a new template for a psyplot plugin
"""
import funcargparse
import os
import os.path as osp
import shutil


def new_plugin(odir, py_name=None, version='0.0.1.dev0',
               description='New plugin'):
    """
    Create a new plugin for the psyplot package

    Parameters
    ----------
    odir: str
        The name of the directory where the data will be copied to. The
        directory must not exist! The name of the directory also defines the
        name of the package.
    py_name: str
        The name of the python package. If None, the basename of `odir` is used
        (and ``'-'`` is replaced by ``'_'``)
    version: str
        The version of the package
    description: str
        The description of the plugin"""
    name = osp.basename(odir)
    if py_name is None:
        py_name = name.replace('-', '_')

    src = osp.join(osp.dirname(__file__), 'plugin-template-files')
    # copy the source files
    shutil.copytree(src, odir)
    os.rename(osp.join(odir, 'plugin_template'), osp.join(odir, py_name))

    replacements = {'PLUGIN_NAME': name,
                    'PLUGIN_PYNAME': py_name,
                    'PLUGIN_VERSION': version,
                    'PLUGIN_DESC': description,
                    }
    files = [
        'README.md',
        'setup.py',
        osp.join(py_name, 'plugin.py'),
        osp.join(py_name, 'plotters.py'),
        osp.join(py_name, '__init__.py'),
        ]

    for fname in files:
        with open(osp.join(odir, fname)) as f:
            s = f.read()
        for key, val in replacements.items():
            s = s.replace(key, val)
        with open(osp.join(odir, fname), 'w') as f:
            f.write(s)


def main(args=None):
    parser = funcargparse.FuncArgParser()
    parser.setup_args(new_plugin)
    parser.update_short(version='v', description='d')
    parser.create_arguments()
    parser.parse2func(args)


if __name__ == '__main__':
    main()
