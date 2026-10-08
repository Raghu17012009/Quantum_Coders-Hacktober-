"""Deterministic Python import scanner (stdlib ast only)."""
from __future__ import annotations

import ast
from pathlib import Path


def discover_modules(repo_root: str | Path) -> list[str]:
    """Top-level directories that contain __init__.py."""
    repo = Path(repo_root)
    if not repo.is_dir():
        return []
    return sorted(
        p.name for p in repo.iterdir() if p.is_dir() and (p / "__init__.py").exists()
    )


_DYNAMIC_IMPORTERS = {"import_module", "__import__"}


def _import_targets(node: ast.AST, pkg_parts: list[str]) -> list[str]:
    """Top-level names a single AST node imports (may be empty)."""
    if isinstance(node, ast.Import):
        return [a.name.split(".")[0] for a in node.names]

    if isinstance(node, ast.ImportFrom):
        if node.level == 0:
            return [node.module.split(".")[0]] if node.module else []
        # Relative import: climb (level - 1) packages from the file's own package.
        up = node.level - 1
        if up < len(pkg_parts):
            return []  # still inside the file's own top-level package
        if up > len(pkg_parts):
            return []  # climbs above the repo root; not resolvable
        # Exactly at the repo root: "from ..other import x" / "from .. import other"
        if node.module:
            return [node.module.split(".")[0]]
        return [a.name for a in node.names if a.name != "*"]

    if isinstance(node, ast.Call):
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if name in _DYNAMIC_IMPORTERS and node.args:
            arg = node.args[0]
            if (
                isinstance(arg, ast.Constant)
                and isinstance(arg.value, str)
                and arg.value
                and not arg.value.startswith(".")
            ):
                return [arg.value.split(".")[0]]
    return []


def scan_module_imports(
    repo_root: str | Path, module_names: list[str]
) -> list[tuple[str, str, str, int]]:
    """Find imports from one listed package into another.

    Returns (source_module, target_module, relative_path, line_number).
    Detected: ``import x``, ``from x import y`` (including ``import x.y as z``),
    relative imports that climb out of the package (``from ..x import y``), and
    ``importlib.import_module("x")`` / ``__import__("x")`` with a literal name.
    Self-imports, unreadable files and syntax errors are ignored.
    """
    edges: list[tuple[str, str, str, int]] = []
    repo = Path(repo_root)
    known = set(module_names)

    for mod in module_names:
        mod_dir = repo / mod
        if not mod_dir.is_dir():
            continue

        for py_file in sorted(mod_dir.rglob("*.py")):
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError, OSError):
                continue

            rel_path = py_file.relative_to(repo)
            pkg_parts = list(rel_path.parts[:-1])
            rel = rel_path.as_posix()
            for node in ast.walk(tree):
                for target in dict.fromkeys(_import_targets(node, pkg_parts)):
                    if target in known and target != mod:
                        edges.append((mod, target, rel, node.lineno))

    edges.sort(key=lambda e: (e[2], e[3], e[1]))
    return edges
