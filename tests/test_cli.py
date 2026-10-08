import json
from pathlib import Path

from archguard.cli import main
from archguard.visualizer import build_mermaid

ROOT = Path(__file__).parents[1]
DEMO = ROOT / "demo_repo"


def run(tmp_path, *extra, edges=None):
    argv = [
        "check", "--repo", str(DEMO),
        "--output-md", str(tmp_path / "r.md"),
        "--output-html", str(tmp_path / "r.html"),
        *extra,
    ]
    if edges is not None:
        argv += ["--edges", str(edges)]
    return main(argv)


def write_edges(tmp_path, edges):
    f = tmp_path / "edges.json"
    f.write_text(json.dumps({"declared_edges": edges}))
    return f


def test_demo_reports_exactly_one_drift(tmp_path, capsys):
    assert run(tmp_path, edges=DEMO / "declared_edges.json") == 1
    out = capsys.readouterr().out
    assert out.count("   ! ") == 1
    assert "order_service -> database in order_service/checkout.py:2" in out
    assert "DRIFT" in (tmp_path / "r.md").read_text()


def test_clean_repo_passes(tmp_path, capsys):
    full = [
        ["api_gateway", "order_service"],
        ["order_service", "inventory_service"],
        ["order_service", "database"],
        ["inventory_service", "database"],
    ]
    assert run(tmp_path, edges=write_edges(tmp_path, full)) == 0
    assert "100%" in (tmp_path / "r.html").read_text()


def test_stale_edge_fails_unless_allowed(tmp_path, capsys):
    full = [
        ["api_gateway", "order_service"],
        ["order_service", "inventory_service"],
        ["order_service", "database"],
        ["inventory_service", "database"],
        ["api_gateway", "database"],  # not used by the code
    ]
    f = write_edges(tmp_path, full)
    assert run(tmp_path, edges=f) == 1
    assert "api_gateway -> database" in capsys.readouterr().out
    assert run(tmp_path, "--allow-stale", edges=f) == 0


def test_declared_name_variants_do_not_cause_false_drift(tmp_path):
    full = [
        ["API Gateway", "Order-Service"],
        ["order_service", "inventory_service"],
        ["order_service", "database"],
        ["inventory_service", "database"],
    ]
    assert run(tmp_path, edges=write_edges(tmp_path, full)) == 0


def test_missing_edges_file_is_a_clear_error(tmp_path, capsys):
    assert run(tmp_path, edges=tmp_path / "typo.json") == 2
    assert "--edges file not found" in capsys.readouterr().err


def test_bad_edges_file_exits_2(tmp_path, capsys):
    f = tmp_path / "bad.json"
    f.write_text("{not json")
    assert run(tmp_path, edges=f) == 2


def test_missing_repo_exits_2(tmp_path):
    assert main(["check", "--repo", str(tmp_path / "nope")]) == 2


def test_mermaid_dedupes_drift_and_quotes_keyword_names():
    drift = [
        {"source": "a", "target": "end", "file": "a/m.py", "line": 1},
        {"source": "a", "target": "end", "file": "a/m.py", "line": 2},
    ]
    code = build_mermaid([["a", "b"]], drift)
    assert code.count("-.->") == 1
    assert "(+1 more)" in code
    assert 'n_end["end"]' in code
