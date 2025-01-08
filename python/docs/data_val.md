# Data Validation with MDF

The MDF [PropDefinitions](#property-definitions) section describes properties (slots or variables), along with the data types that consitute valid values for those properties. Using this information, one can validate data that are meant to comply with these conditions.

The `MDFDataValidator` class uses the [Pydantic](https://docs.pydantic.dev/latest/) data validation library to interpret MDF nodes and properties as Python classes which have attributes whose values are automatically validated. This provides several options for performing data validation against an MDF model. Data to be validated simply needs to be expressed as a Python dict or as JSON. 

Example: Suppose you have defined a node called `sample` in MDF, with properties `sample_type` and `amount`:

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

You can then validate a list of dicts of `sample` data using `validate()` as follows:

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

## Available validation classes and data fields

The first argument of `validate` is a string, the class name, that represents a particular model node. Class names are created by CamelCasing the Node handles that appear in the MDF. Properties for Nodes become data fields within the node validation class. These are snake_case strings given by the MDF property handles.

Available node class names are found in the MDFDataValidator `node_classes` attribute. Available field (property) names for a node class can be retrieved with the `fields_of()` or `props_of()` method.

For example, using [test-model.yml](/python/tests/samples/test-model.yml):

```python
mdf = MDFReader("tests/samples/test-model.yml")
val = MDFDataValidator(mdf)
print( val.node_classes )
# ['Case', 'Diagnosis', 'File', 'Sample']
print( val.fields_of('Sample')
# ['sample_type', 'amount']
```

The second argument to `validate()` is the data to be validated against the given class. It is a dict or a list of dicts, whose keys are names of properties defined in the MDF for the given node, and whose values are actual data values to be validated. If all data records in the list are valid, `validate()` returns True; otherwise, it retuns False.

```python
if val.validate('Sample', {'sample_type': 'normal', 'amount':1.0}):
    print("Valid!")
else:
    print("Invalid.")
```

## The "Model Class"

An additional validation class is created that aggregates all Node classes. This can be used to validate a dict containing a data record for all model Nodes. The model class is named by appending 'Data' to the model handle. This name is found in `val.model_class`.

For example, [test-model.yml](/python/tests/samples/test-model.yml) has handle `test` and its model class is named `testData`. An example validation:

```python
data = {
    "case": {"case_id": "CASE-22"},
    "diagnosis": {
        "disease": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C102872",
        "date_of_dx": "1965-05-04T00:00:00",
    },
    "file": {"file_size": 150342, "md5sum": "9d4cf66a8472f2f97c4594758a06fbd0"},
    "sample": {"amount": 4.0, "sample_type": "normal"},
    }
assert v.validate('testData', data)
```

Note that the Node keys for data are in lower case.

## Inspecting validation errors

If `validate()` returns False, the attribute `last_validation_errors` will contain a dict of error lists emitted by Pydantic. The keys of the dict are the indexes in the data list of the records that errored; the values are a list of Pydantic [ValidationError](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.ValidationError) objects detailing the nature of the errors.

```python

    data = [
        {"md5sum": "9d4cf66a8472f2f97c4594758a06fbd0",
         "file_name": "grelf.txt",
         "file_size": 50},
        {"md5sum": "9d4cf66a8472f2f97c4594758a06Fbd0",
         "file_name": "grolf.txt",
         "file_size": 50.0},
        {"md5sum": "9d4cf66a8472f2f97c4594758a06Fbd0",
         "file_name": "grilf.txt",
         "file_size": "big"}
        ]
    v.validate('File', data)
    print(json.dumps(val.last_validation_errors, indent=4))
```

```json
    {
        "1": [
            {
                "type": "predicate_failed",
                "loc": [
                    "md5sum"
                ],
                "msg": "Predicate Pattern.fullmatch failed",
                "input": "9d4cf66a8472f2f97c4594758a06Fbd0"
            }
        ],
        "2": [
            {
                "type": "predicate_failed",
                "loc": [
                    "md5sum"
                ],
                "msg": "Predicate Pattern.fullmatch failed",
                "input": "9d4cf66a8472f2f97c4594758a06Fbd0"
            },
            {
                "type": "int_parsing",
                "loc": [
                    "file_size",
                    "int"
                ],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "big",
                "url": "https://errors.pydantic.dev/2.10/v/int_parsing"
            }
        ]
```

## Generated Validation Classes

`MDFDataValidator` generates a Python module containing Pydantic classes (generally known as "[models](https://docs.pydantic.dev/latest/concepts/models/)"). The module code is contained in `val.data_model`; it can be printed to a file and used as an independent package in other applications. 

The validator object creates this code using a [Jinja](https://jinja.palletsprojects.com/en/stable/templates/) template and imports it back dynamically with [`importlib`](https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly).

There is no need to deal directly with this machinery in the simplest case of data validation (above). However, you can take advantage of Pydantic features available to these classes by accessing them using `val.model_of()`.

```python
    # instantiate a validated object:
    sample1 = v.model_of('Sample')(sample_type="normal", amount="1.0")
    # get more detail on field types and validations (Pydantic BaseModel methods)
    pydantic_fields = v.model_of('Sample').model_fields()
```

## JSON Schema Representations

Pydantic has extensive JSON Schema generation facilities. For any validation class, a JSON Schema representation can be created that may be used for for data validation across many programming environments and languages, including Python and Javascript. For example, data validation schemas can be stored along side MDF models in their repos, and general tools using JSON Schema can be developed to enable external submitters to validate their data prior to submission.

JSON Schema for any available validation class can be generated with the `json_schema()` method:

```python
import json
print(json.dumps(val.json_schema('Diagnosis'), indent=4))
```
```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "properties": {
        "disease": {
            "anyOf": [
                {
                    "format": "uri",
                    "minLength": 1,
                    "type": "string"
                },
                {
                    "type": "null"
                }
            ],
            "title": "Disease"
        },
        "date_of_dx": {
            "anyOf": [
                {
                    "format": "date-time",
                    "type": "string"
                },
                {
                    "type": "null"
                }
            ],
            "title": "Date Of Dx"
        }
    },
    "required": [
        "disease",
        "date_of_dx"
    ],
    "title": "Diagnosis",
    "type": "object"
}
```

In Python, this JSON Schema could be used to validate data as follows:

```python
import jsonschema
jsonschema.validate(
    {"disease": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C102872",
     "date_of_dx": None},
    val.json_schema('Diagnosis'),
    format_checker=Draft202012Validator.FORMAT_CHECKER
)
```
