bento_mdf
=======

Python 3 drivers for the graph [Model Description Format](https://github.com/CBIIT/bento-mdf)

This directory provides ``test-mdf.py``, a standalone command line MDF validator.

## Installation

Install the latest version (including scripts below) from GitHub using
an up-to-date pip:

	pip install bento-mdf

## Scripts

Scripts [`test-mdf.py`](./test-mdf.py) and
[`load-mdf.py`](./load-mdf.py) are included in the
distribution. `test-mdf` is a verbose validator that can be used to
find issues in a set of local MDFs using the [MDF
JSONSchema](../../schema/mdf-schema.yaml). `load-mdf` will load a
valid set of MDFs into an existing [Neo4j](https://neo4j.com) [Metamodel Database](https://github.com/CBIIT/bento-meta).


## `test-mdf` Usage

    $ test-mdf.py -h
    usage: test-mdf.py [-h] [--schema SCHEMA] [--quiet] [--log-file LOG_FILE]
                       mdf-file [mdf-file ...]

    Validate MDF against JSONSchema

    positional arguments:
      mdf-file             MDF yaml files for validation

    optional arguments:
      -h, --help           show this help message and exit
      --schema SCHEMA      MDF JSONschema file
      --quiet              Suppress output; return only exit value
      --log-file LOG_FILE  Log file name

See "Validator Notes" below.

## `load-mdf` Usage

    $ ./load-mdf.py -h
    usage: load-mdf.py [-h] --commit COMMIT [--handle HANDLE] [--user USER] [--passw PASSW]
                       [--bolt BoltURL] [--put]
                       [MDF-FILE ...]

    Load model in MDF into an MDB

    positional arguments:
      MDF-FILE         MDF file(s)/url(s)

    optional arguments:
      -h, --help       show this help message and exit
      --commit COMMIT  commit SHA1 for MDF instance (if any)
      --handle HANDLE  model handle
      --user USER      MDB username
      --passw PASSW    MDB password
      --bolt BoltURL   MDB Bolt url endpoint (specify as 'bolt://...')
      --put            Load model to database

## Validator `test-mdf.py`Notes

The ``--schema`` argument is optional. ``test-mdf.py`` will automatically retrieve the latest [mdf-schema.yaml](../../schema/mdf-schema.yaml) in the master branch of [this repo](https://github.com/CBIIT/bento-mdf).

The script tests both the syntax of the YAML (for both schema and MDF files), and the validity of the files with respect to the JSONSchema (for both schema and MDF files).

The errors are as emitted from the [PyYaml](https://pyyaml.org/wiki/PyYAMLDocumentation) and [jsonschema](https://python-jsonschema.readthedocs.io/en/stable/) packages, and can be rather obscure.

* Successful test

        $ test-mdf.py samples/ctdc_model_file.yaml samples/ctdc_model_properties_file.yaml 
        Checking schema YAML =====
        Checking as a JSON schema =====
        Checking instance YAML =====
        Checking instance against schema =====

* Bad YAML syntax

        $ test-mdf.py samples/ctdc_model_bad.yaml samples/ctdc_model_properties_file.yaml 
        Checking schema YAML =====
        Checking as a JSON schema =====
        Checking instance YAML =====
        YAML error in 'samples/ctdc_model_bad.yaml':
        while parsing a block mapping
          in "samples/ctdc_model_bad.yaml", line 1, column 1
        expected <block end>, but found '<block mapping start>'
          in "samples/ctdc_model_bad.yaml", line 3, column 3

* Schema-invalid YAML

        $ test-mdf.py samples/ctdc_model_file_invalid.yaml samples/ctdc_model_properties_file.yaml 
        Checking schema YAML =====
        Checking as a JSON schema =====
        Checking instance YAML =====
        Checking instance against schema =====
        ['show_node', 'specimen_id', 'biopsy_sequence_number', 'specimen_type'] is not of type 'object'
        
        Failed validating 'type' in schema['properties']['Nodes']['additionalProperties']:
            {'$id': '#nodeSpec',
             'properties': {'Category': {'$ref': '#/defs/snake_case_id'},
                            'Props': {'oneOf': [{'items': {'$ref': '#/defs/snake_case_id'},
                                                 'type': 'array',
                                                 'uniqueItems': True},
                                                {'type': 'null'}]},
                            'Tags': {'$ref': '#/defs/tagsSpec'}},
             'required': ['Props'],
             'type': 'object'}
        
        On instance['Nodes']['specimen']:
            ['show_node', 'specimen_id', 'biopsy_sequence_number', 'specimen_type']

## Testing the tester

The validator code itself can be tested as follows:

    pip install tox
    cd bento-mdf/validators/mdf-validate
    tox




