# Data Validation with MDF

The MDF [PropDefinitions](#property-definitions) section describes properties (slots or variables), along with the data types that consitute valid values for those properties. Using this information, one can validate data that are meant to comply with these conditions.

The `MDFDataValidator` class uses the [Pydantic](https://docs.pydantic.dev/latest/) data validation library to interpret MDF nodes and properties as Python classes having attributes whose values are automatically validated. This provides several options for performing data validation against an MDF model. Data simply needs to be expressed as a Python dict or as JSON. Suppose you have defined a node `sample` in MDF, with properties `sample_type` and `amount`:

```yaml
# sample-model.yml
Handle: test
Nodes:
  sample:
    Props:
      - sample_type
      - amount
PropDefinitions:
  sample_type:
    Enum:
      - normal
      - tumor
  amount:
    Type:
      units:
        - mg
      value_type: number
```

Then you can validate a list of dicts of `sample` data:

```yaml
from bento_mdf import MDFReader, MDFDataValidator
    mdf = MDFReader("sample-model.yml")
    val = MDFDataValidator(mdf)
    result = val.validate('Sample', 
                          [{"sample_type": "normal", "amount": 0.50},
                           {"sample_type": "tumor", "amount": 1.0},
                           {"sample_type": "wrong", "amount": "fred"}])
    assert result is False # at least one record was invalid
    assert val.last_validation_errors[2] # the last record has error info
```

## Generated Validation Classes

`MDFDataValidator` generates a Python module containing Pydantic classes (known as "models"). The module code is contained in `v.data_model`; it can be printed to a file and used independently. The validator object creates it and imports it dynamically; there is no need to deal directly with it in the simplest case of data validation (above).

The Pydantic classes themselves, however, can be accessed using `model_of()`:

```python
    # instantiate a validated object:
    sample1 = v.model_of('Sample')(sample_type="normal", amount="1.0")
```

The class names are generally camelCase versions of MDF Nodes, and their attributes are Property handles. The class names are available on the MDFDataValidator object:

```python
    pymodel = v.model_of( v.model_class )
    pynodes = {cls : v.model_of(cls) for cls in v.node_classes}
    pyenums = {cls : v.model_of(cls) for cls in v.enum_classes}
```

## JSON Schema Representations
