import os
import os.path as osp
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys


if os.getenv("READTHEDOCS") == "True":
    # to make versioneer working, we need to unshallow this repo
    # because RTD does a checkout with --depth 50
    import subprocess as spr
    rootdir = osp.dirname(__file__)
    spr.call(["git", "-C", rootdir, "fetch", "--unshallow", "origin"])


import versioneer


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ''

    def run_tests(self):
        import shlex
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


version = versioneer.get_version()


def readme():
    with open('README.rst') as f:
        return f.read()


# read the version from version.py
with open(osp.join('psyplot', 'version.py')) as f:
    exec(f.read())

cmdclass = versioneer.get_cmdclass({'test': PyTest})

setup(name='psyplot',
      version=version,
      description='Python package for interactive data visualization',
      long_description=readme(),
      long_description_content_type="text/x-rst",
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Operating System :: OS Independent',
      ],
      python_requires=">=3.6",
      keywords='visualization netcdf raster cartopy earth-sciences',
      project_urls={
          'Documentation': 'https://psyplot.readthedocs.io',
          'Source': 'https://github.com/psyplot/psyplot',
          'Tracker': 'https://github.com/psyplot/psyplot/issues',
      },
      url='https://github.com/psyplot/psyplot',
      author='Philipp Sommer',
      author_email='philipp.sommer@hzg.de',
      license="GPLv2",
      packages=find_packages(exclude=['docs', 'tests*', 'examples']),
      install_requires=[
          'matplotlib',
          'docrep>=0.3',
          'funcargparse',
          'xarray',
          'PyYAML>=4.2b4'
      ],
      package_data={'psyplot': [
          osp.join('psyplot', 'plugin-template-files', '*'),
          osp.join('psyplot', 'plugin-template-files', 'plugin_template', '*'),
          ]},
      include_package_data=True,
      tests_require=['pytest'],
      cmdclass=cmdclass,
      entry_points={'console_scripts': [
          'psyplot=psyplot.__main__:main',
          'psyplot-plugin=psyplot.plugin_template:main']},
      zip_safe=False)
