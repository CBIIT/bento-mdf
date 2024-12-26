import pytest
from bento_mdf import MDFReader, MDFDataValidator
from pathlib import Path
from pdb import set_trace

TDIR = Path("tests/").resolve() if Path("tests").exists() else Path().resolve()


def test_data_validator():

    m = MDFReader(TDIR / "samples" / "test-model.yml", handle="test")
    v = MDFDataValidator(m)
    v.generate_data_model()
    compile(v.data_model, '<string>', 'exec')
    data_model = v.import_data_model()
    assert data_model
    pass
    
