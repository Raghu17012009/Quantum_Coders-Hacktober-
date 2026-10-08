"""Shared edge handling so every source of declared edges is treated identically."""
from __future__ import annotations

import json
from pathlib import Path


def normalize_name(name: str) -> str:
    return name.lower().strip().replace(" ", "_").replace("-", "_")


def normalize_edges(
    raw_edges, module_names
) -> tuple[list[list[str]], list[list[str]]]:
    """Normalize names, drop malformed pairs, self-edges and duplicates.

    Returns (kept, dropped). An edge is dropped when either end is not one of
    ``module_names`` (after normalization) so the diagram can mention external
    boxes (Redis, Stripe...) without producing false findings.
    """
    known = {normalize_name(m) for m in module_names}
    kept: list[list[str]] = []
    dropped: list[list[str]] = []
    for pair in raw_edges or []:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            continue
        u, v = normalize_name(str(pair[0])), normalize_name(str(pair[1]))
        if u == v:
            continue
        if u in known and v in known:
            if [u, v] not in kept:
                kept.append([u, v])
        else:
            dropped.append([u, v])
    return kept, dropped


def load_edges_file(path: str | Path) -> list:
    """Read the raw ``declared_edges`` list from a contract JSON file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object with a 'declared_edges' list")
    edges = data.get("declared_edges", [])
    if not isinstance(edges, list):
        raise ValueError(f"{path}: 'declared_edges' must be a list of [source, target] pairs")
    return edges
