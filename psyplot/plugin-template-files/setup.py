"""Setup file for plugin PLUGIN_NAME

This file is used to install the package to your python distribution.
Installation goes simply via::

    python -m pip install .
"""

# Disclaimer
# ----------
#
# Copyright (C) YOUR-INSTITUTION
#
# This file is part of PLUGIN_NAME and is released under the GNU LGPL-3.O license.
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

from setuptools import setup, find_packages


setup(name='PLUGIN_NAME',
      version='PLUGIN_VERSION',
      description='PLUGIN_DESC',
      keywords='visualization psyplot',
      license="LGPL-3.0-only",
      packages=find_packages(exclude=['docs', 'tests*', 'examples']),
      install_requires=[
          'psyplot',
      ],
      classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Operating System :: OS Independent',
      ],

      entry_points={'psyplot': ['plugin=PLUGIN_PYNAME.plugin']},
      zip_safe=False)
