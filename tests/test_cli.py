import json
from pathlib import Path

from archguard.cli import main

ROOT = Path(__file__).parents[1]
DEMO = ROOT / "demo_repo"

FULL = [
    ["api_gateway", "order_service"],
    ["order_service", "inventory_service"],
    ["order_service", "database"],
    ["inventory_service", "database"],
]


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
    report = (tmp_path / "r.md").read_text(encoding="utf-8")
    assert "FAIL" in report and "order_service/checkout.py#L2" in report


def test_clean_repo_passes(tmp_path, capsys):
    assert run(tmp_path, edges=write_edges(tmp_path, FULL)) == 0
    assert "0 undeclared edges" in capsys.readouterr().out
    assert "PASS" in (tmp_path / "r.md").read_text(encoding="utf-8")


def test_stale_edge_fails_unless_allowed(tmp_path, capsys):
    f = write_edges(tmp_path, FULL + [["api_gateway", "database"]])  # not used by the code
    assert run(tmp_path, edges=f) == 1
    assert "~ api_gateway -> database" in capsys.readouterr().out
    assert "Stale Diagram Edges" in (tmp_path / "r.md").read_text(encoding="utf-8")
    assert run(tmp_path, "--allow-stale", edges=f) == 0


def test_stale_and_drift_together(tmp_path, capsys):
    f = write_edges(
        tmp_path,
        [
            ["api_gateway", "order_service"],
            ["order_service", "inventory_service"],
            ["inventory_service", "database"],
            ["api_gateway", "database"],
        ],
    )
    assert run(tmp_path, edges=f) == 1
    out = capsys.readouterr().out
    assert "   ! order_service -> database" in out
    assert "   ~ api_gateway -> database" in out


def test_declared_name_variants_do_not_cause_false_drift(tmp_path):
    edges = [["API Gateway", "Order-Service"]] + FULL[1:]
    assert run(tmp_path, edges=write_edges(tmp_path, edges)) == 0


def test_missing_edges_file_exits_2(tmp_path, capsys):
    assert run(tmp_path, edges=tmp_path / "typo.json") == 2
    assert "Edge contract does not exist" in capsys.readouterr().err


def test_bad_edges_file_exits_2(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("{not json")
    assert run(tmp_path, edges=f) == 2


def test_missing_repo_exits_2(tmp_path):
    assert main(["check", "--repo", str(tmp_path / "nope")]) == 2


def test_interactive_prompt_answers(tmp_path):
    import builtins

    original = builtins.input
    builtins.input = lambda _prompt="": "y"
    try:
        assert run(tmp_path, "--interactive", edges=DEMO / "declared_edges.json") == 1
    finally:
        builtins.input = original


def test_duplicate_import_sites_draw_one_arrow(tmp_path):
    from archguard.visualizer import generate_drift_assets

    drift = [
        {"source": "a", "target": "b", "file": "a/m.py", "line": 1},
        {"source": "a", "target": "b", "file": "a/m.py", "line": 2},
    ]
    code = generate_drift_assets([["a", "c"]], drift, str(tmp_path / "m.md"), str(tmp_path / "h.html"))
    assert code.count("-.->") == 1
    report = (tmp_path / "m.md").read_text(encoding="utf-8")
    assert "a/m.py#L1" in report and "a/m.py#L2" in report  # both sites still listed
