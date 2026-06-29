"""Tests for MDFReader error/warning handling paths."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import responses
from bento_mdf.mdf import MDF
from bento_meta.entity import ArgError
from bento_meta.model import Model

TDIR = Path("tests/").resolve() if Path("tests").exists() else Path().resolve()
TEST_MODEL_FILE = TDIR / "samples" / "test-model.yml"
TEST_SCHEMA_FILE = TDIR / "samples" / "mdf-schema.yaml"


class TestModelProperty:
    """Tests for the model property error path (lines 104-106)."""

    def test_model_property_raises_when_no_model(self):
        m = MDF(handle="test")
        m._model = None
        with pytest.raises(ArgError, match="Can't fetch model"):
            _ = m.model


class TestLoadYaml:
    """Tests for load_yaml error paths (lines 104-106, 126-130)."""

    def test_load_yaml_schema_failure(self):
        m = MDF(handle="test")
        m.files = [TEST_MODEL_FILE]
        with patch(
            "bento_mdf.mdf.reader.MDFValidator.load_and_validate_schema",
            return_value=None,
        ):
            with pytest.raises(ValueError, match="Error loading & validating MDF schema"):
                m.load_yaml()

    def test_load_yaml_instance_failure(self):
        m = MDF(handle="test")
        m.files = [TEST_MODEL_FILE]
        with patch(
            "bento_mdf.mdf.reader.MDFValidator.load_and_validate_yaml",
            return_value=None,
        ):
            with pytest.raises(ValueError, match="Error loading & validating YAML instance"):
                m.load_yaml()

    def test_load_yaml_from_url_request_failure(self):
        m = MDF(handle="test", raise_error=True)
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                "https://example.com/model.yml",
                body=responses.ConnectionError("fail"),
            )
            with pytest.raises(ArgError, match="Fetching url"):
                m.files = ["https://example.com/model.yml"]
                m.load_yaml()

    def test_load_yaml_from_url_no_raise(self, caplog):
        m = MDF(handle="test", raise_error=False)
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                "https://example.com/model.yml",
                body=responses.ConnectionError("fail"),
            )
            m.files = ["https://example.com/model.yml"]
            with pytest.raises(Exception):
                m.load_yaml()


class TestCreateModel:
    """Tests for create_model error paths (lines 183-184, 198-199, 208-209)."""

    def test_no_handle_logs_error(self, caplog):
        m = MDF(handle="test", ignore_enum_by_reference=True)
        m.files = [TEST_MODEL_FILE]
        m.load_yaml()
        m.handle = None
        m.mdf.pop("Handle", None)
        with caplog.at_level("ERROR"):
            with pytest.raises(ArgError):
                m.create_model()
        assert any("Model handle not present" in r.message for r in caplog.records)

    def test_raise_error_on_failure(self, caplog):
        m = MDF(handle="test", ignore_enum_by_reference=True)
        m.files = [TEST_MODEL_FILE]
        m.load_yaml()
        m.handle = None
        m.mdf.pop("Handle", None)
        with pytest.raises((ArgError, RuntimeError)):
            m.create_model(raise_error=True)


class TestCreateTerms:
    """Tests for create_terms error paths (lines 221-228)."""

    def test_term_missing_value_key(self, caplog):
        m = MDF(handle="test", ignore_enum_by_reference=True)
        m.files = [TEST_MODEL_FILE]
        m.load_yaml()
        m.mdf["Terms"] = {"bad_term": {"Origin": "test"}}
        with caplog.at_level("ERROR"):
            m.create_model()
        assert any(
            "Term specs must have a Value key" in r.message for r in caplog.records
        )
        assert m.create_model_success is False

    def test_term_missing_origin(self, caplog):
        m = MDF(handle="test", ignore_enum_by_reference=True)
        m.files = [TEST_MODEL_FILE]
        m.load_yaml()
        m.mdf["Terms"] = {"ok_term": {"Value": "something"}}
        with caplog.at_level("WARNING"):
            m.create_model()
        assert any(
            "No Origin provided for term" in r.message for r in caplog.records
        )


class TestCreateEdges:
    """Tests for create_edges error/warning paths (lines 260-281)."""

    def test_edge_with_undefined_node(self, caplog):
        m = MDF(handle="test", ignore_enum_by_reference=True)
        m.files = [TEST_MODEL_FILE]
        m.load_yaml()
        m.mdf["Relationships"]["bad_edge"] = {
            "Mul": "one_to_one",
            "Props": None,
            "Ends": [{"Src": "nonexistent_node", "Dst": "case"}],
        }
        with caplog.at_level("WARNING"):
            with pytest.raises(KeyError):
                m.create_model()
        assert any(
            "No node" in r.message and "nonexistent_node" in r.message
            for r in caplog.records
        )

    def test_edge_with_no_multiplicity(self, caplog):
        m = MDF(handle="test", ignore_enum_by_reference=True)
        m.files = [TEST_MODEL_FILE]
        m.load_yaml()
        m.mdf["Relationships"]["no_mul_edge"] = {
            "Props": None,
            "Ends": [{"Src": "sample", "Dst": "case"}],
        }
        with caplog.at_level("WARNING"):
            m.create_model()
        assert any(
            "does not specify a multiplicity" in r.message for r in caplog.records
        )

    def test_edge_with_nonstandard_multiplicity(self, caplog):
        m = MDF(handle="test", ignore_enum_by_reference=True)
        m.files = [TEST_MODEL_FILE]
        m.load_yaml()
        m.mdf["Relationships"]["weird_mul_edge"] = {
            "Mul": "weird_mul",
            "Props": None,
            "Ends": [{"Src": "sample", "Dst": "case"}],
        }
        with caplog.at_level("WARNING"):
            m.create_model()
        assert any(
            "non-standard multiplicity" in r.message for r in caplog.records
        )


class TestCreateProps:
    """Tests for create_props error paths (lines 339, 360-364)."""

    def test_edge_with_duplicate_ends_pair(self, caplog):
        m = MDF(handle="test", ignore_enum_by_reference=True)
        m.files = [TEST_MODEL_FILE]
        m.load_yaml()
        m.mdf["Relationships"]["dup_ends"] = {
            "Mul": "one_to_one",
            "Props": ["days_to_sample"],
            "Ends": [
                {"Src": "sample", "Dst": "case"},
                {"Src": "sample", "Dst": "case"},
            ],
        }
        with caplog.at_level("WARNING"):
            m.create_model()
        assert any(
            "more than one Ends pair" in r.message for r in caplog.records
        )


class TestEnumReference:
    """Tests for enum reference error paths (lines 485-486, 527-532, 582-584, 607-609)."""

    def test_merge_enum_reference_no_ref(self, caplog):
        m = MDF(handle="test", ignore_enum_by_reference=True)
        m.files = [TEST_MODEL_FILE]
        m.load_yaml()
        m.create_model()
        from bento_meta.objects import Property, ValueSet

        prop = Property({"handle": "test_prop", "model": "test"})
        prop.value_set = ValueSet()
        prop.value_set.path = None
        prop.value_set.url = None
        with caplog.at_level("ERROR"):
            m.merge_enum_reference(prop)
        assert any("No enum reference" in r.message for r in caplog.records)

    def test_load_enum_reference_path_not_exists(self, caplog):
        m = MDF(handle="test", ignore_enum_by_reference=True)
        m.files = [TEST_MODEL_FILE]
        m.load_yaml()
        m.create_model()
        from bento_meta.objects import Property, ValueSet

        prop = Property({"handle": "test_prop", "model": "test"})
        prop.value_set = ValueSet()
        prop.value_set.path = "/nonexistent/path/enum.yml"
        prop.value_set.url = None
        with caplog.at_level("ERROR"):
            result = m.load_enum_reference(prop)
        assert result == {} or result is None
        assert any("does not exist" in r.message for r in caplog.records)



class TestLoadEnumByTermFromSts:
    """Tests for STS API paths (lines 551-576)."""

    def test_sts_term_missing_origin_fields(self, caplog):
        m = MDF(handle="test", ignore_enum_by_reference=True)
        m.files = [TEST_MODEL_FILE]
        m.load_yaml()
        m.create_model()
        from bento_meta.objects import Property, Term, ValueSet

        prop = Property({"handle": "test_prop", "model": "test"})
        prop.value_set = ValueSet()
        prop.value_set.path = None
        prop.value_set.url = None
        term = Term({"value": "Test Term"})
        term.origin_name = None
        term.origin_id = None
        term.origin_version = None
        prop.value_set.edp_terms["key"] = term
        with caplog.at_level("ERROR"):
            result = m.load_enum_reference(prop)
        assert result == []
        assert any("Cannot load enum from STS" in r.message for r in caplog.records)

    def test_sts_term_missing_origin_raises(self):
        m = MDF(handle="test", raise_error=True, ignore_enum_by_reference=True)
        m.files = [TEST_MODEL_FILE]
        m.load_yaml()
        m.create_model()
        from bento_meta.objects import Property, Term, ValueSet

        prop = Property({"handle": "test_prop", "model": "test"})
        prop.value_set = ValueSet()
        prop.value_set.path = None
        prop.value_set.url = None
        term = Term({"value": "Test Term"})
        term.origin_name = None
        term.origin_id = None
        term.origin_version = None
        prop.value_set.edp_terms["key"] = term
        with pytest.raises(ArgError, match="Cannot load enum from STS"):
            m.load_enum_reference(prop)

    def test_sts_api_request_failure(self, caplog):
        m = MDF(handle="test", ignore_enum_by_reference=True)
        m.files = [TEST_MODEL_FILE]
        m.load_yaml()
        m.create_model()
        from bento_meta.objects import Property, Term, ValueSet

        prop = Property({"handle": "test_prop", "model": "test"})
        prop.value_set = ValueSet()
        prop.value_set.path = None
        prop.value_set.url = None
        term = Term({"value": "Test Term"})
        term.origin_name = "caDSR"
        term.origin_id = "999999"
        term.origin_version = "1.0"
        prop.value_set.edp_terms["key"] = term
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                "http://localhost:8000/v2/edp/caDSR/999999/1.0/terms",
                body=responses.ConnectionError("connection refused"),
            )
            with caplog.at_level("ERROR"):
                result = m.load_enum_reference(prop)
        assert result is None or result == []
        assert any("STS API call" in r.message for r in caplog.records)



class TestAnnotateEntityFromMdf:
    """Tests for annotate_entity_from_mdf error paths (lines 646-658)."""

    def test_term_spec_missing_value(self, caplog):
        m = MDF(handle="test", ignore_enum_by_reference=True)
        m.files = [TEST_MODEL_FILE]
        m.load_yaml()
        m.create_model()
        node = m.model.nodes["case"]
        with caplog.at_level("ERROR"):
            m.annotate_entity_from_mdf(node, [{"Origin": "test"}])
        assert any(
            "Term specs must have a Value key" in r.message for r in caplog.records
        )
        assert m.create_model_success is False

    def test_term_spec_missing_origin_defaults_to_handle(self, caplog):
        m = MDF(handle="test", ignore_enum_by_reference=True)
        m.files = [TEST_MODEL_FILE]
        m.load_yaml()
        m.create_model()
        node = m.model.nodes["sample"]
        spec = [{"Value": "new_annotation"}]
        with caplog.at_level("WARNING"):
            m.annotate_entity_from_mdf(node, spec)
        assert any(
            "No Origin provided for Term annotation" in r.message
            for r in caplog.records
        )
        assert spec[0]["Origin"] == "test"


class TestResolveCompositeKeyProps:
    """Tests for resolve_composite_key_props error paths (lines 697-727)."""

    def test_nonexistent_key_prop_on_own_node(self, caplog):
        m = MDF(handle="test", ignore_enum_by_reference=True)
        m.files = [TEST_MODEL_FILE]
        m.load_yaml()
        m.create_model()
        node = m.model.nodes["case"]
        node.composite_key_props = ["nonexistent_prop"]
        with caplog.at_level("ERROR"):
            m.resolve_composite_key_props()
        assert any(
            "Composite key property" in r.message and "does not exist" in r.message
            for r in caplog.records
        )
        assert m.create_model_success is False

    def test_composite_key_references_nonexistent_node(self, caplog):
        m = MDF(handle="test", ignore_enum_by_reference=True)
        m.files = [TEST_MODEL_FILE]
        m.load_yaml()
        m.create_model()
        node = m.model.nodes["case"]
        node.composite_key_props = ["ghost_node.some_prop"]
        with caplog.at_level("ERROR"):
            m.resolve_composite_key_props()
        assert any(
            "nonexistent node" in r.message and "ghost_node" in r.message
            for r in caplog.records
        )
        assert m.create_model_success is False

    def test_composite_key_prop_not_in_referent_node(self, caplog):
        m = MDF(handle="test", ignore_enum_by_reference=True)
        m.files = [TEST_MODEL_FILE]
        m.load_yaml()
        m.create_model()
        node = m.model.nodes["case"]
        node.composite_key_props = ["sample.nonexistent_prop"]
        with caplog.at_level("ERROR"):
            m.resolve_composite_key_props()
        assert any(
            "does not exist in referent node" in r.message for r in caplog.records
        )
        assert m.create_model_success is False


class TestLookupTermByHandle:
    """Tests for lookup_term_by_handle warning path (line 635)."""

    def test_multiple_terms_same_handle_warns(self, caplog):
        m = MDF(handle="test", ignore_enum_by_reference=True)
        m.files = [TEST_MODEL_FILE]
        m.load_yaml()
        m.create_model()
        from bento_meta.objects import Term

        m._terms[("dup", "origin_a", None, None)] = Term({"value": "dup_a"})
        m._terms[("dup", "origin_b", None, None)] = Term({"value": "dup_b"})
        with caplog.at_level("WARNING"):
            result = m.lookup_term_by_handle("dup")
        assert result is not None
        assert any("Multiple terms found" in r.message for r in caplog.records)
