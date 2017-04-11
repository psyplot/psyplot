"""Setup file for plugin PLUGIN_NAME

This file is used to install the package to your python distribution.
Installation goes simply via::

    python setup.py install
"""

from setuptools import setup, find_packages


setup(name='PLUGIN_NAME',
      version='PLUGIN_VERSION',
      description='PLUGIN_DESC',
      keywords='visualization psyplot',
      license="GPLv2",
      packages=find_packages(exclude=['docs', 'tests*', 'examples']),
      install_requires=[
          'psyplot',
      ],
      entry_points={'psyplot': ['plugin=PLUGIN_PYNAME.plugin']},
      zip_safe=False)
