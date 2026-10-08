from pathlib import Path

from archguard.ast_scanner import discover_modules, scan_module_imports

DEMO = Path(__file__).parents[1] / "demo_repo"


def make_pkg(root: Path, name: str, files: dict[str, str]):
    pkg = root / name
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("")
    for rel, body in files.items():
        f = pkg / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body)


def edges(root):
    mods = discover_modules(root)
    return {(s, t) for s, t, _f, _l in scan_module_imports(root, mods)}


def test_demo_modules_and_edges():
    mods = discover_modules(DEMO)
    assert mods == ["api_gateway", "database", "inventory_service", "order_service"]
    assert edges(DEMO) == {
        ("api_gateway", "order_service"),
        ("order_service", "inventory_service"),
        ("order_service", "database"),
        ("inventory_service", "database"),
    }


def test_records_file_and_line():
    recs = scan_module_imports(DEMO, discover_modules(DEMO))
    assert ("order_service", "database", "order_service/checkout.py", 2) in recs


def test_self_and_same_package_relative_imports_ignored(tmp_path):
    make_pkg(tmp_path, "a", {"m.py": "import a\nfrom . import n\nfrom .n import x\n"})
    make_pkg(tmp_path, "b", {})
    assert edges(tmp_path) == set()


def test_relative_import_out_of_package_is_detected(tmp_path):
    make_pkg(tmp_path, "a", {"m.py": "from ..b import thing\n", "sub/n.py": "from ... import b\n"})
    make_pkg(tmp_path, "b", {})
    assert edges(tmp_path) == {("a", "b")}


def test_relative_import_above_repo_root_ignored(tmp_path):
    make_pkg(tmp_path, "a", {"m.py": "from ...b import thing\n"})
    make_pkg(tmp_path, "b", {})
    assert edges(tmp_path) == set()


def test_aliased_submodule_and_dynamic_imports(tmp_path):
    make_pkg(
        tmp_path,
        "a",
        {
            "m.py": (
                "import b.core as c\n"
                "import importlib\n"
                "importlib.import_module('d.plugins')\n"
                "__import__('e')\n"
                "importlib.import_module(name)\n"  # non-literal: ignored
            )
        },
    )
    for n in "bde":
        make_pkg(tmp_path, n, {})
    assert edges(tmp_path) == {("a", "b"), ("a", "d"), ("a", "e")}


def test_every_import_site_is_reported(tmp_path):
    make_pkg(tmp_path, "a", {"m.py": "import b\nimport b.sub\n"})
    make_pkg(tmp_path, "b", {})
    recs = scan_module_imports(tmp_path, discover_modules(tmp_path))
    assert [(r[1], r[3]) for r in recs] == [("b", 1), ("b", 2)]


def test_syntax_errors_are_skipped(tmp_path):
    make_pkg(tmp_path, "a", {"bad.py": "def (:\n", "ok.py": "import b\n"})
    make_pkg(tmp_path, "b", {})
    assert edges(tmp_path) == {("a", "b")}
