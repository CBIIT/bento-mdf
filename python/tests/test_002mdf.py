"""Tests for bento_mdf.mdf."""

from pathlib import Path

import pytest
from bento_mdf.mdf import MDF, convert_github_url
from bento_meta.entity import ArgError
from bento_meta.model import Model
from bento_meta.objects import ValueSet

from tests.samples.test_urls import TEST_CONVERT_URLS
from pdb import set_trace

TDIR = Path("tests/").resolve() if Path("tests").exists() else Path().resolve()
CTDC_MODEL_FILE = TDIR / "samples" / "ctdc_model_file.yaml"
CTDC_MODEL_PROPS_FILE = TDIR / "samples" / "ctdc_model_properties_file.yaml"
ICDC_MODEL_URL = "https://cbiit.github.io/icdc-model-tool/model-desc/icdc-model.yml"
ICDC_PROPS_URL = (
    "https://cbiit.github.io/icdc-model-tool/model-desc/icdc-model-props.yml"
)
TEST_MODEL_FILE = TDIR / "samples" / "test-model.yml"
TEST_MODEL_QUAL_PROPS_FILE = TDIR / "samples" / "test-model-qual-props.yml"
TEST_MODEL_TERMS_A = TDIR / "samples" / "test-model-with-terms-a.yml"
CRDC_MODEL_FILE = TDIR / "samples" / "crdc_datahub_mdf.yml"
CCDI_MODEL_URL = (
    "https://github.com/CBIIT/ccdi-model/blob/main/model-desc/ccdi-model.yml"
)
CCDI_PROPS_URL = (
    "https://github.com/CBIIT/ccdi-model/blob/main/model-desc/ccdi-model-props.yml"
)
TEST_SEP_ENUM_MODEL_FILE_PATH = TDIR / "samples" / "test-model-sep-enum.yml"
TEST_SEP_ENUM_MODEL_FILE_URL = TDIR / "samples" / "test-model-sep-enum-url.yml"


def test_class() -> None:
    m = MDF(handle="test")
    assert isinstance(m, MDF)
    with pytest.raises(ArgError, match="arg model= must"):
        MDF(model="boog")


def test_load_yaml() -> None:
    m = MDF(handle="test")
    m.files = [CTDC_MODEL_FILE, CTDC_MODEL_PROPS_FILE]
    m.load_yaml(verify=False)
    assert m.mdf["Nodes"]


def test_load_yaml_url() -> None:
    m = MDF(handle="ICDC")
    m.files = [ICDC_MODEL_URL, ICDC_PROPS_URL]
    m.load_yaml()
    m.create_model()
    assert m.model


def test_create_model() -> None:
    m = MDF(handle="test")
    m.files = [CTDC_MODEL_FILE, CTDC_MODEL_PROPS_FILE]
    m.load_yaml()
    m.create_model()
    assert m.model


def test_created_model() -> None:
    m = MDF(TEST_MODEL_FILE, handle="test")
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
        "date_of_dx",
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
    # following tests specific Props at Rel:Ends spec
    # assert len(derived_from.props.keys()) == 1
    # assert next(iter(derived_from.props.values())).handle == "id"
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


def test_create_model_qual_props() -> None:
    m = MDF(handle="test")
    m.files = [TEST_MODEL_QUAL_PROPS_FILE]
    m.load_yaml()
    m.create_model()
    assert m.model.nodes["case"].props["disease"].value_domain == "string"
    assert m.model.nodes["diagnosis"].props["disease"].value_domain == "url"
    assert (
        m.model.edges[("derived_from", "file", "file")].props["disease"].value_domain
        == "url"
    )


def test_create_model_with_terms_section() -> None:
    m = MDF(handle="test")
    m.files = [TEST_MODEL_TERMS_A]
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


class TestDataHubModel:
    """Tests for parts of the CRDC DataHub sample model."""

    def setup_method(self) -> None:
        """Set up MDF for testing."""
        self.m = MDF(CRDC_MODEL_FILE)

    def test_create_dh_model(self) -> None:
        """Test creating the CRDC model."""
        assert self.m.model
        pr = [x for x in self.m.model.props.values() if x.handle == "collection_method"]
        assert pr[0]
        assert pr[0].value_set.path == '/path/to/collection/methods'

    def test_property_is_key(self) -> None:
        """Test "is_key" attribute set on Property from "Key" object in MDF."""
        assert self.m.model.props[("diagnosis", "diagnosis_id")].is_key is True
        assert self.m.model.props[("diagnosis", "transaction_date")].is_key is False

    def test_property_is_key_default(self) -> None:
        """Test "is_key" attribute set to False when "Key" not present in MDF."""
        assert self.m.model.props[("diagnosis", "diagnosis")].is_key is False

    def test_list_property_with_enum(self) -> None:
        """Test attributes of a list-type Property and Enum item_domain."""
        p = self.m.model.props[("study", "study_data_types")]
        assert p.value_domain == "list"
        assert p.item_domain == "value_set"
        assert p.values == ["Genomic", "Imaging", "Clinical"]  # noqa: PD011
        assert list(p.terms.keys()) == ["Genomic", "Imaging", "Clinical"]

    def test_property_is_strict(self) -> None:
        """Test "is_strict" attribute set on Property from "Strict" object in MDF."""
        assert self.m.model.props[("diagnosis", "diagnosis")].is_strict is False
        assert self.m.model.props[("participant", "race")].is_strict is True

    def test_property_is_strict_default(self) -> None:
        """Test "is_strict" attribute set to False when "Strict" not present in MDF."""
        assert (
            self.m.model.props[("study", "adult_or_childhood_study")].is_strict is True
        )

    def test_property_is_required(self) -> None:
        """Test "is_required" attribute set on Property from "Req" object in MDF."""
        assert self.m.model.props[("diagnosis", "diagnosis")].is_required == "Preferred"
        assert self.m.model.props[("diagnosis", "id")].is_required is True
        assert self.m.model.props[("diagnosis", "date")].is_required is True
        assert self.m.model.props[("diagnosis", "transaction_id")].is_required is False
        assert (
            self.m.model.props[("diagnosis", "transaction_date")].is_required is False
        )

    def test_property_is_required_default(self) -> None:
        """Test "is_required" attribute set to False when "Req" not present in MDF."""
        assert self.m.model.props[("diagnosis", "diagnosis_id")].is_required is False

    def test_enum_list_type(self) -> None:
        """Test list types expressed as (value_type, item_type) and (value_type, Enum)."""
        sdt = self.m.model.props[("study", "study_data_types")]
        sdte = self.m.model.props[("study", "study_data_types_enum")]
        assert len(sdt.terms) == 3
        assert len(sdte.terms) == 3
        assert "Genomic" in sdt.terms
        assert "Imaging" in sdte.terms


@pytest.mark.parametrize(("input_url", "expected_url"), TEST_CONVERT_URLS)
def test_convert_github_url(input_url: str, expected_url: str) -> None:
    """Test converting a GitHub blob URL to a raw URL."""
    assert convert_github_url(input_url) == expected_url


def test_load_repo_url() -> None:
    """Test loading model from a GitHub blob URL converted to raw URL."""
    m = MDF(handle="CCDI")
    m.files = [CCDI_MODEL_URL, CCDI_PROPS_URL]
    m.load_yaml()
    m.create_model()
    assert m.model


def test_load_separate_enums_yaml_from_file_path() -> None:
    """Test loading model where enum list in separate yaml file referenced by path."""
    m = MDF(TEST_SEP_ENUM_MODEL_FILE_PATH, handle="CCDI")
    set_trace()
    # sex_at_birth
    assert "female" in m.model.props[("participant", "sex_at_birth")].terms
    assert ("male", "caDSR") in m.model.terms
    assert "intersex" in m.model.props[("participant", "sex_at_birth")].terms
    assert ("none_of_these_describe_me", "CCDI") in m.model.terms
    # race
    assert "asian" in m.model.props[("participant", "race")].terms
    assert ("white", "caDSR") in m.model.terms
    assert "hispanic_or_latino" in m.model.props[("participant", "race")].terms
    assert ("middle_eastern_or_north_african", "CCDI") in m.model.terms


def test_load_separate_enums_yaml_from_url() -> None:
    """Test loading model where enum list in separate yaml file referenced by url."""
    m = MDF(TEST_SEP_ENUM_MODEL_FILE_URL, handle="CCDI")
    # sex_at_birth
    assert "female" in m.model.props[("participant", "sex_at_birth")].terms
    assert ("male", "caDSR") in m.model.terms
    assert "intersex" in m.model.props[("participant", "sex_at_birth")].terms
    assert ("none_of_these_describe_me", "CCDI") in m.model.terms
    # race
    assert "asian" in m.model.props[("participant", "race")].terms
    assert ("white", "caDSR") in m.model.terms
    assert "hispanic_or_latino" in m.model.props[("participant", "race")].terms
    assert ("middle_eastern_or_north_african", "CCDI") in m.model.terms
