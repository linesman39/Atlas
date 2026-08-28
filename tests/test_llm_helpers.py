import pytest

from atlas.llm import extract_json


def test_extract_json_plain():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_with_code_fence():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_with_surrounding_prose():
    assert extract_json('Sure, here you go:\n{"a": 1}\nHope that helps!') == {"a": 1}


def test_extract_json_array():
    assert extract_json("[1, 2, 3]") == [1, 2, 3]


def test_extract_json_nested():
    assert extract_json('{"a": {"b": [1, 2]}}') == {"a": {"b": [1, 2]}}


def test_extract_json_raises_when_absent():
    with pytest.raises(ValueError):
        extract_json("no json here at all")
