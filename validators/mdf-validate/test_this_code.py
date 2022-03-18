import pytest
import sys
sys.path.insert(0,".")
from yaml.parser import ParserError
from yaml.constructor import ConstructorError
from jsonschema import ValidationError, SchemaError, RefResolutionError
from MDFValidate.validator import MDFValidator
from pdb import set_trace

test_schema_file = 'samples/mdf-schema.yaml'
test_latest_schema = '../../schema/mdf-schema.yaml'
test_mdf_files = ['samples/ctdc_model_file.yaml','samples/ctdc_model_properties_file.yaml']
test_schema_bad = 'samples/mdf-bad-schema.yaml'
test_yaml_bad = 'samples/ctdc_model_bad.yaml'
test_yaml_with_keydup = 'samples/ctdc_model_keydup.yaml'
test_yaml_with_eltdup = 'samples/ctdc_model_eltdup.yaml'
test_mdf_files_invalid_wrt_schema = ['samples/ctdc_model_file_invalid.yaml','samples/ctdc_model_properties_file.yaml']
test_list_type_files = ['samples/ctdc_model_file.yaml','samples/list-type-test.yaml']
test_enum_kw_files = ['samples/ctdc_model_file.yaml','samples/ctdc_model_properties_enum_kw.yaml']
test_enum_and_type_kw_files = ['samples/ctdc_model_file.yaml','samples/ctdc_model_properties_enum_and_type_kw.yaml']

def test_with_all_File_args():
  sch = open(test_schema_file,"r")
  mdf0 = open(test_mdf_files[0],"r")
  mdf1 = open(test_mdf_files[1],"r")  
  assert MDFValidator(sch, mdf0, mdf1)
    
def test_with_all_str_args():
  assert MDFValidator(test_schema_file, *test_mdf_files)

def test_with_remote_schema():
  v = MDFValidator(None, *test_mdf_files)
  assert v
  assert v.load_and_validate_schema()
  assert v.load_and_validate_yaml()

def test_bad_yaml():
  v = MDFValidator(test_schema_file, test_yaml_bad, raiseError=True)
  with pytest.raises(ParserError):
    v.load_and_validate_yaml()

def test_keydup_yaml():
  v = MDFValidator(test_schema_file, test_yaml_with_keydup,raiseError=True)
  with pytest.raises(ConstructorError):
    v.load_and_validate_yaml()

def test_eltdup_yaml():
  v = MDFValidator(test_schema_file, test_yaml_with_eltdup, raiseError=True)
  with pytest.raises(ConstructorError):
    v.load_and_validate_yaml()
    
def test_bad_schema():
  # pytest.skip()
  v =  MDFValidator(test_schema_bad, raiseError=True)
  with pytest.raises(SchemaError):
    v.load_and_validate_schema()
   
def test_instance_not_valid_wrt_schema():
  v =  MDFValidator(test_schema_file, *test_mdf_files_invalid_wrt_schema, raiseError=True)  
  assert v.load_and_validate_schema()
  assert v.load_and_validate_yaml()
  with pytest.raises(ValidationError):
    v.validate_instance_with_schema()

def test_list_type():
  v = MDFValidator(test_latest_schema, *test_list_type_files)
  assert v
  assert v.load_and_validate_schema()
  assert v.load_and_validate_yaml()
  v.validate_instance_with_schema()  
  
def test_enum_vs_type_kw():
  v = MDFValidator(test_latest_schema, *test_enum_kw_files)
  assert v
  assert v.load_and_validate_schema()
  assert v.load_and_validate_yaml()
  v.validate_instance_with_schema()

def test_enum_and_type_kw():
  v = MDFValidator(test_latest_schema, *test_enum_and_type_kw_files, raiseError=True)
  assert v
  assert v.load_and_validate_schema()
  assert v.load_and_validate_yaml()
  with pytest.raises(ValidationError):
    v.validate_instance_with_schema()



