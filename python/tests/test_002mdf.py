"""Tests for bento_mdf.mdf"""
import os.path
import sys

import pytest
import yaml
from bento_mdf.mdf import MDF
from bento_meta.entity import ArgError
from bento_meta.model import Model
from bento_meta.objects import Concept, Node, Property, Tag, Term, ValueSet
from yaml import Loader as yloader

TDIR = "tests/" if os.path.exists("tests") else ""

def test_class():
    m = MDF(handle="test")
    assert isinstance(m, MDF)
    with pytest.raises(ArgError, match="arg model= must"):
        MDF(model="boog")


def test_load_yaml():
    m = MDF(handle="test")
    m.files = [
        "{}samples/ctdc_model_file.yaml".format(TDIR),
        "{}samples/ctdc_model_properties_file.yaml".format(TDIR),
    ]
    m.load_yaml(verify=False)
    assert m.mdf["Nodes"]


def test_load_yaml_url():
    m = MDF(handle="ICDC")
    m.files = [
        "https://cbiit.github.io/icdc-model-tool/model-desc/icdc-model.yml",
        "https://cbiit.github.io/icdc-model-tool/model-desc/icdc-model-props.yml",
    ]
    m.load_yaml()
    m.create_model()
    assert m.model


def test_create_model():
    m = MDF(handle="test")
    m.files = [
        "{}samples/ctdc_model_file.yaml".format(TDIR),
        "{}samples/ctdc_model_properties_file.yaml".format(TDIR),
    ]
    m.load_yaml()
    m.create_model()
    assert m.model


def test_created_model():
    m = MDF("{}samples/test-model.yml".format(TDIR), handle="test")
    assert isinstance(m.model, Model)
    assert set([x.handle for x in m.model.nodes.values()]) == {
        "case",
        "sample",
        "file",
        "diagnosis",
    }
    assert set([x.triplet for x in m.model.edges.values()]) == {
        ("of_case", "sample", "case"),
        ("of_case", "diagnosis", "case"),
        ("of_sample", "file", "sample"),
        ("derived_from", "file", "file"),
        ("derived_from", "sample", "sample"),
    }
    assert set([x.handle for x in m.model.props.values()]) == {
        "case_id",
        "patient_id",
        "sample_type",
        "amount",
        "md5sum",
        "file_name",
        "file_size",
        "disease",
        "days_to_sample",
        "workflow_id",
        "id",
    }
    assert m.model.nodes["case"].concept
    assert [x for x in m.model.nodes["case"].concept.terms.values()][
        0
    ].origin_name == "CTDC"
    assert m.model.edges[("of_case", "sample", "case")].concept
    assert [
        x for x in m.model.edges[("of_case", "sample", "case")].concept.terms.values()
    ][0].origin_name == "CTDC"
    assert m.model.props[("case", "case_id")].concept
    assert [x for x in m.model.props[("case", "case_id")].concept.terms.values()][
        0
    ].origin_name == "CTDC"
    file_ = m.model.nodes["file"]
    assert file_
    assert file_.props
    assert set([x.handle for x in file_.props.values()]) == {
        "md5sum",
        "file_name",
        "file_size",
    }
    assert m.model.nodes["file"].props["md5sum"].value_domain == "regexp"
    assert m.model.nodes["file"].props["md5sum"].pattern
    amount = m.model.props[("sample", "amount")]
    assert amount
    assert amount.value_domain == "number"
    assert amount.units == "mg"
    file_size = m.model.props[("file", "file_size")]
    assert file_size
    assert file_size.units == "Gb;Mb"
    derived_from = m.model.edges[("derived_from", "sample", "sample")]
    assert derived_from
    assert len(derived_from.props.keys()) == 1
    assert next(iter(derived_from.props.values())).handle == "id"
    d_f = m.model.edges_by_dst(m.model.nodes["file"])
    assert d_f
    assert len(d_f) == 1
    assert "workflow_id" in d_f[0].props.keys()
    assert len(m.model.edges_in(m.model.nodes["case"])) == 2
    assert len(m.model.edges_out(m.model.nodes["file"])) == 2
    sample = m.model.nodes["sample"]
    sample_type = sample.props["sample_type"]
    assert sample_type.value_domain == "value_set"
    assert isinstance(sample_type.value_set, ValueSet)
    assert set(sample_type.values) == {"tumor", "normal"}
    assert m.model.nodes["case"].tags["this"].value == "that"
    assert (
        m.model.edges[("derived_from", "sample", "sample")].tags["item1"].value
        == "value1"
    )
    assert (
        m.model.edges[("derived_from", "sample", "sample")].tags["item2"].value
        == "value2"
    )
    assert m.model.nodes["file"].props["md5sum"].tags["another"].value == "value3"
    assert m.model.nodes["case"].concept.terms[("case_term", "CTDC")]
    assert m.model.nodes["case"].concept.terms[("case_term", "CTDC")].value == "case"
    assert m.model.nodes["case"].concept.terms[("subject", "caDSR")]


def test_create_model_qual_props():
    m = MDF(handle="test")
    m.files = ["{}samples/test-model-qual-props.yml".format(TDIR)]
    m.load_yaml()
    m.create_model()
    assert m.model.nodes["case"].props["disease"].value_domain == "string"
    assert m.model.nodes["diagnosis"].props["disease"].value_domain == "url"
    assert (
        m.model.edges[("derived_from", "file", "file")].props["disease"].value_domain
        == "url"
    )


def test_create_mode_with_terms_section():
    m = MDF(handle="test")
    m.files = ["{}samples/test-model-with-terms.yml".format(TDIR)]
    m.load_yaml()
    m.create_model()
    assert m._terms[("normal", "Fred")]
    assert m._terms[("tumor", "Al")]
    assert m.model.nodes["sample"].props["sample_type"].terms["normal"]
    assert m.model.nodes["sample"].props["sample_type"].terms["tumor"]
    assert m.model.nodes["sample"].props["sample_type"].terms["undetermined"]
    assert (
        m.model.nodes["sample"].props["sample_type"].terms["undetermined"].origin_name
        == "test"
    )
    assert (
        m.model.nodes["sample"].props["sample_type"].terms["normal"].origin_id == 10083
    )
    assert (
        m.model.nodes["sample"].props["sample_type"].terms["tumor"].origin_id == 10084
    )


def test_create_model_union_type():
    m = MDF(handle="test")
    m.files = ["{}samples/test-model-union-type.yml".format(TDIR)]
    m.load_yaml()
    m.create_model()
    assert m.model
    assert m.model.nodes["case"].props["disease"].value_domain == "union"
    assert type(m.model.nodes["case"].props["disease"].value_types) == list
    assert {
        x["value_domain"] for x in m.model.nodes["case"].props["disease"].value_types
    } == {"string", "url"}
    assert m.model.nodes["sample"].props["sample_type"].value_domain == "union"
    vt = m.model.nodes["sample"].props["sample_type"].value_types
    assert {t.value for t in vt[1]["value_set"]} == {"normal", "tumor"}


# @pytest.mark.skip("TODO")
def test_write_mdf():
    yml = yaml.load(open("{}samples/test-model.yml".format(TDIR), "r"), Loader=yloader)
    m = MDF("{}samples/test-model.yml".format(TDIR), handle="test")
    wr_m = MDF(model=m.model)
    assert isinstance(wr_m.model, Model)
    mdf = wr_m.write_mdf()
    assert isinstance(mdf, dict)

    assert set(yml["Nodes"]) == set(mdf["Nodes"])
    assert set(yml["Relationships"]) == set(mdf["Relationships"])
    assert set(yml["PropDefinitions"]) == set(mdf["PropDefinitions"])
    for n in yml["Nodes"]:
        if "Props" in yml["Nodes"][n]:
            assert set(yml["Nodes"][n]["Props"]) == set(mdf["Nodes"][n]["Props"])
    for n in yml["Relationships"]:
        def_props = set()
        if "Props" in yml["Relationships"][n]:
            def_props = set(yml["Relationships"][n]["Props"])
        yml_ends = yml["Relationships"][n]["Ends"]
        yml_ends = {(x["Src"], x["Dst"]): x for x in yml_ends}
        mdf_ends = mdf["Relationships"][n]["Ends"]
        mdf_ends = {(x["Src"], x["Dst"]): x for x in mdf_ends}
        for ends in yml_ends:
            assert mdf_ends[ends]
            if "Props" in yml_ends[ends]:
                assert set(mdf_ends[ends]["Props"]) == set(yml_ends[ends]["Props"])
            else:
                if def_props:  # i.e., there are default properties in the source file
                    assert set(mdf_ends[ends]["Props"]) == def_props
    yp = yml["PropDefinitions"]
    mp = mdf["PropDefinitions"]
    assert yp["case_id"]["Type"]["pattern"] == mp["case_id"]["Type"]["pattern"]
    assert yp["patient_id"]["Type"] == mp["patient_id"]["Type"]
    assert set(yp["sample_type"]["Type"]) == set(mp["sample_type"]["Enum"])
    assert set(yp["amount"]["Type"]["units"]) == set(mp["amount"]["Type"]["units"])
    assert set(yp["file_size"]["Type"]["units"]) == set(
        mp["file_size"]["Type"]["units"]
    )
    assert (
        yp["file_size"]["Type"]["value_type"] == mp["file_size"]["Type"]["value_type"]
    )
    assert yp["md5sum"]["Tags"]["another"] == mp["md5sum"]["Tags"]["another"]

def test_write_mdf_nested_terms_tags():
    model = Model(handle="test")
    node = Node({"handle": "test_node"})
    model.add_node(node)
    prop = Property({"handle": "test_prop", "value_domain": "value_set"})
    model.add_prop(node, prop)
    term_1 = Term({
        "value":"Test Term 1",
        "origin_id":"111",
        "origin_name": "test",
        "origin_definition": "test term 1",
        "handle": "test_term_1"
    })
    # tag
    tag = Tag({"key": "test_tag_key", "value": "test_tag_val"})
    term_1.tags[tag.key] = tag
    # concept w/ synonym terms
    concept = Concept()
    term_2 = Term({
        "value":"Test Term 2", 
        "origin_id":"222", 
        "origin_name": "test", 
        "origin_definition": "test term 2",
        "handle": "test_term_2"
    })
    term_3 = Term({
        "value":"Test Term 3", 
        "origin_id":"333", 
        "origin_name": "test", 
        "origin_definition": "test term 3",
        "handle": "test_term_3"
    })
    concept.terms[term_2.value] = term_2
    concept.terms[term_3.value] = term_3
    term_1.concept = concept
    model.add_terms(prop, term_1)
    mdf = MDF(handle="test", model=model)
    mdf_dict = mdf.write_mdf()
    actual = mdf_dict.get("Terms")
    expected = {
        'test_term_1': {
            'Term': [
                {
                    'Value': 'Test Term 2',
                    'Definition': "test term 2",
                    'Origin': "test",
                    'Code': '222',
                    'Handle': 'test_term_2'
                },
                {
                    'Value': 'Test Term 3',
                    'Definition': "test term 3",
                    'Origin': "test",
                    'Code': '333',
                    'Handle': 'test_term_3'
                }
            ],
            'Tags': {'test_tag_key': 'test_tag_val'},
            'Value': 'Test Term 1',
            'Definition': "test term 1",
            'Origin': "test",
            'Code': '111',
            'Handle': 'test_term_1'
        }
    }
    assert actual == expected
