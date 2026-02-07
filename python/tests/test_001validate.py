from pathlib import Path

import pytest
from bento_mdf.validator import MDFValidator
from jsonschema import SchemaError, ValidationError
from yaml.constructor import ConstructorError
from yaml.parser import ParserError

tdir = Path("tests/").resolve() if Path("tests").exists() else Path().resolve()


test_schema_file = tdir / "samples" / "mdf-schema.yaml"
test_latest_schema = tdir.parents[1] / "schema/mdf-schema.yaml"
test_mdf_files = [
    tdir / "samples" / "ctdc_model_file.yaml",
    tdir / "samples" / "ctdc_model_properties_file.yaml",
]
test_schema_bad = tdir / "samples" / "mdf-bad-schema.yaml"
test_yaml_bad = tdir / "samples" / "ctdc_model_bad.yaml"
test_yaml_with_keydup = tdir / "samples/ctdc_model_keydup.yaml"
test_yaml_with_eltdup = tdir / "samples/ctdc_model_eltdup.yaml"
test_mdf_files_invalid_wrt_schema = [
    tdir / "samples" / "ctdc_model_file_invalid.yaml",
    tdir / "samples" / "ctdc_model_properties_file.yaml",
]
test_list_type_files = [
    tdir / "samples" / "ctdc_model_file.yaml",
    tdir / "samples" / "list-type-test.yaml",
]
test_enum_kw_files = [
    tdir / "samples" / "ctdc_model_file.yaml",
    tdir / "samples" / "ctdc_model_properties_enum_kw.yaml",
]
test_enum_and_type_kw_files = [
    tdir / "samples" / "ctdc_model_file.yaml",
    tdir / "samples" / "ctdc_model_properties_enum_and_type_kw.yaml",
]
crdc_dh_file = tdir / "samples" / "crdc_datahub_mdf.yml"
test_model_file = tdir / "samples" / "test-model.yml"
test_model_file_bad_type_value = tdir / "samples" / "test-model-bad-type-value-1.yml"
test_model_file_bad_list_type = tdir / "samples" / "test-model-bad-list-type.yml"
test_model_null_cde = tdir / "samples" / "test-model-null-cde.yml"


def test_with_all_file_args():
    sch = test_schema_file.open()
    mdf0 = test_mdf_files[0].open()
    mdf1 = test_mdf_files[1].open()
    assert MDFValidator(sch, mdf0, mdf1)


def test_with_all_str_args():
    assert MDFValidator(str(test_schema_file), *[str(f) for f in test_mdf_files])


def test_with_remote_schema():
    v = MDFValidator(None, *test_mdf_files)
    assert v
    assert v.load_and_validate_schema()
    assert v.load_and_validate_yaml()


def test_bad_yaml():
    v = MDFValidator(test_schema_file, test_yaml_bad, raise_error=True)
    with pytest.raises(ParserError):
        v.load_and_validate_yaml()


def test_keydup_yaml():
    v = MDFValidator(test_schema_file, test_yaml_with_keydup, raise_error=True)
    with pytest.raises(ConstructorError):
        v.load_and_validate_yaml()


def test_eltdup_yaml():
    v = MDFValidator(test_schema_file, test_yaml_with_eltdup, raise_error=True)
    with pytest.raises(ConstructorError):
        v.load_and_validate_yaml()


def test_bad_schema():
    v = MDFValidator(test_schema_bad, raise_error=True)
    with pytest.raises(SchemaError):
        v.load_and_validate_schema()


def test_instance_not_valid_wrt_schema():
    v = MDFValidator(
        test_schema_file,
        *test_mdf_files_invalid_wrt_schema,
        raise_error=True,
    )
    assert v.load_and_validate_schema()
    assert v.load_and_validate_yaml()
    with pytest.raises(ValidationError):
        v.validate_instance_with_schema()


def test_validation_errors_include_line_numbers(caplog):
    v = MDFValidator(
        test_schema_file,
        *test_mdf_files_invalid_wrt_schema,
    )
    assert v.load_and_validate_schema()
    assert v.load_and_validate_yaml()
    with caplog.at_level("ERROR"):
        result = v.validate_instance_with_schema()
    assert result is None
    assert any("line" in rec.message for rec in caplog.records)


def test_list_type():
    v = MDFValidator(test_latest_schema, *test_list_type_files)
    assert v
    assert v.load_and_validate_schema()
    assert v.load_and_validate_yaml()
    assert v.validate_instance_with_schema()


def test_enum_vs_type_kw():
    v = MDFValidator(test_latest_schema, *test_enum_kw_files)
    assert v
    assert v.load_and_validate_schema()
    assert v.load_and_validate_yaml()
    assert v.validate_instance_with_schema()


def test_enum_and_type_kw():
    v = MDFValidator(test_latest_schema, *test_enum_and_type_kw_files, raise_error=True)
    assert v
    assert v.load_and_validate_schema()
    assert v.load_and_validate_yaml()
    with pytest.raises(ValidationError):
        v.validate_instance_with_schema()


def test_validate_crdc_model():
    v = MDFValidator(test_latest_schema, crdc_dh_file)
    assert v
    assert v.load_and_validate_schema()
    assert v.load_and_validate_yaml()
    assert v.validate_instance_with_schema()


def test_example_model():
    v = MDFValidator(test_latest_schema, test_model_file)
    assert v
    assert v.load_and_validate_schema()
    assert v.load_and_validate_yaml()
    assert v.validate_instance_with_schema()


def test_bad_type_value():
    # test that 'Type: enum' is invalid
    v = MDFValidator(
        test_latest_schema, test_model_file_bad_type_value, raise_error=True
    )
    assert v
    assert v.load_and_validate_schema()
    assert v.load_and_validate_yaml()
    with pytest.raises(ValidationError):
        v.validate_instance_with_schema()


def test_bad_list_type():
    # tests invalid list type spec
    v = MDFValidator(
        test_latest_schema, test_model_file_bad_list_type, raise_error=True
    )
    assert v
    assert v.load_and_validate_schema()
    assert v.load_and_validate_yaml()
    with pytest.raises(ValidationError):
        v.validate_instance_with_schema()


def test_use_null_cde_validates():
    """
    Test that MDF with useNullCDE attribute validates against schema.

    Verifies the MDF schema accepts useNullCDE in Term sections.
    """
    v = MDFValidator(test_latest_schema, test_model_null_cde)
    assert v
    assert v.load_and_validate_schema()
    assert v.load_and_validate_yaml()
    assert v.validate_instance_with_schema()
