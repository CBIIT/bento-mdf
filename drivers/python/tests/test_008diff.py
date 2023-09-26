"""
Tests for bento_mdf.diff
"""
import os
import sys

from bento_mdf.diff import Diff, diff_models
from bento_mdf.mdf import MDF
from bento_meta.objects import Property, Term, ValueSet

sys.path.insert(0, ".")
sys.path.insert(0, "..")
TDIR = "tests/" if os.path.exists("tests") else ""


def sort_nested_lists(dict_with_lists: dict) -> None:
    """helper function to sort any lists found in a nested dict"""
    for value in dict_with_lists.values():
        if isinstance(value, dict):
            sort_nested_lists(value)
        elif isinstance(value, list):
            value.sort()


def test_diff_of_same_yaml():
    """diff of a yml against a copy of itself better darn be empty"""
    a = MDF(TDIR + "samples/test-model-a.yml", handle="test")
    b = MDF(TDIR + "samples/test-model-a.yml", handle="test")
    actual = diff_models(a.model, b.model, objects_as_dicts=True)
    expected = {}
    assert actual == expected


def test_diff_of_extra_node_properties_and_terms():
    """a_b"""
    a = MDF(TDIR + "samples/test-model-a.yml", handle="test")
    b = MDF(TDIR + "samples/test-model-b.yml", handle="test")
    actual = diff_models(a.model, b.model, objects_as_dicts=True)

    expected = {
        "nodes": {
            "added": None,
            "file": {"props": {"added": ["encryption_type"], "removed": None}},
            "removed": None,
        },
        "props": {
            ("sample", "sample_type"): {
                "value_set": {"removed": None, "added": ["not a tumor"]}
            },
            "removed": None,
            "added": {
                ("file", "encryption_type"): {
                    "handle": "encryption_type",
                    "model": "test",
                    "value_domain": "value_set",
                }
            },
        },
    }
    assert actual == expected


def test_diff_of_extra_node_property():
    """a_d"""
    a = MDF(TDIR + "samples/test-model-a.yml", handle="test")
    b = MDF(TDIR + "samples/test-model-d.yml", handle="test")
    actual = diff_models(a.model, b.model, objects_as_dicts=True)
    expected = {
        "nodes": {
            "diagnosis": {"props": {"removed": None, "added": ["fatal"]}},
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
                }
            },
        },
    }
    assert actual == expected


def test_diff_of_extra_node_edge_and_property():
    """a_e"""
    a = MDF(TDIR + "samples/test-model-a.yml", handle="test")
    b = MDF(TDIR + "samples/test-model-e.yml", handle="test")
    actual = diff_models(a.model, b.model, objects_as_dicts=True)
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
                }
            },
        },
        "props": {
            "removed": None,
            "added": {
                ("outcome", "fatal"): {
                    "handle": "fatal",
                    "model": "test",
                    "value_domain": "value_set",
                }
            },
        },
    }
    assert actual == expected


def test_diff_of_extra_node():
    """a_f"""
    a = MDF(TDIR + "samples/test-model-a.yml", handle="test")
    b = MDF(TDIR + "samples/test-model-f.yml", handle="test")
    actual = diff_models(a.model, b.model, objects_as_dicts=True)
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
                }
            },
            "added": None,
        },
        "props": {
            "removed": {
                ("diagnosis", "disease"): {
                    "handle": "disease",
                    "model": "test",
                    "value_domain": "url",
                }
            },
            "added": None,
        },
    }
    assert actual == expected


def test_diff_of_missing_node():
    """a_g"""
    a = MDF(TDIR + "samples/test-model-a.yml", handle="test")
    b = MDF(TDIR + "samples/test-model-g.yml", handle="test")
    actual = diff_models(a.model, b.model, objects_as_dicts=True)
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
                }
            },
        },
    }
    assert actual == expected


def test_diff_of_swapped_nodeprops():
    """a_h"""
    a = MDF(TDIR + "samples/test-model-a.yml", handle="test")
    b = MDF(TDIR + "samples/test-model-h.yml", handle="test")
    actual = diff_models(a.model, b.model, objects_as_dicts=True)
    sort_nested_lists(actual)
    expected = {
        "nodes": {
            "diagnosis": {
                "props": {
                    "removed": ["disease"],
                    "added": ["file_name", "file_size", "md5sum"],
                }
            },
            "file": {
                "props": {
                    "removed": ["file_name", "file_size", "md5sum"],
                    "added": ["disease"],
                }
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


def test_diff_where_yaml_has_extra_term():
    """c_d"""
    a = MDF(TDIR + "samples/test-model-c.yml", handle="test")
    b = MDF(TDIR + "samples/test-model-d.yml", handle="test")
    actual = diff_models(a.model, b.model, objects_as_dicts=True)
    expected = {
        "props": {
            ("diagnosis", "fatal"): {
                "value_set": {"removed": None, "added": ["unknown"]}
            },
            "added": None,
            "removed": None,
        }
    }
    assert actual == expected


def test_diff_of_assorted_changes():
    """d_e"""
    a = MDF(TDIR + "samples/test-model-d.yml", handle="test")
    b = MDF(TDIR + "samples/test-model-e.yml", handle="test")
    actual = diff_models(a.model, b.model, objects_as_dicts=True)
    expected = {
        "nodes": {
            "diagnosis": {"props": {"removed": ["fatal"], "added": None}},
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
                }
            },
        },
        "props": {
            "removed": {
                ("diagnosis", "fatal"): {
                    "handle": "fatal",
                    "model": "test",
                    "value_domain": "value_set",
                }
            },
            "added": {
                ("outcome", "fatal"): {
                    "handle": "fatal",
                    "model": "test",
                    "value_domain": "value_set",
                }
            },
        },
    }
    assert actual == expected


def test_diff_of_assorted_changes_summary():
    """d_e summary only"""
    a = MDF(TDIR + "samples/test-model-d.yml", handle="test")
    b = MDF(TDIR + "samples/test-model-e.yml", handle="test")
    actual = diff_models(a.model, b.model, objects_as_dicts=True, include_summary=True)
    actual_summary = actual["summary"]
    expected_summary = (
        "1 node(s) added; "
        "1 edge(s) added; "
        "1 prop(s) removed; "
        "1 prop(s) added; "
        "1 node attribute(s) changed\n"
    )
    assert actual_summary == expected_summary


diff = Diff()
term_a = Term({"value": "Merida"})
term_b = Term({"value": "Cumana"})
term_c = Term({"value": "Maracaibo"})
term_d = Term({"value": "Ciudad Bolivar"})
term_e = Term({"value": "Barcelona"})
term_f = Term({"value": "Barquisimeto"})


def test_valuesets_are_different__a():
    """test using sets as input"""

    vs_1 = ValueSet({"_id": "1"})
    vs_2 = ValueSet({"_id": "2"})

    vs_1.terms["Merida"] = term_a
    vs_1.terms["Cumana"] = term_b
    vs_1.terms["Maracaibo"] = term_c
    vs_1.terms["Ciudad Bolivar"] = term_d

    vs_2.terms["Merida"] = term_a
    vs_2.terms["Cumana"] = term_b
    vs_2.terms["Maracaibo"] = term_c
    vs_2.terms["Ciudad Bolivar"] = term_d

    actual = diff.valuesets_are_different(vs_1, vs_2)
    expected = False
    assert actual == expected


def test_valuesets_are_different__b():
    """test using sets as input"""

    vs_1 = ValueSet({"_id": "1"})
    vs_2 = ValueSet({"_id": "2"})

    vs_1.terms["Merida"] = term_a
    vs_1.terms["Cumana"] = term_b
    vs_1.terms["Maracaibo"] = term_c
    vs_1.terms["Ciudad Bolivar"] = term_d

    vs_2.terms["Merida"] = term_a
    vs_2.terms["Cumana"] = term_b
    vs_2.terms["Maracaibo"] = term_c

    actual = diff.valuesets_are_different(vs_1, vs_2)
    expected = True
    assert actual == expected


def test_valuesets_are_different__c():
    """test using sets as input"""

    vs_1 = ValueSet({"_id": "1"})
    vs_2 = ValueSet({"_id": "2"})

    vs_1.terms["Merida"] = term_a
    vs_1.terms["Cumana"] = term_b
    vs_1.terms["Maracaibo"] = term_c
    vs_1.terms["Ciudad Bolivar"] = term_d

    vs_2.terms["Merida"] = term_a
    vs_2.terms["Cumana"] = term_b
    vs_2.terms["Maracaibo"] = term_c
    vs_2.terms["Ciudad Bolivar"] = term_d
    vs_2.terms["Barcelona"] = term_e

    actual = diff.valuesets_are_different(vs_1, vs_2)
    expected = True
    assert actual == expected


def test_valuesets_are_different__d():
    """test using sets as input"""

    vs_1 = ValueSet({"_id": "1"})
    vs_2 = ValueSet({"_id": "2"})

    actual = diff.valuesets_are_different(vs_1, vs_2)
    expected = False
    assert actual == expected


def test_valuesets_are_different__e():
    """test using sets as input"""

    vs_1 = ValueSet({"_id": "1"})

    vs_1.terms["Merida"] = term_a
    vs_1.terms["Cumana"] = term_b
    vs_1.terms["Maracaibo"] = term_c
    vs_1.terms["Ciudad Bolivar"] = term_d

    actual = diff.valuesets_are_different(vs_1, vs_1)
    expected = False
    assert actual == expected


def test_valuesets_are_different__f():
    """test using sets as input"""
    p_1 = Property({"handle": "States"})
    p_2 = Property({"handle": "Estados"})
    vs_1 = ValueSet({"_id": "1"})
    vs_2 = ValueSet({"_id": "2"})

    term_a = Term({"value": "Merida"})
    term_b = Term({"value": "Cumana"})
    term_c = Term({"value": "Maracaibo"})
    term_d = Term({"value": "Ciudad Bolivar"})
    term_e = Term({"value": "Barcelona"})
    term_f = Term({"value": "Barquisimeto"})

    vs_1.terms["Merida"] = term_a
    vs_1.terms["Cumana"] = term_b
    vs_1.terms["Maracaibo"] = term_c
    vs_1.terms["Ciudad Bolivar"] = term_d

    vs_2.terms["Merida"] = term_a
    vs_2.terms["Cumana"] = term_b
    vs_2.terms["Maracaibo"] = term_c
    vs_2.terms["Ciudad Bolivar"] = term_d

    p_1.value_set = vs_1
    p_2.value_set = vs_2

    actual = diff.valuesets_are_different(p_1.value_set, p_2.value_set)
    expected = False
    assert actual == expected
