import pytest
from pytest import raises
from bento_mdf import MDFReader, MDFDataValidator
from pydantic import ValidationError
from pathlib import Path
from pdb import set_trace

TDIR = Path("tests/").resolve() if Path("tests").exists() else Path().resolve()


def test_data_validator():

    m = MDFReader(TDIR / "samples" / "test-model.yml", handle="test")
    v = MDFDataValidator(m)
    compile(v.data_model, '<string>', 'exec')
    assert v.data_module
    assert v.module_name == 'testData'
    assert set(v.node_classes) == {'Case', 'Sample', 'File', 'Diagnosis'}
    assert set(v.enum_classes) == {'SampleTypeEnum'}
    pass


def test_data_validation():
    
    m = MDFReader(TDIR / "samples" / "test-model.yml", handle="test")
    v = MDFDataValidator(m)
    cs = v.adapter('Case')
    smp = v.adapter('Sample')
    fl = v.adapter('File')
    dx =  v.adapter('Diagnosis')
    assert cs.validate_python({"case_id": "CASE-999"})
    with raises(ValidationError, match='fullmatch failed'):
        cs.validate_python({"case_id": "CASE-99A"})
    assert smp.validate_python({"sample_type": "tumor", "amount": 1.0})
    with raises(ValidationError, match='should be a valid number'):
        smp.validate_python({"sample_type": "tumor", "amount": "dude"})
    with raises(ValidationError, match="should be 'normal' or 'tumor'"):
        smp.validate_python({"sample_type": "narf", "amount": 1.0})
    assert fl.validate_python({"md5sum": "9d4cf66a8472f2f97f4594758a06fbd0",
                               "file_name": "grelf.txt",
                               "file_size": 50})
    with raises(ValidationError, match="fullmatch failed"):
        fl.validate_python({"md5sum": "9d4cf66a8472f2f97F4594758a06fbd0",
                            "file_name": "grelf.txt",
                            "file_size": 50})

    with raises(ValidationError, match="should be a valid integer"):
        fl.validate_python({"md5sum": "9d4cf66a8472f2f97c4594758a06fbd0",
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
    pass

def test_validator_for_gold_mdf():

    m = MDFReader(TDIR / "samples" / "crdc_datahub_mdf.yml")
    v = MDFDataValidator(m)
    assert v
    
