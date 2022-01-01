from setuptools import setup, find_packages
setup(
  name="mdf-validate",
  version="0.2",
  packages=find_packages(),
  scripts=['test-mdf.py'],
  install_requires=[
    'jsonschema>=3.0.1',
    'PyYAML>=5.1.1',
    'delfick-project',
    'requests'
    ],
  tests_require=[
    'jsonschema>=3.0.1',
    'PyYAML>=5.1.1',
    'pytest'
    ]
  )
