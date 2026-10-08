def find_drift(declared_edges: list[list[str]], actual_records: list[tuple[str, str, str, int]]) -> list[dict]:
    """
    Find undeclared edges between declared diagram edges and actual import records.
    Returns: list of dicts with source, target, file, line.
    """
    declared = {tuple(edge) for edge in declared_edges}
    drift = []

    for src, dst, file_path, lineno in actual_records:
        if (src, dst) not in declared:
            drift.append({
                "source": src,
                "target": dst,
                "file": file_path,
                "line": lineno,
            })

    return drift


def find_stale(declared_edges: list[list[str]], actual_records: list[tuple[str, str, str, int]]) -> list[dict]:
    """
    Find stale edges: arrows declared in the diagram that no import in the code uses.
    Returns: list of dicts with source and target.
    """
    actual = {(src, dst) for src, dst, _file, _line in actual_records}
    seen: set[tuple[str, str]] = set()
    stale = []
    for edge in declared_edges:
        key = tuple(edge)
        if key not in actual and key not in seen:
            seen.add(key)
            stale.append({"source": key[0], "target": key[1]})
    return stale
