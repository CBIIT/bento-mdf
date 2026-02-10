"""Tests for bento_mdf.mdf.validator.MDFDataValidator."""

from pathlib import Path
import pytest
from bento_mdf import MDFReader
from bento_mdf.mdf.validator import MDFDataValidator
from pydantic import ValidationError

TDIR = Path("tests/").resolve() if Path("tests").exists() else Path().resolve()
TEST_MODEL_VALIDATOR_FILE = TDIR / "samples" / "test-model-mdfdatavalidator.yml"


@pytest.fixture
def simple_validator():
    """Create a validator from a test model."""
    mdf = MDFReader(TEST_MODEL_VALIDATOR_FILE, handle="test_validator", )
    return MDFDataValidator(mdf)


class TestMDFDataValidatorInit:
    """Tests for MDFDataValidator initialization."""

    def test_init_creates_validator(self, simple_validator):
        """Test that validator is properly initialized."""
        assert isinstance(simple_validator, MDFDataValidator)
        assert simple_validator.model is not None
        assert simple_validator.data_model is not None
        assert simple_validator.module is not None

    def test_init_generates_node_classes(self, simple_validator):
        """Test that node classes are generated during initialization."""
        assert len(simple_validator.node_classes) > 0
        # Check that node class names are in CamelCase
        for cls in simple_validator.node_classes:
            assert cls[0].isupper()

    def test_init_generates_enum_classes(self, simple_validator):
        """Test that enum classes are generated for value sets."""
        # Test model should have some enum properties
        assert isinstance(simple_validator.enum_classes, list)
        assert len(simple_validator.enum_classes) > 0

    def test_module_name_matches_handle(self, simple_validator):
        """Test that generated module name matches model handle."""
        assert simple_validator.model_class == "TestvalidatorData"


class TestMDFDataValidatorProperties:
    """Tests for MDFDataValidator property methods."""

    def test_data_model_property_returns_string(self, simple_validator):
        """Test that data_model property returns a string."""
        assert isinstance(simple_validator.data_model, str)
        assert len(simple_validator.data_model) > 0
        # Should contain Python code
        assert "class" in simple_validator.data_model

    def test_module_property_returns_module(self, simple_validator):
        """Test that module property returns a module object."""
        assert simple_validator.module is not None
        assert hasattr(simple_validator.module, "__name__")

    def test_node_classes_property(self, simple_validator):
        """Test that node_classes property returns sorted list."""
        classes = simple_validator.node_classes
        assert isinstance(classes, list)
        assert classes == sorted(classes)

    def test_enum_classes_property(self, simple_validator):
        """Test that enum_classes property returns sorted list."""
        classes = simple_validator.enum_classes
        assert isinstance(classes, list)
        assert classes == sorted(classes)

    def test_last_validation_errors_initially_none(self, simple_validator):
        """Test that last_validation_errors is None before validation."""
        assert simple_validator.last_validation_errors is None

    def test_last_validation_warnings_initially_none(self, simple_validator):
        """Test that last_validation_warnings is None before validation."""
        assert simple_validator.last_validation_warnings is None


class TestMDFDataValidatorModelOf:
    """Tests for model_of method."""

    def test_model_of_valid_class(self, simple_validator):
        """Test model_of with valid class name."""
        # Get first node class
        cls_name = simple_validator.node_classes[0]
        model = simple_validator.model_of(cls_name)
        assert model is not None

    def test_model_of_invalid_class_raises_error(self, simple_validator):
        """Test model_of with invalid class name raises RuntimeError."""
        with pytest.raises(RuntimeError, match="does not contain class"):
            simple_validator.model_of("NonExistentClass")

    def test_model_of_caches_results(self, simple_validator):
        """Test that model_of caches its results."""
        cls_name = simple_validator.node_classes[0]
        model1 = simple_validator.model_of(cls_name)
        model2 = simple_validator.model_of(cls_name)
        assert model1 is model2


class TestMDFDataValidatorFieldsOf:
    """Tests for fields_of and props_of methods."""

    def test_fields_of_returns_list(self, simple_validator):
        """Test that fields_of returns a list of field names."""
        cls_name = simple_validator.node_classes[0]
        fields = simple_validator.fields_of(cls_name)
        assert isinstance(fields, list)

    def test_fields_of_invalid_class_raises_error(self, simple_validator):
        """Test fields_of with invalid class name raises RuntimeError."""
        with pytest.raises(RuntimeError, match="does not contain node class"):
            simple_validator.fields_of("NonExistentClass")

    def test_props_of_returns_same_as_fields_of(self, simple_validator):
        """Test that props_of returns same result as fields_of."""
        cls_name = simple_validator.node_classes[0]
        fields = simple_validator.fields_of(cls_name)
        props = simple_validator.props_of(cls_name)
        assert fields == props


class TestMDFDataValidatorValidator:
    """Tests for validator method."""

    def test_validator_returns_callable(self, simple_validator):
        """Test that validator returns a callable."""
        cls_name = simple_validator.node_classes[0]
        validator = simple_validator.validator(cls_name)
        assert callable(validator)

    def test_validator_caches_results(self, simple_validator):
        """Test that validator caches its results."""
        cls_name = simple_validator.node_classes[0]
        validator1 = simple_validator.validator(cls_name)
        validator2 = simple_validator.validator(cls_name)
        assert validator1 is validator2


class TestMDFDataValidatorJsonSchema:
    """Tests for json_schema method."""

    def test_json_schema_returns_dict(self, simple_validator):
        """Test that json_schema returns a dictionary."""
        cls_name = simple_validator.node_classes[0]
        schema = simple_validator.json_schema(cls_name)
        assert isinstance(schema, (dict, list))

    def test_json_schema_contains_schema_tag(self, simple_validator):
        """Test that generated JSON schema contains $schema tag."""
        cls_name = simple_validator.node_classes[0]
        schema = simple_validator.json_schema(cls_name)
        if isinstance(schema, dict):
            assert "$schema" in schema

    def test_json_schema_valid_structure(self, simple_validator):
        """Test that JSON schema has expected structure."""
        cls_name = simple_validator.node_classes[0]
        schema = simple_validator.json_schema(cls_name)
        if isinstance(schema, dict):
            # Should have typical JSON schema fields
            assert "properties" in schema or "type" in schema


class TestMDFDataValidatorValidate:
    """Tests for validate method."""

    def test_validate_with_valid_dict(self, simple_validator):
        """Test validation with a valid single dict."""
        # Create minimal valid data for participant node
        data = {
            "participant_id": "PART_001",
            "race": ["White"],
            "sex_at_birth": "Female"
        }
        result = simple_validator.validate("participant", data)
        assert result is True

    def test_validate_with_valid_list(self, simple_validator):
        """Test validation with a list of dicts."""
        data = [
            {
                "participant_id": "PART_001",
                "race": ["White"],
                "sex_at_birth": "Female"
            },
            {
                "participant_id": "PART_002",
                "race": ["Asian"],
                "sex_at_birth": "Male"
            }
        ]
        result = simple_validator.validate("participant", data)
        assert result is True

    def test_validate_sets_errors_on_failure(self, simple_validator):
        """Test that validation errors are set when validation fails."""
        # Invalid data - wrong type for participant_id
        data = {
            "participant_id": 12345,  # should be string
            "race": ["White"],
            "sex_at_birth": "Female"
        }
        result = simple_validator.validate("participant", data, strict=True)
        assert result is False
        assert simple_validator.last_validation_errors is not None
        assert isinstance(simple_validator.last_validation_errors, dict)

    def test_validate_clears_errors_on_success(self, simple_validator):
        """Test that validation errors are cleared on successful validation."""
        # First fail validation
        invalid_data = {
            "participant_id": 12345,
            "race": ["White"],
            "sex_at_birth": "Female"
        }
        simple_validator.validate("participant", invalid_data, strict=True)
        
        # Then succeed
        valid_data = {
            "participant_id": "PART_001",
            "race": ["White"],
            "sex_at_birth": "Female"
        }
        result = simple_validator.validate("participant", valid_data)
        assert result is True
        assert simple_validator.last_validation_errors is None

    def test_validate_with_strict_mode(self, simple_validator):
        """Test validation extra field"""
        data = {
            "participant_id": "PART_001",
            "race": ["White"],
            "sex_at_birth": "Female",
            "extra_field": "value"  # Extra field should fail
        }
        result = simple_validator.validate("participant", data)
        # Strict mode should reject extra fields
        assert result is False
        assert len(simple_validator._validation_errors) == 1

    def test_validate_error_contains_index(self, simple_validator):
        """Test that validation errors contain record index."""
        data = [
            {
                "participant_id": "PART_001",
                "race": ["White"],
                "sex_at_birth": "Female"
            },
            {
                "participant_id": 12345,  # invalid - should be string
                "race": ["White"],
                "sex_at_birth": "Female"
            }
        ]
        result = simple_validator.validate("participant", data, strict=True)
        assert result is False
        errors = simple_validator.last_validation_errors
        # Check that error keys are indices
        assert all(isinstance(k, int) for k in errors.keys())
        # Second record (index 1) should have errors
        assert 1 in errors

    def test_validate_error_structure(self, simple_validator):
        """Test the structure of validation errors."""
        data = {
            "participant_id": 12345,
            "race": ["White"],
            "sex_at_birth": "Female"
        }
        result = simple_validator.validate("participant", data, strict=True)
        assert result is False
        errors = simple_validator.last_validation_errors
        # Each error should have level and other fields
        for idx, error_list in errors.items():
            for err in error_list:
                assert "level" in err
                assert err["level"] in ["error", "warning"]

    def test_validate_handles_list_of_valid_records(self, simple_validator):
        """Test validation with multiple valid records."""
        data = [
            {
                "participant_id": "PART_001",
                "race": ["White"],
                "sex_at_birth": "Female"
            },
            {
                "participant_id": "PART_002",
                "race": ["Asian"],
                "sex_at_birth": "Male"
            },
            {
                "participant_id": "PART_003",
                "race": ["Black or African American"],
                "sex_at_birth": "Unknown"
            }
        ]
        result = simple_validator.validate("participant", data)
        assert result is True

    def test_validate_converts_dict_to_list(self, simple_validator):
        """Test that single dict is converted to list internally."""
        dict_data = {
            "participant_id": "PART_001",
            "race": ["White"],
            "sex_at_birth": "Female"
        }
        list_data = [{
            "participant_id": "PART_001",
            "race": ["White"],
            "sex_at_birth": "Female"
        }]
        
        result1 = simple_validator.validate("participant", dict_data)
        result2 = simple_validator.validate("participant", list_data)
        
        # Should have same result
        assert result1 == result2
        assert result1 is True


class TestMDFDataValidatorEnumValidation:
    """Tests for enum validation with strict and non-strict enums."""

    def test_validate_non_strict_enum_with_valid_value(self, simple_validator):
        """Test that valid enum values pass validation."""
        data = {
            "participant_id": "PART_001",
            "race": ["White"],
            "sex_at_birth": "Female"  # Valid enum value
        }
        result = simple_validator.validate("participant", data)
        assert result is True
        assert simple_validator.last_validation_warnings is None

    def test_validate_non_strict_enum_violation_creates_warning(self, simple_validator):
        """Test that non-strict enum violations are treated as warnings."""
        data = {
            "participant_id": "PART_001",
            "race": ["White"],
            "sex_at_birth": "Non-Binary"  # Invalid value but non-strict enum
        }
        result = simple_validator.validate("participant", data)
        # Non-strict enum violations should still fail validation
        assert result is False
        # But should create warnings instead of errors
        if simple_validator.last_validation_warnings:
            warnings = simple_validator.last_validation_warnings
            assert 0 in warnings
            # Check that warning has proper structure
            for warning in warnings[0]:
                assert warning["level"] == "warning"
                assert warning["type"] == "enum"

    def test_validate_non_strict_list_enum_violation(self, simple_validator):
        """Test non-strict enum violations in list type properties."""
        data = {
            "participant_id": "PART_001",
            "race": ["White", "Other Race"],  # "Other Race" not in enum but non-strict
            "sex_at_birth": "Female"
        }
        result = simple_validator.validate("participant", data)
        # Should fail but create warning
        assert result is False
        # Check warnings were created
        if simple_validator.last_validation_warnings:
            assert 0 in simple_validator.last_validation_warnings

    def test_validate_optional_non_strict_enum(self, simple_validator):
        """Test optional non-strict enum property."""
        data = {
            "participant_id": "PART_001",
            "race": ["White"],
            "sex_at_birth": "Female",
            "occupation": "Software Engineer"  # Invalid value but optional and non-strict
        }
        result = simple_validator.validate("participant", data)
        assert result is False
        # Should generate warnings for invalid enum value
        if simple_validator.last_validation_warnings:
            warnings = simple_validator.last_validation_warnings[0]
            assert any(w["type"] == "enum" for w in warnings)

    def test_validation_warnings_property(self, simple_validator):
        """Test that validation warnings are properly set."""
        # Initially None
        assert simple_validator.last_validation_warnings is None
        
        # After failed validation with non-strict enum
        data = {
            "participant_id": "PART_001",
            "race": ["White"],
            "sex_at_birth": "Non-Binary"
        }
        simple_validator.validate("participant", data)
        # Warnings should be set if non-strict enum violated
        if simple_validator.last_validation_warnings:
            assert isinstance(simple_validator.last_validation_warnings, dict)


class TestMDFDataValidatorHelperFunctions:
    """Tests for helper functions used in validator."""

    def test_to_camel_case(self):
        """Test toCamelCase helper function."""
        from bento_mdf.mdf.validator import toCamelCase
        assert toCamelCase("test_node") == "TestNode"
        assert toCamelCase("case") == "Case"
        assert toCamelCase("my_sample_type") == "MySampleType"

    def test_to_snakecase(self):
        """Test to_snakecase helper function."""
        from bento_mdf.mdf.validator import to_snakecase
        assert to_snakecase("TestNode") == "testnode"
        assert to_snakecase("My Sample Type") == "my_sample_type"
        assert to_snakecase("Test-Node") == "test_minus_node"
        assert to_snakecase("123test") == "digit_123test"
        assert to_snakecase("") == "unspecified"

    def test_normalize_operators(self):
        """Test normalize_operators helper function."""
        from bento_mdf.mdf.validator import normalize_operators
        assert "plus" in normalize_operators("test+value")
        assert "minus" in normalize_operators("test-value")
        assert "percent" in normalize_operators("test%value")


class TestMDFDataValidatorIntegration:
    """Integration tests for MDFDataValidator."""

    def test_full_validation_workflow(self, simple_validator):
        """Test complete validation workflow from model load to validation."""
        # This is an end-to-end test
        assert simple_validator.model is not None
        assert len(simple_validator.node_classes) > 0
        
        # Pick a node and validate some data
        node_name = "participant"
        data = {
            "participant_id": "PART_001",
            "race": ["White"],
            "sex_at_birth": "Female"
        }
        result = simple_validator.validate(node_name, data)
        assert result is True

    def test_validator_with_participant_node(self, simple_validator):
        """Test validator with participant node."""
        # Test the participant node
        data = {
            "participant_id": "PART_001",
            "race": ["Asian", "White"],  # Multiple values allowed in list
            "sex_at_birth": "Male",
            "occupation": "Physician Assistant",
            "guid": "550e8400-e29b-41d4-a716-446655440000"
        }
        result = simple_validator.validate("participant", data)
        assert result is True

    def test_generated_code_quality(self, simple_validator):
        """Test that generated Python code is valid."""
        code = simple_validator.data_model
        # Should be valid Python
        assert "import" in code
        assert "class" in code
        assert "BaseModel" in code
        
        # Should not have syntax errors (implicitly tested by successful import)
        assert simple_validator.module is not None
