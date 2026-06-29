"""Tests for MDFValidator exception/error handling paths."""

from pathlib import Path
from unittest.mock import patch

import pytest
from bento_mdf.validator import MDFValidator, MDFSCHEMA_URL
from jsonschema import SchemaError, ValidationError
from yaml.constructor import ConstructorError
from yaml.parser import ParserError
from yaml.scanner import ScannerError

tdir = Path("tests/").resolve() if Path("tests").exists() else Path().resolve()

test_schema_file = tdir / "samples" / "mdf-schema.yaml"
test_mdf_files = [
    tdir / "samples" / "ctdc_model_file.yaml",
    tdir / "samples" / "ctdc_model_properties_file.yaml",
]


class TestLoadSchemaFromUrl:
    """Tests for load_schema_from_url error paths (lines 68-72)."""

    def test_network_error_returns_empty_string(self):
        v = MDFValidator(None)
        with patch("bento_mdf.validator.requests.get", side_effect=ConnectionError("fail")):
            result = v.load_schema_from_url("http://example.com/bad")
        assert result == ""

    def test_network_error_raises_when_raise_error(self):
        v = MDFValidator(None, raise_error=True)
        with patch("bento_mdf.validator.requests.get", side_effect=ConnectionError("fail")):
            with pytest.raises(ConnectionError):
                v.load_schema_from_url("http://example.com/bad")


class TestLoadSchemaFromFile:
    """Tests for load_schema_from_file error paths (lines 81-85)."""

    def test_nonexistent_file_returns_empty_string(self):
        v = MDFValidator(None)
        result = v.load_schema_from_file("/nonexistent/path/schema.yaml")
        assert result == ""

    def test_nonexistent_file_raises_when_raise_error(self):
        v = MDFValidator(None, raise_error=True)
        with pytest.raises(OSError):
            v.load_schema_from_file("/nonexistent/path/schema.yaml")


class TestLoadSchemaFromYaml:
    """Tests for load_schema_from_yaml error paths (lines 92-112)."""

    def test_constructor_error_returns_none(self):
        v = MDFValidator(None)
        v.schema = {}
        v.sch_file = "!!python/object:os.system ['echo hi']"
        with patch(
            "bento_mdf.validator.yaml.load",
            side_effect=ConstructorError("bad construct"),
        ):
            result = v.load_schema_from_yaml()
        assert result is None

    def test_constructor_error_raises_when_raise_error(self):
        v = MDFValidator(None, raise_error=True)
        v.schema = {}
        v.sch_file = "bad yaml"
        with patch(
            "bento_mdf.validator.yaml.load",
            side_effect=ConstructorError("bad construct"),
        ):
            with pytest.raises(ConstructorError):
                v.load_schema_from_yaml()

    def test_parser_error_returns_none(self):
        v = MDFValidator(None)
        v.schema = {}
        v.sch_file = "bad: yaml: content"
        with patch(
            "bento_mdf.validator.yaml.load",
            side_effect=ParserError("bad parse"),
        ):
            result = v.load_schema_from_yaml()
        assert result is None

    def test_parser_error_raises_when_raise_error(self):
        v = MDFValidator(None, raise_error=True)
        v.schema = {}
        v.sch_file = "bad yaml"
        with patch(
            "bento_mdf.validator.yaml.load",
            side_effect=ParserError("bad parse"),
        ):
            with pytest.raises(ParserError):
                v.load_schema_from_yaml()

    def test_generic_exception_returns_none(self):
        v = MDFValidator(None)
        v.sch_file = "something"
        with patch(
            "bento_mdf.validator.yaml.load",
            side_effect=RuntimeError("unexpected"),
        ):
            result = v.load_schema_from_yaml()
        assert result is None

    def test_generic_exception_raises_when_raise_error(self):
        v = MDFValidator(None, raise_error=True)
        v.sch_file = "something"
        with patch(
            "bento_mdf.validator.yaml.load",
            side_effect=RuntimeError("unexpected"),
        ):
            with pytest.raises(RuntimeError):
                v.load_schema_from_yaml()


class TestCheckSchemaAsJson:
    """Tests for check_schema_as_json error paths (lines 118-131)."""

    def test_no_schema_logs_error(self, caplog):
        v = MDFValidator(None)
        v.schema = None
        with caplog.at_level("ERROR"):
            v.check_schema_as_json()
        assert any("No schema found" in r.message for r in caplog.records)

    def test_schema_error_returns_none(self, caplog):
        v = MDFValidator(None)
        v.schema = {"type": "invalid_type_value"}
        with caplog.at_level("ERROR"):
            v.check_schema_as_json()
        assert any("MDF Schema error" in r.message for r in caplog.records)

    def test_schema_error_raises_when_raise_error(self):
        v = MDFValidator(None, raise_error=True)
        v.schema = {"type": "invalid_type_value"}
        with pytest.raises(SchemaError):
            v.check_schema_as_json()

    def test_generic_exception_in_check_schema(self):
        v = MDFValidator(None)
        v.schema = {"type": "object"}
        with patch(
            "bento_mdf.validator.Draft6Validator.check_schema",
            side_effect=RuntimeError("unexpected"),
        ):
            v.check_schema_as_json()

    def test_generic_exception_raises_when_raise_error(self):
        v = MDFValidator(None, raise_error=True)
        v.schema = {"type": "object"}
        with patch(
            "bento_mdf.validator.Draft6Validator.check_schema",
            side_effect=RuntimeError("unexpected"),
        ):
            with pytest.raises(RuntimeError):
                v.check_schema_as_json()


class TestLoadAndValidateSchema:
    """Tests for load_and_validate_schema cached return (line 136)."""

    def test_returns_cached_schema(self):
        v = MDFValidator(None)
        cached_schema = {"type": "object", "properties": {}}
        v.schema = cached_schema
        result = v.load_and_validate_schema()
        assert result is cached_schema


class TestLoadYamlFromInstFile:
    """Tests for load_yaml_from_inst_file invalid type (line 184)."""

    def test_invalid_file_type_logs_error(self, caplog):
        v = MDFValidator(None)
        with caplog.at_level("ERROR"):
            v.load_yaml_from_inst_file(12345)
        assert any("Invalid instance file type" in r.message for r in caplog.records)


class TestLoadAndValidateYaml:
    """Tests for load_and_validate_yaml error paths (lines 186-206)."""

    def test_no_inst_files_logs_error(self, caplog):
        v = MDFValidator(None)
        v.instance = None
        with caplog.at_level("ERROR"):
            v.load_and_validate_yaml()

    def test_no_inst_files_raises_when_raise_error(self):
        v = MDFValidator(None, raise_error=True)
        v.instance = None
        with pytest.raises(ValueError, match="No instance yaml"):
            v.load_and_validate_yaml()

    def test_scanner_error_returns_none(self, tmp_path):
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("key: [unclosed bracket")
        v = MDFValidator(None, str(bad_yaml), raise_error=False)
        v.instance = None
        result = v.load_and_validate_yaml()
        assert result is None

    def test_scanner_error_raises_when_raise_error(self, tmp_path):
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("key: [unclosed bracket")
        v = MDFValidator(None, str(bad_yaml), raise_error=True)
        v.instance = None
        with pytest.raises((ScannerError, ParserError)):
            v.load_and_validate_yaml()

    def test_generic_exception_returns_none(self):
        v = MDFValidator(None, "dummy.yaml", raise_error=False)
        v.instance = None
        with patch(
            "bento_mdf.validator.MDFValidator.load_yaml_from_inst_file",
            side_effect=RuntimeError("unexpected"),
        ):
            result = v.load_and_validate_yaml()
        assert result is None

    def test_generic_exception_raises_when_raise_error(self):
        v = MDFValidator(None, "dummy.yaml", raise_error=True)
        v.instance = None
        with patch(
            "bento_mdf.validator.MDFValidator.load_yaml_from_inst_file",
            side_effect=RuntimeError("unexpected"),
        ):
            with pytest.raises(RuntimeError):
                v.load_and_validate_yaml()


class TestValidateInstanceWithSchema:
    """Tests for validate_instance_with_schema error paths (lines 267-298)."""

    def test_no_schema_returns_none(self, caplog):
        v = MDFValidator(None)
        v.schema = None
        v.instance = {"some": "data"}
        with caplog.at_level("WARNING"):
            result = v.validate_instance_with_schema()
        assert result is None
        assert any("No valid schema" in r.message for r in caplog.records)

    def test_no_instance_returns_none(self, caplog):
        v = MDFValidator(None)
        v.schema = {"type": "object"}
        v.instance = None
        with caplog.at_level("WARNING"):
            result = v.validate_instance_with_schema()
        assert result is None
        assert any("No valid yaml instance" in r.message for r in caplog.records)

    def test_validation_error_verbose(self, caplog):
        v = MDFValidator(None)
        v.schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        from delfick_project.option_merge.merge import MergedOptions

        v.instance = MergedOptions()
        v.instance.update({"name": 123})
        v.inst_files = []
        with caplog.at_level("ERROR"):
            result = v.validate_instance_with_schema(verbose=True)
        assert result is None
        assert any("[detail]" in r.message for r in caplog.records)

    def test_validation_error_raises_when_raise_error(self):
        v = MDFValidator(None, raise_error=True)
        v.schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        from delfick_project.option_merge.merge import MergedOptions

        v.instance = MergedOptions()
        v.instance.update({"name": 123})
        v.inst_files = []
        with pytest.raises(ValidationError):
            v.validate_instance_with_schema()

    def test_generic_exception_returns_none(self):
        v = MDFValidator(None)
        v.schema = {"type": "object"}
        from delfick_project.option_merge.merge import MergedOptions

        v.instance = MergedOptions()
        v.instance.update({"key": "value"})
        with patch(
            "bento_mdf.validator.validate",
            side_effect=RuntimeError("unexpected"),
        ):
            result = v.validate_instance_with_schema()
        assert result is None

    def test_generic_exception_raises_when_raise_error(self):
        v = MDFValidator(None, raise_error=True)
        v.schema = {"type": "object"}
        from delfick_project.option_merge.merge import MergedOptions

        v.instance = MergedOptions()
        v.instance.update({"key": "value"})
        with patch(
            "bento_mdf.validator.validate",
            side_effect=RuntimeError("unexpected"),
        ):
            with pytest.raises(RuntimeError):
                v.validate_instance_with_schema()
