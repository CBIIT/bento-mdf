"""Tests for bento_mdf.diff."""

import re
from pathlib import Path

from bento_mdf.diff import Diff, diff_models
from bento_mdf.mdf import MDF
from bento_meta.objects import Property, Term, ValueSet

# constants
TDIR = Path(__file__).resolve().parent
TEST_HANDLE = "test"
TEST_MODEL_A = MDF(TDIR / "samples" / "test-model-a.yml", handle=TEST_HANDLE)
TEST_MODEL_B = MDF(TDIR / "samples" / "test-model-b.yml", handle=TEST_HANDLE)
TEST_MODEL_C = MDF(TDIR / "samples" / "test-model-c.yml", handle=TEST_HANDLE)
TEST_MODEL_D = MDF(TDIR / "samples" / "test-model-d.yml", handle=TEST_HANDLE)
TEST_MODEL_E = MDF(TDIR / "samples" / "test-model-e.yml", handle=TEST_HANDLE)
TEST_MODEL_F = MDF(TDIR / "samples" / "test-model-f.yml", handle=TEST_HANDLE)
TEST_MODEL_G = MDF(TDIR / "samples" / "test-model-g.yml", handle=TEST_HANDLE)
TEST_MODEL_H = MDF(TDIR / "samples" / "test-model-h.yml", handle=TEST_HANDLE)
TEST_MODEL_I = MDF(TDIR / "samples" / "test-model-i.yml", handle=TEST_HANDLE)
TEST_MODEL_TERMS_A = MDF(
    TDIR / "samples" / "test-model-with-terms-a.yml",
    handle=TEST_HANDLE,
)
TEST_MODEL_TERMS_B = MDF(
    TDIR / "samples" / "test-model-with-terms-b.yml",
    handle=TEST_HANDLE,
)
TEST_MODEL_TERMS_C = MDF(
    TDIR / "samples" / "test-model-with-terms-c.yml",
    handle=TEST_HANDLE,
)


# tests for other changes
class TestDiffs:
    """Tests for various changes between models"""

    def test_diff_of_same_yaml(self):
        """Diff of a yml against a copy of itself better darn be empty."""
        actual = diff_models(
            TEST_MODEL_A.model,
            TEST_MODEL_A.model,
            objects_as_dicts=True,
        )
        expected = {}
        assert actual == expected

    def test_diff_of_extra_node_properties_and_terms(self):
        """a_b"""
        actual = diff_models(
            TEST_MODEL_A.model,
            TEST_MODEL_B.model,
            objects_as_dicts=True,
        )

        expected = {
            "nodes": {
                "added": None,
                "changed": {
                    "file": {
                        "props": {
                            "added": {
                                "encryption_type": {
                                    "handle": "encryption_type",
                                    "model": "test",
                                    "value_domain": "value_set",
                                },
                            },
                            "removed": None,
                        },
                    },
                },
                "removed": None,
            },
            "props": {
                "changed": {
                    ("sample", "sample_type"): {
                        "value_set": {
                            "removed": None,
                            "added": {
                                "not a tumor": {
                                    "handle": "not a tumor",
                                    "value": "not a tumor",
                                    "origin_name": "test",
                                },
                            },
                        },
                    },
                },
                "removed": None,
                "added": {
                    ("file", "encryption_type"): {
                        "handle": "encryption_type",
                        "model": "test",
                        "value_domain": "value_set",
                    },
                },
            },
            "terms": {
                "removed": None,
                "added": {
                    ("password", "test"): {
                        "value": "password",
                        "origin_name": "test",
                        "handle": "password",
                    },
                    ("not a tumor", "test"): {
                        "value": "not a tumor",
                        "origin_name": "test",
                        "handle": "not a tumor",
                    },
                    ("certificate", "test"): {
                        "value": "certificate",
                        "origin_name": "test",
                        "handle": "certificate",
                    },
                },
            },
        }
        assert actual == expected

    def test_diff_of_extra_node_property(self):
        """a_d"""
        actual = diff_models(
            TEST_MODEL_A.model,
            TEST_MODEL_D.model,
            objects_as_dicts=True,
        )
        expected = {
            "nodes": {
                "changed": {
                    "diagnosis": {
                        "props": {
                            "removed": None,
                            "added": {
                                "fatal": {
                                    "handle": "fatal",
                                    "model": "test",
                                    "value_domain": "value_set",
                                },
                            },
                        },
                    },
                },
                "removed": None,
                "added": None,
            },
            "props": {
                "removed": None,
                "added": {
                    ("diagnosis", "fatal"): {
                        "handle": "fatal",
                        "model": "test",
                        "value_domain": "value_set",
                    },
                },
            },
            "terms": {
                "removed": None,
                "added": {
                    ("non-fatal", "test"): {
                        "value": "non-fatal",
                        "origin_name": "test",
                        "handle": "non-fatal",
                    },
                    ("fatal", "test"): {
                        "value": "fatal",
                        "origin_name": "test",
                        "handle": "fatal",
                    },
                    ("unknown", "test"): {
                        "value": "unknown",
                        "origin_name": "test",
                        "handle": "unknown",
                    },
                },
            },
        }
        assert actual == expected

    def test_diff_of_extra_node_edge_and_property(self):
        """a_e"""
        actual = diff_models(
            TEST_MODEL_A.model,
            TEST_MODEL_E.model,
            objects_as_dicts=True,
        )
        expected = {
            "nodes": {
                "removed": None,
                "added": {"outcome": {"handle": "outcome", "model": "test"}},
            },
            "edges": {
                "removed": None,
                "added": {
                    ("end_result", "diagnosis", "outcome"): {
                        "handle": "end_result",
                        "model": "test",
                        "multiplicity": "many_to_one",
                    },
                },
            },
            "props": {
                "removed": None,
                "added": {
                    ("outcome", "fatal"): {
                        "handle": "fatal",
                        "model": "test",
                        "value_domain": "value_set",
                    },
                },
            },
            "terms": {
                "removed": None,
                "added": {
                    ("non-fatal", "test"): {
                        "value": "non-fatal",
                        "origin_name": "test",
                        "handle": "non-fatal",
                    },
                    ("unknown", "test"): {
                        "value": "unknown",
                        "origin_name": "test",
                        "handle": "unknown",
                    },
                    ("fatal", "test"): {
                        "value": "fatal",
                        "origin_name": "test",
                        "handle": "fatal",
                    },
                },
            },
        }
        assert actual == expected

    def test_diff_of_extra_node(self):
        """a_f"""
        actual = diff_models(
            TEST_MODEL_A.model,
            TEST_MODEL_F.model,
            objects_as_dicts=True,
        )
        expected = {
            "nodes": {
                "removed": {"diagnosis": {"handle": "diagnosis", "model": "test"}},
                "added": None,
            },
            "edges": {
                "removed": {
                    ("of_case", "diagnosis", "case"): {
                        "handle": "of_case",
                        "model": "test",
                        "multiplicity": "one_to_one",
                    },
                },
                "added": None,
            },
            "props": {
                "removed": {
                    ("diagnosis", "disease"): {
                        "handle": "disease",
                        "model": "test",
                        "value_domain": "url",
                    },
                },
                "added": None,
            },
        }
        assert actual == expected

    def test_diff_of_missing_node(self):
        """a_g"""
        actual = diff_models(
            TEST_MODEL_A.model,
            TEST_MODEL_G.model,
            objects_as_dicts=True,
        )
        expected = {
            "nodes": {
                "removed": None,
                "added": {"outcome": {"handle": "outcome", "model": "test"}},
            },
            "props": {
                "removed": None,
                "added": {
                    ("outcome", "disease"): {
                        "handle": "disease",
                        "model": "test",
                        "value_domain": "url",
                    },
                },
            },
        }
        assert actual == expected

    def test_diff_of_swapped_nodeprops(self):
        """a_h"""
        actual = diff_models(
            TEST_MODEL_A.model,
            TEST_MODEL_H.model,
            objects_as_dicts=True,
        )
        expected = {
            "nodes": {
                "changed": {
                    "diagnosis": {
                        "props": {
                            "removed": {
                                "disease": {
                                    "handle": "disease",
                                    "model": "test",
                                    "value_domain": "url",
                                },
                            },
                            "added": {
                                "file_size": {
                                    "handle": "file_size",
                                    "model": "test",
                                    "value_domain": "integer",
                                    "units": "Gb;Mb",
                                },
                                "file_name": {
                                    "handle": "file_name",
                                    "model": "test",
                                    "value_domain": "string",
                                },
                                "md5sum": {
                                    "handle": "md5sum",
                                    "model": "test",
                                    "value_domain": "regexp",
                                    "pattern": "^[a-f0-9]{40}",
                                },
                            },
                        },
                    },
                    "file": {
                        "props": {
                            "removed": {
                                "file_size": {
                                    "handle": "file_size",
                                    "model": "test",
                                    "value_domain": "integer",
                                    "units": "Gb;Mb",
                                },
                                "file_name": {
                                    "handle": "file_name",
                                    "model": "test",
                                    "value_domain": "string",
                                },
                                "md5sum": {
                                    "handle": "md5sum",
                                    "model": "test",
                                    "value_domain": "regexp",
                                    "pattern": "^[a-f0-9]{40}",
                                },
                            },
                            "added": {
                                "disease": {
                                    "handle": "disease",
                                    "model": "test",
                                    "value_domain": "url",
                                },
                            },
                        },
                    },
                },
                "added": None,
                "removed": None,
            },
            "props": {
                "removed": {
                    ("file", "file_name"): {
                        "handle": "file_name",
                        "model": "test",
                        "value_domain": "string",
                    },
                    ("diagnosis", "disease"): {
                        "handle": "disease",
                        "model": "test",
                        "value_domain": "url",
                    },
                    ("file", "file_size"): {
                        "handle": "file_size",
                        "model": "test",
                        "value_domain": "integer",
                        "units": "Gb;Mb",
                    },
                    ("file", "md5sum"): {
                        "handle": "md5sum",
                        "model": "test",
                        "value_domain": "regexp",
                        "pattern": "^[a-f0-9]{40}",
                    },
                },
                "added": {
                    ("diagnosis", "file_size"): {
                        "handle": "file_size",
                        "model": "test",
                        "value_domain": "integer",
                        "units": "Gb;Mb",
                    },
                    ("diagnosis", "file_name"): {
                        "handle": "file_name",
                        "model": "test",
                        "value_domain": "string",
                    },
                    ("file", "disease"): {
                        "handle": "disease",
                        "model": "test",
                        "value_domain": "url",
                    },
                    ("diagnosis", "md5sum"): {
                        "handle": "md5sum",
                        "model": "test",
                        "value_domain": "regexp",
                        "pattern": "^[a-f0-9]{40}",
                    },
                },
            },
        }
        assert actual == expected

    def test_diff_where_yaml_has_extra_term(self):
        """c_d"""
        actual = diff_models(
            TEST_MODEL_C.model,
            TEST_MODEL_D.model,
            objects_as_dicts=True,
        )
        expected = {
            "props": {
                "changed": {
                    ("diagnosis", "fatal"): {
                        "value_set": {
                            "removed": None,
                            "added": {
                                "unknown": {
                                    "value": "unknown",
                                    "origin_name": "test",
                                    "handle": "unknown",
                                },
                            },
                        },
                    },
                },
                "added": None,
                "removed": None,
            },
            "terms": {
                "removed": None,
                "added": {
                    ("unknown", "test"): {
                        "value": "unknown",
                        "origin_name": "test",
                        "handle": "unknown",
                    },
                },
            },
        }
        assert actual == expected

    def test_diff_of_assorted_changes(self):
        """d_e"""
        actual = diff_models(
            TEST_MODEL_D.model,
            TEST_MODEL_E.model,
            objects_as_dicts=True,
        )
        expected = {
            "nodes": {
                "changed": {
                    "diagnosis": {
                        "props": {
                            "removed": {
                                "fatal": {
                                    "handle": "fatal",
                                    "model": "test",
                                    "value_domain": "value_set",
                                },
                            },
                            "added": None,
                        },
                    },
                },
                "removed": None,
                "added": {"outcome": {"handle": "outcome", "model": "test"}},
            },
            "edges": {
                "removed": None,
                "added": {
                    ("end_result", "diagnosis", "outcome"): {
                        "handle": "end_result",
                        "model": "test",
                        "multiplicity": "many_to_one",
                    },
                },
            },
            "props": {
                "removed": {
                    ("diagnosis", "fatal"): {
                        "handle": "fatal",
                        "model": "test",
                        "value_domain": "value_set",
                    },
                },
                "added": {
                    ("outcome", "fatal"): {
                        "handle": "fatal",
                        "model": "test",
                        "value_domain": "value_set",
                    },
                },
            },
        }
        assert actual == expected


class TestDiffSummaries:
    """Tests for summaries of various changes between models."""

    def sort_summary_terms(self, summary_string: str) -> str:
        """Organize terms in summary string for testing."""
        lines = summary_string.split("\n")

        term_lines = [
            line
            for line in lines
            if re.match(r"-\s*(Added|Removed|Changed)\s*term:", line)
        ]
        term_lines.sort(key=lambda x: re.search(r"term:\s*'([^']*)'", x).group(1))

        sorted_lines = []
        term_line_index = 0
        for line in lines:
            if re.match(r"-\s*(Added|Removed|Changed)\s*term:", line):
                sorted_lines.append(term_lines[term_line_index])
                term_line_index += 1
            else:
                sorted_lines.append(line)

        return "\n".join(sorted_lines)

    def test_diff_of_assorted_changes_summary(self) -> None:
        """d_e summary only."""
        actual = diff_models(
            TEST_MODEL_D.model,
            TEST_MODEL_E.model,
            objects_as_dicts=True,
            include_summary=True,
        )
        actual_summary = actual["summary"]
        expected_summary = (
            "1 node(s) added; "
            "1 edge(s) added; "
            "1 prop(s) removed; "
            "1 prop(s) added; "
            "1 attribute(s) changed for 1 node(s)\n"
            "- Added node: 'outcome'\n"
            "- Added edge: 'end_result' with src: 'diagnosis' and dst: 'outcome'\n"
            "- Removed prop: 'fatal' with parent: 'diagnosis'\n"
            "- Added prop: 'fatal' with parent: 'outcome'"
        )
        assert actual_summary == expected_summary

    def test_diff_of_extra_node_property_summary(self):
        """a_d summary only"""
        actual = diff_models(
            TEST_MODEL_A.model,
            TEST_MODEL_D.model,
            objects_as_dicts=True,
            include_summary=True,
        )
        actual_summary = actual["summary"]
        actual_summary_sorted = self.sort_summary_terms(actual_summary)
        expected_summary = (
            "1 prop(s) added; "
            "3 term(s) added; "
            "1 attribute(s) changed for 1 node(s)\n"
            "- Added prop: 'fatal' with parent: 'diagnosis'\n"
            "- Added term: 'fatal' with origin: 'test'\n"
            "- Added term: 'non-fatal' with origin: 'test'\n"
            "- Added term: 'unknown' with origin: 'test'"
        )
        assert actual_summary_sorted == expected_summary

    def test_diff_of_multiple_attr_changes_summary(self):
        """a_i summary only"""
        actual = diff_models(
            TEST_MODEL_A.model,
            TEST_MODEL_I.model,
            objects_as_dicts=True,
            include_summary=True,
        )
        actual_summary = actual["summary"]
        actual_summary_sorted = self.sort_summary_terms(actual_summary)
        expected_summary = "7 attribute(s) changed for 3 prop(s)\n"
        assert actual_summary_sorted == expected_summary

    def test_diff_summary_term_annotation(self) -> None:
        """Test change in term annotation for a property."""
        actual = diff_models(
            TEST_MODEL_TERMS_A.model,
            TEST_MODEL_TERMS_B.model,
            objects_as_dicts=True,
            include_summary=True,
        )
        actual_summary = actual["summary"]
        actual_summary_sorted = self.sort_summary_terms(actual_summary)
        expected_summary = (
            "1 term(s) removed; "
            "2 term(s) added; "
            "1 attribute(s) changed for 1 node(s); "
            "1 attribute(s) changed for 1 prop(s); "
            "4 attribute(s) changed for 3 term(s)\n"
            "- Changed term: 'case_id' with origin: 'CTDC' "
            "which annotates prop: 'case_id' with parent: 'case'. "
            "Attribute: 'origin_id' updated from 'None' to '123'\n"
            "- Removed term: 'case_term' with origin: 'CTDC' "
            "which annotates node: 'case'\n"
            "- Added term: 'case_term' with origin: 'CDS' "
            "which annotates node: 'case'\n"
            "- Changed term: 'of_case_term' with origin: 'CTDC' "
            "which annotates edge: 'of_case' with src: 'sample' and dst: 'case'. "
            "Attribute: 'origin_id' updated from 'None' to '596'. "
            "Attribute: 'origin_version' updated from 'None' to 'v2.0'\n"
            "- Added term: 'patient_id' with origin: 'caDSR' "
            "which annotates prop: 'patient_id' with parent: 'case'\n"
            "- Changed term: 'subject' with origin: 'caDSR' "
            "which annotates node: 'case'. "
            "Attribute: 'origin_id' updated from 'None' to '42'"
        )
        assert actual_summary_sorted == expected_summary

    def test_diff_summary_new_ent_term_annotation(self) -> None:
        """Test addition of new entity that has a term annotation."""
        actual = diff_models(
            TEST_MODEL_TERMS_A.model,
            TEST_MODEL_TERMS_C.model,
            objects_as_dicts=True,
            include_summary=True,
        )
        actual_summary = actual["summary"]
        actual_summary_sorted = self.sort_summary_terms(actual_summary)
        expected_summary = (
            "1 prop(s) added; 2 term(s) added; 1 attribute(s) changed for 1 node(s)\n"
            "- Added prop: 'sample_id' with parent: 'sample'. "
            "Property annotated by: 'sample_id' with origin 'caDSR', "
            "'sample_num' with origin 'ACOTAR'\n"
            "- Added term: 'sample_id' with origin: 'caDSR'\n"
            "- Added term: 'sample_num' with origin: 'ACOTAR'"
        )
        assert actual_summary_sorted == expected_summary


class TestValueSets:
    """Test value_sets_are_different method."""

    diff = Diff()
    term_a = Term({"value": "Merida"})
    term_b = Term({"value": "Cumana"})
    term_c = Term({"value": "Maracaibo"})
    term_d = Term({"value": "Ciudad Bolivar"})
    term_e = Term({"value": "Barcelona"})
    term_f = Term({"value": "Barquisimeto"})
    vs_1 = ValueSet({"_id": "1"})
    vs_2 = ValueSet({"_id": "2"})
    p_1 = Property({"handle": "States"})
    p_2 = Property({"handle": "Estados"})

    def test_identical_value_sets_are_not_different(self) -> None:
        """Test value_sets_are_different for value sets with same terms."""
        vs_1, vs_2 = self.vs_1, self.vs_2
        vs_1.terms, vs_2.terms = {}, {}

        vs_1.terms["Merida"] = self.term_a
        vs_1.terms["Cumana"] = self.term_b
        vs_1.terms["Maracaibo"] = self.term_c
        vs_1.terms["Ciudad Bolivar"] = self.term_d

        vs_2.terms["Merida"] = self.term_a
        vs_2.terms["Cumana"] = self.term_b
        vs_2.terms["Maracaibo"] = self.term_c
        vs_2.terms["Ciudad Bolivar"] = self.term_d

        actual = self.diff.valuesets_are_different(vs_1, vs_2)
        expected = False
        assert actual == expected

    def test_value_set_with_removed_term_is_different(self) -> None:
        """Test value_sets_are_different when first value_set has extra term."""
        vs_1, vs_2 = self.vs_1, self.vs_2
        vs_1.terms, vs_2.terms = {}, {}

        vs_1.terms["Merida"] = self.term_a
        vs_1.terms["Cumana"] = self.term_b
        vs_1.terms["Maracaibo"] = self.term_c
        vs_1.terms["Ciudad Bolivar"] = self.term_d

        vs_2.terms["Merida"] = self.term_a
        vs_2.terms["Cumana"] = self.term_b
        vs_2.terms["Maracaibo"] = self.term_c

        actual = self.diff.valuesets_are_different(vs_1, vs_2)
        expected = True
        assert actual == expected

    def test_value_set_with_added_term_is_different(self) -> None:
        """Test value_sets_are_different when second value_set has extra term."""
        vs_1, vs_2 = self.vs_1, self.vs_2
        vs_1.terms, vs_2.terms = {}, {}

        vs_1.terms["Merida"] = self.term_a
        vs_1.terms["Cumana"] = self.term_b
        vs_1.terms["Maracaibo"] = self.term_c
        vs_1.terms["Ciudad Bolivar"] = self.term_d

        vs_2.terms["Merida"] = self.term_a
        vs_2.terms["Cumana"] = self.term_b
        vs_2.terms["Maracaibo"] = self.term_c
        vs_2.terms["Ciudad Bolivar"] = self.term_d
        vs_2.terms["Barcelona"] = self.term_e

        actual = self.diff.valuesets_are_different(vs_1, vs_2)
        expected = True
        assert actual == expected

    def test_empty_value_sets_are_not_different(self) -> None:
        """Test value_sets_are_different for empty value sets."""
        vs_1, vs_2 = self.vs_1, self.vs_2
        vs_1.terms, vs_2.terms = {}, {}

        actual = self.diff.valuesets_are_different(vs_1, vs_2)
        expected = False
        assert actual == expected

    def test_value_set_not_different_from_self(self) -> None:
        """Test value_sets_are_different when value set compared to itself."""
        vs_1 = self.vs_1
        vs_1.terms = {}

        vs_1.terms["Merida"] = self.term_a
        vs_1.terms["Cumana"] = self.term_b
        vs_1.terms["Maracaibo"] = self.term_c
        vs_1.terms["Ciudad Bolivar"] = self.term_d

        actual = self.diff.valuesets_are_different(vs_1, vs_1)
        expected = False
        assert actual == expected

    def test_identical_prop_value_sets_are_not_different(self) -> None:
        """Test value_sets_are_different for properties with identical value sets."""
        p_1, p_2 = self.p_1, self.p_2
        vs_1, vs_2 = self.vs_1, self.vs_2
        vs_1.terms, vs_2.terms = {}, {}

        vs_1.terms["Merida"] = self.term_a
        vs_1.terms["Cumana"] = self.term_b
        vs_1.terms["Maracaibo"] = self.term_c
        vs_1.terms["Ciudad Bolivar"] = self.term_d

        vs_2.terms["Merida"] = self.term_a
        vs_2.terms["Cumana"] = self.term_b
        vs_2.terms["Maracaibo"] = self.term_c
        vs_2.terms["Ciudad Bolivar"] = self.term_d

        p_1.value_set = vs_1
        p_2.value_set = vs_2

        actual = self.diff.valuesets_are_different(p_1.value_set, p_2.value_set)
        expected = False
        assert actual == expected
