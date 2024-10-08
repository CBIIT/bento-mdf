![Build Status](https://github.com/CBIIT/bento-mdf/actions/workflows/who-validates-the-validator.yml/badge.svg)

# Bento-MDF: Bento Graph Model Description Format

The Bento graph model description format allows a user to provide a
very simple, human-readable description of an overall [property
graph](https://en.wikipedia.org/wiki/Graph_(abstract_data_type))
model. The layout of nodes, relationships, node properties, and
relationship properties are specified in data structures expressed in
YAML-formatted _model description files_.

This repo holds tools for loading, validating, manipulating, and writing MDF. The latest MDF spec can be found in the [mdf-schema](./schema/mdf-schema.yaml). A detailed explanation of the format can be found in the [documenation](#documentation).

## Where to get the Python package

Install the latest version of the [`bento-mdf` Python package](https://pypi.org/project/bento-mdf/) from PyPI:

```sh
pip install bento-mdf
```

## Documentation

The complete documentation for the Model Description Format and `bento-mdf` package can be found [here on GitHub pages.](https://cbiit.github.io/bento-mdf/)