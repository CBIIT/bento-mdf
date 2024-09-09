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
from pdb import set_trace

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


def test_create_model_with_terms_section():
    m = MDF(handle="test")
    m.files = ["{}samples/test-model-with-terms.yml".format(TDIR)]
    m.load_yaml()
    m.create_model()
    assert m._terms["normal"].origin_name == "Fred"
    assert m._terms["tumor"].origin_name == "Al"
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

# union type deprecated
# def test_create_model_union_type():
#     m = MDF(handle="test")
#     m.files = ["{}samples/test-model-union-type.yml".format(TDIR)]
#     m.load_yaml()
#     m.create_model()
#     assert m.model
#     assert m.model.nodes["case"].props["disease"].value_domain == "union"
#     assert type(m.model.nodes["case"].props["disease"].value_types) == list
#     assert {
#         x["value_domain"] for x in m.model.nodes["case"].props["disease"].value_types
#     } == {"string", "url"}
#     assert m.model.nodes["sample"].props["sample_type"].value_domain == "union"
#     vt = m.model.nodes["sample"].props["sample_type"].value_types
#     assert {t.value for t in vt[1]["value_set"]} == {"normal", "tumor"}
