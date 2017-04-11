from setuptools import setup, find_packages


setup(name='psyplot_test',
      version='1.0.0',
      license="GPLv2",
      packages=find_packages(exclude=['docs', 'tests*', 'examples']),
      entry_points={'psyplot': ['plugin=psyplot_test.plugin',
                                'patches=psyplot_test.plugin:patches']},
      zip_safe=False)
