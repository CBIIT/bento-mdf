"""
Tests for diff.py module
"""
import os
import sys

from bento_mdf.diff import Diff, diff_models
from bento_mdf.mdf import MDF
from bento_meta.objects import Property, Term, ValueSet

sys.path.insert(0, ".")
sys.path.insert(0, "..")
tdir = "tests/" if os.path.exists("tests") else ""


def test_diff_of_same_yaml():
    """diff of a yml against a copy of itself better darn be empty"""
    a = MDF(tdir + "samples/test-model-a.yml", handle="test")
    b = MDF(tdir + "samples/test-model-a.yml", handle="test")
    actual = diff_models(a.model, b.model)
    expected = {}
    assert actual == expected


def test_diff_of_extra_node_properties_and_terms():
    """a_b"""
    a = MDF(tdir + "samples/test-model-a.yml", handle="test")
    b = MDF(tdir + "samples/test-model-b.yml", handle="test")
    actual = diff_models(a.model, b.model)
    expected = {
        "nodes": {"file": {"props": {"a": None, "b": ["encryption_type"]}}},
        "props": {
            ("sample", "sample_type"): {"value_set": {"a": None, "b": ["not a tumor"]}},
            "a": None,
            "b": [("file", "encryption_type")],
        },
    }
    assert actual == expected


def test_diff_of_extra_node_property():
    """a_d"""
    a = MDF(tdir + "samples/test-model-a.yml", handle="test")
    b = MDF(tdir + "samples/test-model-d.yml", handle="test")
    actual = diff_models(a.model, b.model)
    expected = {
        "nodes": {"diagnosis": {"props": {"a": None, "b": ["fatal"]}}},
        "props": {"a": None, "b": [("diagnosis", "fatal")]},
    }
    assert actual == expected


def test_diff_of_extra_node_edge_and_property():
    """a_e"""
    a = MDF(tdir + "samples/test-model-a.yml", handle="test")
    b = MDF(tdir + "samples/test-model-e.yml", handle="test")
    actual = diff_models(a.model, b.model)
    expected = {
        "nodes": {"a": None, "b": ["outcome"]},
        "edges": {"a": None, "b": [("end_result", "diagnosis", "outcome")]},
        "props": {"a": None, "b": [("outcome", "fatal")]},
    }
    assert actual == expected


def test_diff_of_extra_node():
    """a_f"""
    a = MDF(tdir + "samples/test-model-a.yml", handle="test")
    b = MDF(tdir + "samples/test-model-f.yml", handle="test")
    actual = diff_models(a.model, b.model)
    expected = {
        "nodes": {"a": ["diagnosis"], "b": None},
        "edges": {"a": [("of_case", "diagnosis", "case")], "b": None},
        "props": {"a": [("diagnosis", "disease")], "b": None},
    }
    assert actual == expected


def test_diff_of_missing_node():
    """a_g"""
    a = MDF(tdir + "samples/test-model-a.yml", handle="test")
    b = MDF(tdir + "samples/test-model-g.yml", handle="test")
    actual = diff_models(a.model, b.model)
    expected = {
        "nodes": {"a": None, "b": ["outcome"]},
        "props": {"a": None, "b": [("outcome", "disease")]},
    }
    assert actual == expected


def test_diff_of_swapped_nodeprops():
    """a_h"""
    a = MDF(tdir + "samples/test-model-a.yml", handle="test")
    b = MDF(tdir + "samples/test-model-h.yml", handle="test")
    actual = diff_models(a.model, b.model)
    for node_val in actual["nodes"].values():
        node_val["props"]["a"].sort()
        node_val["props"]["b"].sort()
    actual["props"]["a"].sort()
    actual["props"]["b"].sort()
    expected = {
        "nodes": {
            "diagnosis": {
                "props": {"a": ["disease"], "b": ["file_name", "file_size", "md5sum"]}
            },
            "file": {
                "props": {"a": ["file_name", "file_size", "md5sum"], "b": ["disease"]}
            },
        },
        "props": {
            "a": [
                ("diagnosis", "disease"),
                ("file", "file_name"),
                ("file", "file_size"),
                ("file", "md5sum"),
            ],
            "b": [
                ("diagnosis", "file_name"),
                ("diagnosis", "file_size"),
                ("diagnosis", "md5sum"),
                ("file", "disease"),
            ],
        },
    }
    assert actual == expected


def test_diff_where_yaml_has_extra_term():
    """c_d"""
    a = MDF(tdir + "samples/test-model-c.yml", handle="test")
    b = MDF(tdir + "samples/test-model-d.yml", handle="test")
    actual = diff_models(a.model, b.model)
    expected = {
        "props": {("diagnosis", "fatal"): {"value_set": {"a": None, "b": ["unknown"]}}}
    }
    assert actual == expected


def test_diff_of_assorted_changes():
    """d_e"""
    a = MDF(tdir + "samples/test-model-d.yml", handle="test")
    b = MDF(tdir + "samples/test-model-e.yml", handle="test")
    actual = diff_models(a.model, b.model)
    expected = {
        "nodes": {
            "diagnosis": {"props": {"a": ["fatal"], "b": None}},
            "a": None,
            "b": ["outcome"],
        },
        "edges": {"a": None, "b": [("end_result", "diagnosis", "outcome")]},
        "props": {"a": [("diagnosis", "fatal")], "b": [("outcome", "fatal")]},
    }
    assert actual == expected


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
