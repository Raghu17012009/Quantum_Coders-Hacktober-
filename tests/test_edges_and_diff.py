import json

import pytest

from archguard.dag_extractor import _parse_response, extract_declared_edges, normalize_name
from archguard.diff_engine import find_drift, find_stale

MODS = ["api_gateway", "order_service"]


def test_normalize_name():
    assert normalize_name(" Order-Service ") == "order_service"


def test_offline_contract_is_normalized_and_filtered(tmp_path):
    f = tmp_path / "e.json"
    f.write_text(
        json.dumps(
            {"declared_edges": [["API_Gateway", "Order Service"], ["api_gateway", "redis"]]}
        )
    )
    assert extract_declared_edges("x.png", MODS, fallback_file=str(f)) == [
        ["api_gateway", "order_service"]
    ]


def test_missing_contract_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        extract_declared_edges("x.png", MODS, fallback_file=str(tmp_path / "typo.json"))


def test_model_response_with_chatter_is_parsed():
    raw = 'Sure! {"declared_edges": [["API Gateway", "order-service"]]} done'
    assert _parse_response(raw, MODS) == [["api_gateway", "order_service"]]


def test_model_response_without_json_is_rejected():
    with pytest.raises(ValueError):
        _parse_response("no json here", MODS)


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
