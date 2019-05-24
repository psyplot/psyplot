import os.path as osp
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys


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


def readme():
    with open('README.rst') as f:
        return f.read()


# read the version from version.py
with open(osp.join('psyplot', 'version.py')) as f:
    exec(f.read())


setup(name='psyplot',
      version=__version__,
      description='Python package for interactive data visualization',
      long_description=readme(),
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: OS Independent',
      ],
      keywords='visualization netcdf raster cartopy earth-sciences',
      project_urls={
          'Documentation': 'https://psyplot.readthedocs.io',
      },
      url='https://github.com/Chilipp/psyplot',
      author='Philipp Sommer',
      author_email='philipp.sommer@unil.ch',
      license="GPLv2",
      packages=find_packages(exclude=['docs', 'tests*', 'examples']),
      install_requires=[
          'matplotlib',
          'docrep',
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
      cmdclass={'test': PyTest},
      entry_points={'console_scripts': [
          'psyplot=psyplot.__main__:main',
          'psyplot-plugin=psyplot.plugin_template:main']},
      zip_safe=False)
