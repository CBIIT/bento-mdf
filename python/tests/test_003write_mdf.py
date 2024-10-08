import os
import pytest
import yaml
from yaml import Loader as yloader
from bento_mdf.mdf import MDF
from bento_meta.model import Model
from bento_meta.objects import Concept, Node, Property, Tag, Term

TDIR = "tests/" if os.path.exists("tests") else ""


@pytest.mark.skip("TODO")
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


@pytest.mark.skip("TODO")    
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
