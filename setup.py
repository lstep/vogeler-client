from setuptools import setup, find_packages
import sys, os
import vogelerclient

version = vogelerclient.__version__

setup(name='vogelerclient',
      version=version,
      description="Python-based Configuration Management Framework - Client Part",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='cmdb management',
      author='Luc Stepniewski',
      author_email='luc.stepniewski@adelux.fr',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
#      package_data = {
#          'vogelerclientdata': ['data/*',],
#      },
      tests_require='nose',
      test_suite='nose.collector',

      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'amqplib',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      vogelerclient = vogelerclient.command:main
      """,
      )
