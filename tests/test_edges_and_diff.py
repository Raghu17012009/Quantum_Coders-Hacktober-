import json

import pytest

from archguard.dag_extractor import _parse_model_json, extract_declared_edges
from archguard.diff_engine import find_drift, find_stale
from archguard.edges import normalize_edges

MODS = ["api_gateway", "order_service"]


def test_normalize_edges_names_filters_and_dedupes():
    kept, dropped = normalize_edges(
        [["API Gateway", "order-service"], ["api_gateway", "order_service"], ["a", "a"], ["x"], ["api_gateway", "redis"]],
        MODS,
    )
    assert kept == [["api_gateway", "order_service"]]
    assert dropped == [["api_gateway", "redis"]]


def test_offline_contract_is_normalized_like_live(tmp_path):
    f = tmp_path / "e.json"
    f.write_text(json.dumps({"declared_edges": [["API_Gateway", "Order Service"]]}))
    assert extract_declared_edges("x.png", MODS, fallback_file=f) == [["api_gateway", "order_service"]]


def test_drift_and_stale():
    declared = [["a", "b"], ["b", "c"]]
    actual = [("a", "b", "f.py", 1), ("a", "c", "f.py", 2), ("a", "c", "g.py", 9)]
    assert [(d["source"], d["target"], d["line"]) for d in find_drift(declared, actual)] == [
        ("a", "c", 2),
        ("a", "c", 9),
    ]
    assert find_stale(declared, actual) == [{"source": "b", "target": "c"}]


def test_no_findings_when_in_sync():
    assert find_drift([["a", "b"]], [("a", "b", "f", 1)]) == []
    assert find_stale([["a", "b"]], [("a", "b", "f", 1)]) == []


def test_parse_model_json_handles_fences_chatter_and_extra_braces():
    assert _parse_model_json('```json\n{"declared_edges": [["a","b"]]}\n```') == [["a", "b"]]
    assert _parse_model_json('Sure {not json} here: {"declared_edges": [["a","b"]]} bye {x}') == [["a", "b"]]


def test_parse_model_json_rejects_garbage():
    with pytest.raises(ValueError):
        _parse_model_json("no json here")
