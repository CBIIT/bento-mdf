"""Tests for converting MDF specifications to bento-meta entities."""

import pytest
from bento_meta.objects import Term

from bento_mdf.mdf.convert import spec_to_entity


def test_null_term_value_reports_offending_spec():
    spec = {
        "Value": None,
        "Origin": "caDSR",
        "Definition": "None",
        "Code": "TBD",
    }

    with pytest.raises(ValueError) as exc_info:
        spec_to_entity(
            None,
            spec,
            {"_commit": "dummy"},
            Term,
        )

    message = str(exc_info.value)
    assert "Term Value cannot be null" in message
    assert repr(spec) in message

def test_term_with_value_generates_handle():
    term = spec_to_entity(
        None,
        {
            "Value": "Adjacent Biospecimen",
            "Origin": "caDSR",
        },
        {"_commit": "dummy"},
        Term,
    )

    assert term.value == "Adjacent Biospecimen"
    assert term.handle == "adjacent_biospecimen"