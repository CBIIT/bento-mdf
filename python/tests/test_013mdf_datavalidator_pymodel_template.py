"""Tests for the pymodel.py.jinja2 template code blocks.

Each test class targets a specific block or branch in the template and uses the
test-model-mdfdatavalidator.yml fixture, which intentionally contains properties
that exercise the major conditional branches:

  participant node
  ----------------
  - race           : value_type list / item_type value_set  → List[RaceEnum]
  - sex_at_birth   : value_set (Enum)                       → SexAtBirthEnum
  - occupation     : value_set (Enum)                       → OccupationEnum
  - participant_id : string                                 → str
  - guid           : string, not required                   → Optional[str]

  sample node  (newly added properties)
  -------------------------------------
  - sample_id      : string, required                       → str
  - sample_list_prop : value_type list / item_type string   → Optional[List[str]]
  - sample_bool_prop : boolean                              → Optional[bool]
  - sample_tbd_prop  : TBD                                  → Optional[Any]
"""

import ast
from pathlib import Path

import pytest
from bento_mdf import MDFReader
from bento_mdf.mdf.validator import MDFDataValidator

TDIR = Path("tests/").resolve() if Path("tests").exists() else Path().resolve()
TEST_MODEL_FILE = TDIR / "samples" / "test-model-mdfdatavalidator.yml"


@pytest.fixture(scope="module")
def validator():
    mdf = MDFReader(TEST_MODEL_FILE, handle="test_validator")
    return MDFDataValidator(mdf)


@pytest.fixture(scope="module")
def rendered(validator):
    """Return the Python source code produced by the template."""
    return validator.data_model


# ---------------------------------------------------------------------------
# Template output: basic validity
# ---------------------------------------------------------------------------


class TestTemplateOutputIsValidPython:
    """The template must always produce syntactically correct Python."""

    def test_rendered_parses_as_valid_python(self, rendered):
        """ast.parse raises SyntaxError on malformed output."""
        tree = ast.parse(rendered)
        assert tree is not None

    def test_rendered_is_non_empty_string(self, rendered):
        assert isinstance(rendered, str)
        assert len(rendered) > 0

    def test_rendered_contains_required_imports(self, rendered):
        assert "from enum import Enum" in rendered
        assert "from pydantic import" in rendered
        assert "from typing import" in rendered
        assert "Optional" in rendered
        assert "List" in rendered


# ---------------------------------------------------------------------------
# Template block: node class generation
# ---------------------------------------------------------------------------


class TestNodeClassGeneration:
    """Covers the {% for node in model.nodes.values() %} block."""

    def test_participant_class_is_generated(self, rendered):
        assert "class Participant(MDFBaseModel):" in rendered

    def test_sample_class_is_generated(self, rendered):
        assert "class Sample(MDFBaseModel):" in rendered

    def test_all_node_classes_present(self, rendered, validator):
        for cls in validator.node_classes:
            assert f"class {cls}(MDFBaseModel):" in rendered

    def test_node_classes_are_sorted(self, validator):
        classes = validator.node_classes
        assert classes == sorted(classes)


# ---------------------------------------------------------------------------
# Template block: top-level data class
# ---------------------------------------------------------------------------


class TestTopLevelDataClass:
    """Covers the class {{model.handle}}Data block at the end of the template."""

    def test_data_class_is_present(self, rendered, validator):
        assert f"class {validator.model_class}(BaseModel):" in rendered

    def test_data_class_references_participant(self, rendered):
        assert "participant: Participant" in rendered

    def test_data_class_references_sample(self, rendered):
        assert "sample: Sample" in rendered


# ---------------------------------------------------------------------------
# Template block: enum class generation (value_set branch)
# ---------------------------------------------------------------------------


class TestEnumClassGeneration:
    """Covers the {% if pr.value_domain == 'value_set' %} branch."""

    def test_enum_classes_are_generated(self, validator):
        assert len(validator.enum_classes) > 0

    def test_sex_at_birth_enum_class_present(self, rendered):
        assert "class SexAtBirthEnum(str, Enum):" in rendered

    def test_occupation_enum_class_present(self, rendered):
        assert "class OccupationEnum(str, Enum):" in rendered

    def test_enum_classes_are_sorted(self, validator):
        classes = validator.enum_classes
        assert classes == sorted(classes)

    def test_enum_field_declared_in_participant(self, rendered):
        # sex_at_birth should reference SexAtBirthEnum inside Participant
        assert "sex_at_birth" in rendered
        assert "SexAtBirthEnum" in rendered


# ---------------------------------------------------------------------------
# Template block: list / item_domain branch (sample_list_prop)
# ---------------------------------------------------------------------------


class TestListTypeBranch:
    """Covers the {% elif pr.item_domain is not none %} branch via sample_list_prop
    (value_type: list, item_type: string → item_domain='string').
    """

    def test_sample_list_prop_field_present(self, rendered):
        assert "sample_list_prop" in rendered

    def test_sample_list_prop_uses_list_wrapper(self, rendered):
        """The maybe_list filter should wrap the type in List[...]."""
        assert "List[str]" in rendered

    def test_sample_list_prop_is_optional_when_not_required(self, rendered):
        """Req: false means maybe_optional wraps with Optional."""
        # Confirm Optional[List[str]] appears for the non-required list prop
        assert "Optional[List[str]]" in rendered

    def test_sample_node_compiled_has_list_field(self, validator):
        """Runtime check: the Sample pydantic class has sample_list_prop field."""
        Sample = validator.model_of("Sample")
        assert "sample_list_prop" in Sample.model_fields


# ---------------------------------------------------------------------------
# Template block: boolean branch (sample_bool_prop)
# ---------------------------------------------------------------------------


class TestBooleanTypeBranch:
    """Covers the {% elif pr.value_domain == 'boolean' %} branch."""

    def test_sample_bool_prop_field_present(self, rendered):
        assert "sample_bool_prop" in rendered

    def test_sample_bool_prop_uses_bool_type(self, rendered):
        assert "bool" in rendered

    def test_sample_bool_prop_is_optional_when_not_required(self, rendered):
        assert "Optional[bool]" in rendered

    def test_sample_node_compiled_has_bool_field(self, validator):
        Sample = validator.model_of("Sample")
        assert "sample_bool_prop" in Sample.model_fields

    def test_sample_bool_field_accepts_true(self, validator):
        Sample = validator.model_of("Sample")
        instance = Sample(
            sample_id="S001",
            sample_bool_prop=True,
        )
        assert instance.sample_bool_prop is True

    def test_sample_bool_field_accepts_false(self, validator):
        Sample = validator.model_of("Sample")
        instance = Sample(
            sample_id="S001",
            sample_bool_prop=False,
        )
        assert instance.sample_bool_prop is False

    def test_sample_bool_field_accepts_none_when_optional(self, validator):
        Sample = validator.model_of("Sample")
        instance = Sample(sample_id="S001", sample_bool_prop=None)
        assert instance.sample_bool_prop is None


# ---------------------------------------------------------------------------
# Template block: TBD branch (sample_tbd_prop)
# ---------------------------------------------------------------------------


class TestTBDTypeBranch:
    """Covers the {% elif pr.value_domain == 'TBD' %} branch."""

    def test_sample_tbd_prop_field_present(self, rendered):
        assert "sample_tbd_prop" in rendered

    def test_sample_tbd_prop_uses_any_type(self, rendered):
        """TBD maps to Any in the typemap."""
        assert "Any" in rendered

    def test_sample_tbd_prop_is_optional_when_not_required(self, rendered):
        assert "Optional[Any]" in rendered

    def test_sample_node_compiled_has_tbd_field(self, validator):
        Sample = validator.model_of("Sample")
        assert "sample_tbd_prop" in Sample.model_fields

    def test_sample_tbd_field_accepts_string(self, validator):
        Sample = validator.model_of("Sample")
        instance = Sample(sample_id="S001", sample_tbd_prop="anything")
        assert instance.sample_tbd_prop == "anything"

    def test_sample_tbd_field_accepts_dict(self, validator):
        Sample = validator.model_of("Sample")
        instance = Sample(sample_id="S001", sample_tbd_prop={"key": "value"})
        assert instance.sample_tbd_prop == {"key": "value"}

    def test_sample_tbd_field_accepts_none_when_optional(self, validator):
        Sample = validator.model_of("Sample")
        instance = Sample(sample_id="S001", sample_tbd_prop=None)
        assert instance.sample_tbd_prop is None


# ---------------------------------------------------------------------------
# Template block: string branch (sample_id, participant_id, guid)
# ---------------------------------------------------------------------------


class TestStringTypeBranch:
    """Covers the {% elif pr.value_domain == 'string' %} branch."""

    def test_participant_id_field_uses_str(self, rendered):
        assert "participant_id" in rendered
        assert "str" in rendered

    def test_sample_id_field_uses_str(self, rendered):
        assert "sample_id" in rendered

    def test_required_string_is_not_optional(self, validator):
        """sample_id has Req: true → must not be Optional."""
        Sample = validator.model_of("Sample")
        field = Sample.model_fields["sample_id"]
        # A required field has no default (default is PydanticUndefined)
        assert field.is_required()

    def test_optional_string_has_default_none(self, validator):
        """guid has Req: false → should be Optional with default None."""
        Participant = validator.model_of("Participant")
        field = Participant.model_fields["guid"]
        assert not field.is_required()
