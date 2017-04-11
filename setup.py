import os.path as osp
from setuptools import setup, find_packages
import sys

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []


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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Operating System :: OS Independent',
      ],
      keywords='visualization netcdf raster cartopy earth-sciences',
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
          'PyYAML'
      ],
      package_data={'psyplot': [
          osp.join('psyplot', 'plugin-template-files', '*'),
          osp.join('psyplot', 'plugin-template-files', 'plugin_template', '*'),
          ]},
      include_package_data=True,
      setup_requires=pytest_runner,
      tests_require=['pytest'],
      entry_points={'console_scripts': [
          'psyplot=psyplot.__main__:main',
          'psyplot-plugin=psyplot.plugin_template:main']},
      zip_safe=False)
