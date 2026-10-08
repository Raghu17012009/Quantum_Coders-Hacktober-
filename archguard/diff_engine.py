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
