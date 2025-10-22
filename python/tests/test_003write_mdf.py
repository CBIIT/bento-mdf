from pathlib import Path
from pdb import set_trace
from tempfile import NamedTemporaryFile

import pytest
import yaml
from bento_mdf import MDFReader, MDFValidator, MDFWriter
from bento_mdf.diff import diff_models
from bento_meta.model import Model
from bento_meta.objects import Concept, Node, Property, Tag, Term
from yaml import Loader as yloader

TDIR = Path("tests/").resolve() if Path("tests").exists() else Path.cwd()


def test_write_mdf():
    yml = yaml.load(open(TDIR / "samples" / "test-model.yml"), Loader=yloader)
    m = MDFReader(TDIR / "samples" / "test-model.yml", handle="test")
    wr_m = MDFWriter(model=m.model)
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
        if yml["Relationships"][n].get("Props"):
            def_props = set(yml["Relationships"][n]["Props"])
        yml_ends = yml["Relationships"][n]["Ends"]
        yml_ends = {(x["Src"], x["Dst"]): x for x in yml_ends}
        mdf_ends = mdf["Relationships"][n]["Ends"]
        mdf_ends = {(x["Src"], x["Dst"]): x for x in mdf_ends}
        if def_props:  # i.e., there are default properties in the source file
            assert set(mdf["Relationships"][n]["Props"]) == def_props
        for ends in yml_ends:
            assert mdf_ends[ends]
            # Note, props at specific End specs are not currently allowed by MDF Schema
            if "Props" in yml_ends[ends]:
                assert set(mdf_ends[ends]["Props"]) == set(yml_ends[ends]["Props"])

    yp = yml["PropDefinitions"]
    mp = mdf["PropDefinitions"]
    assert yp["case_id"]["Type"]["pattern"] == mp["case_id"]["Type"]["pattern"]
    assert yp["patient_id"]["Type"] == mp["patient_id"]["Type"]
    assert set(yp["sample_type"]["Enum"]) == set(mp["sample_type"]["Enum"])
    assert set(yp["amount"]["Type"]["units"]) == set(mp["amount"]["Type"]["units"])
    assert set(yp["file_size"]["Type"]["units"]) == set(
        mp["file_size"]["Type"]["units"]
    )
    assert (
        yp["file_size"]["Type"]["value_type"] == mp["file_size"]["Type"]["value_type"]
    )
    assert yp["md5sum"]["Tags"]["another"] == mp["md5sum"]["Tags"]["another"]
    # following asserts that model building in reader.py collects terms appropriately
    assert set([x for x in yml["Terms"]]) == set([x for x in mdf["Terms"]])


def test_read_write_gold_std_roundtrip():
    m = MDFReader(TDIR / "samples" / "crdc_datahub_mdf.yml", handle="test")
    wr_m = MDFWriter(model=m.model)
    assert isinstance(wr_m.model, Model)
    with NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False) as mdf_w:
        wr_m.write_mdf(file=mdf_w)
        mdf_w.close()
        # validate generated MDF
        val = MDFValidator(None, mdf_w.name, raise_error=True)
        val.load_and_validate_schema()
        val.load_and_validate_yaml()
        val.validate_instance_with_schema()
        # check that generated model is equivalent to input model
        rd_wr_m = MDFReader(mdf_w.name)
        result = diff_models(rd_wr_m.model, m.model, include_summary=True)
        assert result["summary"] is None
        Path(mdf_w.name).unlink()


@pytest.mark.skip(
    "Need a schema change (allow Terms to have Term keys) for this use case"
)
def test_write_mdf_nested_terms_tags():
    model = Model(handle="test", version="1.0.0")
    node = Node({"handle": "test_node"})
    model.add_node(node)
    prop = Property({"handle": "test_prop", "value_domain": "value_set"})
    model.add_prop(node, prop)
    term_1 = Term(
        {
            "value": "Test Term 1",
            "origin_id": "111",
            "origin_name": "test",
            "origin_definition": "test term 1",
            "handle": "test_term_1",
        }
    )
    # tag
    tag = Tag({"key": "test_tag_key", "value": "test_tag_val"})
    term_1.tags[tag.key] = tag
    # concept w/ synonym terms
    concept = Concept()
    term_2 = Term(
        {
            "value": "Test Term 2",
            "origin_id": "222",
            "origin_name": "test",
            "origin_definition": "test term 2",
            "handle": "test_term_2",
        }
    )
    term_3 = Term(
        {
            "value": "Test Term 3",
            "origin_id": "333",
            "origin_name": "test",
            "origin_definition": "test term 3",
            "handle": "test_term_3",
        }
    )
    concept.terms[term_2.value] = term_2
    concept.terms[term_3.value] = term_3
    term_1.concept = concept
    model.add_terms(prop, term_1)
    mdf = MDFWriter(model=model)
    mdf_dict = mdf.write_mdf()
    set_trace()
    actual = mdf_dict.get("Terms")
    expected = {
        "test_term_1": {
            "Term": [
                {
                    "Value": "Test Term 2",
                    "Definition": "test term 2",
                    "Origin": "test",
                    "Code": "222",
                    "Handle": "test_term_2",
                },
                {
                    "Value": "Test Term 3",
                    "Definition": "test term 3",
                    "Origin": "test",
                    "Code": "333",
                    "Handle": "test_term_3",
                },
            ],
            "Tags": {"test_tag_key": "test_tag_val"},
            "Value": "Test Term 1",
            "Definition": "test term 1",
            "Origin": "test",
            "Code": "111",
            "Handle": "test_term_1",
        }
    }
    assert actual == expected


def test_write_use_null_cde_to_term():
    """
    Test that useNullCDE Property tag gets written to caDSR term spec.

    When a Property has a useNullCDE tag and caDSR terms, the writer should
    add useNullCDE to the first caDSR term in the Term list.
    """
    m = MDFReader(TDIR / "samples" / "test-model-null-cde.yml", handle="test_null_cde")
    wr_m = MDFWriter(model=m.model)
    mdf = wr_m.write_mdf()

    # Check imaging_software property
    imaging_software = mdf["PropDefinitions"]["imaging_software"]
    assert "Term" in imaging_software
    assert len(imaging_software["Term"]) == 1

    # Should have useNullCDE in the term spec
    term = imaging_software["Term"][0]
    assert term["Origin"] == "caDSR"
    assert "useNullCDE" in term
    assert term["useNullCDE"] is True  # YAML converts "Yes" to True

    # Check processing_method property
    processing_method = mdf["PropDefinitions"]["processing_method"]
    assert "Term" in processing_method
    assert len(processing_method["Term"]) == 1

    term = processing_method["Term"][0]
    assert term["Origin"] == "caDSR"
    assert "useNullCDE" in term
    assert term["useNullCDE"] is False  # YAML converts "No" to False


def test_write_use_null_cde_roundtrip():
    """
    Test round-trip: read → write → read preserves useNullCDE.

    Ensures that reading an MDF with useNullCDE, writing it back out,
    and reading it again produces the same result.
    """
    m1 = MDFReader(TDIR / "samples" / "test-model-null-cde.yml", handle="test_null_cde")

    with NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        temp_path = f.name
        MDFWriter(model=m1.model).write_mdf(file=f)

    m2 = MDFReader(temp_path, handle="test_null_cde")

    img_prop_1 = m1.model.props[("sample", "imaging_software")]
    img_prop_2 = m2.model.props[("sample", "imaging_software")]

    assert "useNullCDE" in img_prop_1.tags
    assert "useNullCDE" in img_prop_2.tags
    assert img_prop_1.tags["useNullCDE"].value == img_prop_2.tags["useNullCDE"].value

    proc_prop_1 = m1.model.props[("sample", "processing_method")]
    proc_prop_2 = m2.model.props[("sample", "processing_method")]

    assert "useNullCDE" in proc_prop_1.tags
    assert "useNullCDE" in proc_prop_2.tags
    assert proc_prop_1.tags["useNullCDE"].value == proc_prop_2.tags["useNullCDE"].value

    Path(temp_path).unlink()  # cleanup


def test_write_use_null_cde_only_on_cadsr_terms():
    """
    Test that useNullCDE only appears on caDSR terms, not others.

    If a Property has both caDSR and non-caDSR terms, useNullCDE should
    only appear on the caDSR term.
    """
    model = Model(handle="test")
    node = Node({"handle": "test_node", "model": "test"})
    model.add_node(node)

    prop = Property({"handle": "test_prop", "value_domain": "string"})
    node.props[prop.handle] = prop
    prop.belongs[node] = node
    model.add_prop(node, prop)

    concept = Concept({"_commit": "test"})
    prop.concept = concept

    term1 = Term(
        {
            "handle": "cadsr_term",
            "value": "Test CDE",
            "origin_name": "caDSR",
            "origin_id": "123",
            "_commit": "test",
        }
    )
    concept.terms[
        (term1.handle, term1.origin_name, term1.origin_id, term1.origin_version)
    ] = term1

    term2 = Term(
        {
            "handle": "ncit_term",
            "value": "Test Term",
            "origin_name": "NCIt",
            "origin_id": "C456",
            "_commit": "test",
        }
    )
    concept.terms[
        (term2.handle, term2.origin_name, term2.origin_id, term2.origin_version)
    ] = term2

    prop.tags["useNullCDE"] = Tag(
        {"key": "useNullCDE", "value": True, "_commit": "test"}
    )

    wr_m = MDFWriter(model=model)
    mdf = wr_m.write_mdf()

    prop_spec = mdf["PropDefinitions"]["test_prop"]
    assert "Term" in prop_spec

    cadsr_terms = [t for t in prop_spec["Term"] if t["Origin"] == "caDSR"]
    ncit_terms = [t for t in prop_spec["Term"] if t["Origin"] == "NCIt"]

    assert len(cadsr_terms) == 1
    assert len(ncit_terms) == 1

    assert "useNullCDE" in cadsr_terms[0]
    assert "useNullCDE" not in ncit_terms[0]
