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


def scan_module_imports(
    repo_root: str | Path, module_names: list[str]
) -> list[tuple[str, str, str, int]]:
    """Find absolute imports from one listed package into another.

    Returns (source_module, target_module, relative_path, line_number).
    Self-imports, relative imports, unreadable files and syntax errors are ignored.
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
            except (SyntaxError, UnicodeDecodeError):
                continue

            rel = py_file.relative_to(repo).as_posix()
            for node in ast.walk(tree):
                targets: list[str] = []
                if isinstance(node, ast.Import):
                    targets = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    # level == 0 means an absolute import; "from .x import y" is skipped.
                    targets = [node.module.split(".")[0]]

                for target in dict.fromkeys(targets):  # de-dupe per line, keep order
                    if target in known and target != mod:
                        edges.append((mod, target, rel, node.lineno))

    edges.sort(key=lambda e: (e[2], e[3], e[1]))
    return edges
