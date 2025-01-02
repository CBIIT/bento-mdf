import pytest
import re
import jsonschema
from pytest import raises
from bento_mdf import MDFReader, MDFDataValidator
from pydantic import ValidationError, BaseModel
from enum import Enum
from pathlib import Path
from pdb import set_trace

TDIR = Path("tests/").resolve() if Path("tests").exists() else Path().resolve()


def test_data_validator():

    m = MDFReader(TDIR / "samples" / "test-model.yml", handle="test")
    v = MDFDataValidator(m)
    compile(v.data_model, '<string>', 'exec')
    assert v.module
    assert v.model_class == 'testData'
    assert set(v.node_classes) == {'Case', 'Sample', 'File', 'Diagnosis'}
    assert set(v.enum_classes) == {'SampleTypeEnum'}
    assert issubclass(v.model_of('testData'), BaseModel)
    assert issubclass(v.model_of('Case'), BaseModel)
    assert issubclass(v.model_of('SampleTypeEnum'), Enum)
    pass


def test_data_validation():
    
    m = MDFReader(TDIR / "samples" / "test-model.yml", handle="test")
    v = MDFDataValidator(m)
    cs = v.validator('Case')
    smp = v.validator('Sample')
    fl = v.validator('File')
    dx =  v.validator('Diagnosis')
    md = v.validator('testData')
    assert cs({"case_id": "CASE-999"})
    with raises(ValidationError, match='fullmatch failed'):
        cs({"case_id": "CASE-99A"})
    assert smp({"sample_type": "tumor", "amount": 1.0})
    with raises(ValidationError, match='should be a valid number'):
        smp({"sample_type": "tumor", "amount": "dude"})
    with raises(ValidationError, match="should be 'normal' or 'tumor'"):
        smp({"sample_type": "narf", "amount": 1.0})
    assert fl({"md5sum": "9d4cf66a8472f2f97f4594758a06fbd0",
               "file_name": "grelf.txt",
               "file_size": 50})
    with raises(ValidationError, match="fullmatch failed"):
        fl({"md5sum": "9d4cf66a8472f2f97F4594758a06fbd0",
            "file_name": "grelf.txt",
            "file_size": 50})

    with raises(ValidationError, match="should be a valid integer"):
        fl({"md5sum": "9d4cf66a8472f2f97c4594758a06fbd0",
            "file_name": "grelf.txt",
            "file_size": 50.0}, strict=True)

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
    assert not v.validate('File', data)
    assert v.last_validation_errors
    assert {x for x in v.last_validation_errors} == {1, 2}

    data = {
        "case": {"case_id": "CASE-22"},
        "diagnosis": {"disease": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C102872"},
        "file": {"file_size": 150342, "md5sum": "9d4cf66a8472f2f97c4594758a06fbd0"},
        "sample": {"amount": 4.0, "sample_type": "normal"},
        }
    assert v.validate('testData', data)
    data_nulls = {
        "case": {"case_id": "CASE-22"},
        "diagnosis": {"disease": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C102872"},
        "file": {"file_size": None, "md5sum": "9d4cf66a8472f2f97c4594758a06fbd0"},
        "sample": {"amount": 4.0, "sample_type": None},
        }
    assert v.validate('testData', data_nulls)
    data_nulled_req = {
        "case": {"case_id": None},
        "diagnosis": {"disease": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C102872"},
        "file": {"file_size": None, "md5sum": "9d4cf66a8472f2f97c4594758a06fbd0"},
        "sample": {"amount": 4.0, "sample_type": None},
        }
    assert not v.validate('testData', data_nulled_req)
    assert re.match(".*should be a valid string", v.last_validation_errors[0][0]['msg'])
    
    pass


def test_jsonschema():
    m = MDFReader(TDIR / "samples" / "test-model.yml", handle="test")
    v = MDFDataValidator(m)
    js = v.json_schema('testData')
    assert js['$schema']
    data = {
        "case": {"case_id": "CASE-22"},
        "diagnosis": {"disease": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C102872"},
        "file": {"file_size": 150342, "md5sum": "9d4cf66a8472f2f97c4594758a06fbd0"},
        "sample": {"amount": 4.0, "sample_type": "normal"},
        }
    jsonschema.validate(data, js)
    data["sample"] = "alien"
    with raises(jsonschema.exceptions.ValidationError):
        jsonschema.validate(data, js)


def test_validator_for_gold_mdf():

    m = MDFReader(TDIR / "samples" / "crdc_datahub_mdf.yml")
    v = MDFDataValidator(m)
    assert v
    
