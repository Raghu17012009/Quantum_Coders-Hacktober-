from __future__ import annotations


def _declared_set(declared_edges) -> set[tuple[str, str]]:
    return {tuple(edge) for edge in declared_edges}


def find_drift(
    declared_edges: list[list[str]],
    actual_records: list[tuple[str, str, str, int]],
) -> list[dict]:
    """Undeclared edges: imports in the code that the diagram does not draw.

    Returns a list of dicts with source, target, file, line (one per import site).
    """
    declared = _declared_set(declared_edges)
    return [
        {"source": src, "target": dst, "file": file_path, "line": lineno}
        for src, dst, file_path, lineno in actual_records
        if (src, dst) not in declared
    ]


def find_stale(
    declared_edges: list[list[str]],
    actual_records: list[tuple[str, str, str, int]],
) -> list[dict]:
    """Stale edges: arrows in the diagram with no matching import in the code."""
    actual = {(src, dst) for src, dst, _f, _l in actual_records}
    seen: set[tuple[str, str]] = set()
    stale = []
    for edge in declared_edges:
        key = tuple(edge)
        if key not in actual and key not in seen:
            seen.add(key)
            stale.append({"source": key[0], "target": key[1]})
    return stale
