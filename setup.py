from setuptools import setup, find_packages

version = '0.1'

setup(name='django-vff',
      version=version,
      description="Django versioned file field",
      long_description="""\
Django file field that saves a new version of a file each time it is modified. Relies on a backend for the actual versioning (git backend provided).""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='django versioned file field',
      author='TERENA',
      author_email='eperez@yaco.es',
      url='http://pypi.python.org',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'GitPython',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
