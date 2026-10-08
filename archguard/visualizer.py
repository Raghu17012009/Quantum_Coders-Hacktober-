from pathlib import Path
from urllib.parse import quote


def generate_drift_assets(
    declared_edges: list[list[str]],
    drift_records: list[dict],
    output_md: str = "drift_report.md",
    output_html: str = "drift_report.html",
    stale_edges: list[dict] | None = None,
    stale_is_failure: bool = True,
) -> str:
    """
    Generate drift_report.md (required) and drift_report.html (secondary).

    Mermaid linkStyle indices are assigned in the order links are declared:
      - indices 0..(N_declared-1)  → solid declared arrows  (green)
      - indices N_declared..end    → dashed red drift arrows

    Parameters
    ----------
    declared_edges : list of [source, target] pairs from the architecture contract
    drift_records  : list of dicts {source, target, file, line}
    output_md      : path for the Markdown report (VS Code previewable, offline)
    output_html    : path for the optional HTML report
    stale_edges    : declared edges no import uses, list of dicts {source, target};
                     drawn as amber dotted arrows
    stale_is_failure : False when stale edges are only warnings (--allow-stale)
    """
    is_drift = len(drift_records) > 0
    stale_edges = stale_edges or []
    has_stale = len(stale_edges) > 0
    stale_pairs = {(item["source"], item["target"]) for item in stale_edges}

    # ── Collect all node names so we can style them individually ─────────────
    declared_nodes: list[str] = []
    for src, dst in declared_edges:
        if src not in declared_nodes:
            declared_nodes.append(src)
        if dst not in declared_nodes:
            declared_nodes.append(dst)

    drift_sources = {item["source"] for item in drift_records}

    # ── Build Mermaid lines ───────────────────────────────────────────────────
    lines = ["flowchart TD"]

    # Node label aliases  (box with icon prefix)
    for node in declared_nodes:
        icon = "🔴 " if node in drift_sources else ""
        lines.append(f'    {node}["{icon}{node}"]')

    link_i = 0
    drift_idx = []
    declared_idx = []
    stale_idx = []

    for src, dst in declared_edges:
        lines.append(f"    {src} --> {dst}")
        if (src, dst) in stale_pairs:
            stale_idx.append(link_i)
        else:
            declared_idx.append(link_i)
        link_i += 1

    if drift_records:
        drawn_pairs: set[tuple[str, str]] = set()
        for item in drift_records:
            pair = (item["source"], item["target"])
            if pair in drawn_pairs:
                continue  # one arrow per pair; every import site is still listed in the table
            drawn_pairs.add(pair)
            lines.append(
                f'    {item["source"]} -.->|"DRIFT"| {item["target"]}'
            )
            drift_idx.append(link_i)
            link_i += 1

    # ── Node styles ───────────────────────────────────────────────────────────
    for node in declared_nodes:
        if node in drift_sources:
            lines.append(
                f"    style {node} fill:#fef3c7,stroke:#d97706,stroke-width:3px,"
                f"color:#92400e,font-weight:bold"
            )
        else:
            lines.append(
                f"    style {node} fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e40af"
            )

    for idx in declared_idx:
        lines.append(
            f"    linkStyle {idx} stroke:#22c55e,stroke-width:2.5px;"
        )
    for idx in stale_idx:
        lines.append(
            f"    linkStyle {idx} stroke:#f59e0b,stroke-width:3px,"
            f"stroke-dasharray:2 4;"
        )
    for idx in drift_idx:
        lines.append(
            f"    linkStyle {idx} stroke:#ef4444,stroke-width:3px,"
            f"stroke-dasharray:8 4;"
        )

    mermaid_code = "\n".join(lines)

    # ── drift_report.md ───────────────────────────────────────────────────────
    md = ["# ArchGuard Drift Report\n\n"]
    if is_drift:
        noun = "import" if len(drift_records) == 1 else "imports"
        md.append(f"## FAIL — {len(drift_records)} undeclared {noun}\n\n")
        md.append("The code contains a dependency that is not declared in the architecture.\n\n")
        md.append("### Detected Drift\n\n")
        md.append("| Source | Target | File | Line |\n")
        md.append("|---|---|---|---:|\n")
        for item in drift_records:
            source_path = quote(item["file"], safe="/._-")
            md.append(
                f"| `{item['source']}` | `{item['target']}` "
                f"| [{item['file']}]({source_path}#L{item['line']}) "
                f"| {item['line']} |\n"
            )
        md.append("\n### Architecture\n\n")
        md.append("Solid arrows = declared architecture.<br>\n")
        md.append("Red dashed arrows = undeclared code dependencies.")
        md.append("<br>\nAmber dotted arrows = stale edges (drawn, no import found).\n\n" if has_stale else "\n\n")
        md.append("### Source Location\n\n")
        for item in drift_records:
            source_path = quote(item["file"], safe="/._-")
            md.append(
                f"[{item['file']}:{item['line']}]"
                f"({source_path}#L{item['line']})\n\n"
            )
        md.append(
            "Review each dependency and either correct the code or update the "
            "architecture contract if it is intentional.\n\n"
        )
    elif has_stale:
        level = "FAIL" if stale_is_failure else "WARN"
        noun = "edge" if len(stale_edges) == 1 else "edges"
        md.append(f"## {level} — 0 undeclared imports, {len(stale_edges)} stale {noun}\n\n")
        md.append("## Architecture\n\n")
        md.append("Green solid arrows = declared architecture and used by the code.<br>\n")
        md.append("Amber dotted arrows = stale edges (drawn, no import found).\n\n")
    else:
        md.append("## PASS — 0 undeclared imports\n\n")
        md.append("The code matches the documented architecture.\n\n")
        md.append("## Architecture\n\n")
        md.append("Green solid arrows = declared architecture.\n\n")

    if has_stale:
        md.append("### Stale Diagram Edges\n\n")
        md.append("These arrows are drawn in the diagram but no import in the code uses them.\n\n")
        md.append("| Source | Target |\n")
        md.append("|---|---|\n")
        for item in stale_edges:
            md.append(f"| `{item['source']}` | `{item['target']}` |\n")
        md.append("\n")

    md.append("```mermaid\n")
    md.append(mermaid_code)
    md.append("\n```\n")

    Path(output_md).write_text("".join(md), encoding="utf-8")

    title = (
        f"Architectural Drift Detected — {len(drift_records)} undeclared edge(s)"
        if is_drift
        else "0 undeclared edges — Codebase conforms to architecture"
    )
    rows = "".join(
        f"<li><code>{item['source']} → {item['target']}</code> "
        f"in <code>{item['file']}:{item['line']}</code></li>"
        for item in drift_records
    )
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>ArchGuard Report</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.3/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true}});</script></head>
<body><main><h1>{title}</h1>
{"<h2>Undeclared imports</h2><ul>" + rows + "</ul>" if rows else ""}
<div class="mermaid">{mermaid_code}</div>
</main></body></html>"""
    Path(output_html).write_text(html_content, encoding="utf-8")
    return mermaid_code
