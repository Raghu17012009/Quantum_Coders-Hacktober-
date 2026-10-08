from pathlib import Path
import ast


def discover_modules(repo_root: str) -> list[str]:
    """
    Discovers top-level Python modules by scanning for directories containing __init__.py.
    """
    repo = Path(repo_root)
    if not repo.is_dir():
        return []
    return sorted([
        p.name for p in repo.iterdir()
        if p.is_dir() and (p / "__init__.py").exists()
    ])


def scan_module_imports(repo_root: str, module_names: list[str]) -> list[tuple[str, str, str, int]]:
    """
    Walk each top-level package. Parse every .py file with ast.
    Record Import and ImportFrom whose first segment is another listed package.
    Ignore self-imports and syntax errors.
    Returns: list of (source_module, target_module, rel_path, line_number)
    """
    edges = []
    repo = Path(repo_root)

    for mod in module_names:
        mod_dir = repo / mod
        if not mod_dir.is_dir():
            continue

        for py_file in mod_dir.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                targets = []
                if isinstance(node, ast.Import):
                    targets = [a.name.split(".")[0] for a in node.names]
                elif (
                    isinstance(node, ast.ImportFrom)
                    and node.level == 0
                    and node.module
                ):
                    targets = [node.module.split(".")[0]]

                for target in targets:
                    if target in module_names and target != mod:
                        rel = py_file.relative_to(repo).as_posix()
                        edges.append((mod, target, rel, node.lineno))

    return edges
