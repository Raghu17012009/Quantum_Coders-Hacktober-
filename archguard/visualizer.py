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

    # ── drift_report.html (secondary) ─────────────────────────────────────────
    if is_drift or (has_stale and stale_is_failure):
def generate_drift_assets(
    declared_edges: list[list[str]],
    drift_records: list[dict],
    output_mermaid: str = "drift_report.md",
    output_html: str = "drift_report.html",
    stale_edges: list[dict] | None = None,
) -> str:
    stale_edges = stale_edges or []
    mermaid_code = build_mermaid(declared_edges, drift_records, stale_edges)

    n_drift, n_stale = len(drift_records), len(stale_edges)
    md = ["# ArchGuard Drift Report\n\n"]
    if n_drift:
        noun = "import" if n_drift == 1 else "imports"
        md.append(f"## FAIL — {n_drift} undeclared {noun}\n\n")
        md.append("The code contains a dependency that is not declared in the architecture.\n\n")
        md.append("### Detected Drift\n\n")
        md.append("| Source | Target | File | Line |\n|---|---|---|---:|\n")
        for item in drift_records:
            md.append(
                f"| `{item['source']}` | `{item['target']}` | "
                f"`{item['file']}` | {item['line']} |\n"
            )
        md.append("\n### Architecture\n\n")
        md.append("Solid arrows = declared architecture.<br>\n")
        md.append("Red dashed arrows = undeclared code dependencies.\n\n")
        md.append("Review each dependency and either correct the code or update the architecture contract if intentional.\n\n")
    elif n_stale:
        md.append(f"## FAIL — {n_stale} stale diagram edge(s)\n\n")
        md.append("The architecture declares an edge that is not used by the code.\n\n")
    else:
        md.append("## PASS — 0 undeclared imports\n\n")
        md.append("The code matches the documented architecture.\n\n")
        md.append("## Architecture\n\n")
        md.append("Green solid arrows = declared architecture.\n\n")
    md.append("```mermaid\n")
    md.append(mermaid_code)
    md.append("\n```\n")
    Path(output_mermaid).write_text("".join(md), encoding="utf-8")

    if n_drift or n_stale:
        parts = []
        if n_drift:
            parts.append(f"{n_drift} undeclared import{'s' if n_drift != 1 else ''}")
        if n_stale:
            parts.append(f"{n_stale} stale diagram edge{'s' if n_stale != 1 else ''}")
        header_text = "⚠️ Architectural Drift Detected (" + ", ".join(parts) + ")"
        title_color = "#ef4444"
    elif has_stale:
        title_color = "#f59e0b"
    else:
        title_color = "#22c55e"
    if is_drift:
        header_text = f"⚠️ Architectural Drift Detected — {len(drift_records)} undeclared edge(s)"
        if has_stale:
            header_text += f", {len(stale_edges)} stale edge(s)"
    elif has_stale:
        header_text = f"⚠️ 0 undeclared edges — {len(stale_edges)} stale diagram edge(s)"
    else:
        header_text = "✅ 0 undeclared edges — Codebase conforms to architecture"

    drift_rows = ""
    for item in drift_records:
        source_path = quote(item["file"], safe="/._-")
        drift_rows += (
            f"<tr>"
            f"<td><code>{item['source']}</code></td>"
            f"<td><code>{item['target']}</code></td>"
            f'<td><a href="{source_path}#L{item["line"]}">'
            f"<code>{item['file']}:{item['line']}</code></a></td>"
            f"</tr>\n"
        )

    drift_table = ""
    if drift_rows:
        drift_table = f"""
    <h2>Undeclared Edges</h2>
    <table>
      <tr><th>Source</th><th>Target</th><th>Location</th></tr>
      {drift_rows}
    </table>"""

    stale_rows = "".join(
        f"<tr><td><code>{item['source']}</code></td><td><code>{item['target']}</code></td></tr>\n"
        for item in stale_edges
    )
    stale_table = ""
    if stale_rows:
        stale_table = f"""
    <h2>Stale Diagram Edges</h2>
    <table>
      <tr><th>Source</th><th>Target</th></tr>
      {stale_rows}
    </table>"""

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>ArchGuard — Conformance Report</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({{startOnLoad:true,theme:'base',
    themeVariables:{{primaryColor:'#dbeafe',primaryBorderColor:'#3b82f6',
    primaryTextColor:'#1e40af',edgeLabelBackground:'#f8fafc'}}}});</script>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:system-ui,-apple-system,sans-serif;background:#0f172a;color:#f1f5f9;padding:2rem}}
    .card{{background:#1e293b;border-radius:16px;padding:2rem;max-width:900px;margin:0 auto;box-shadow:0 4px 32px #0008}}
    h1{{color:{title_color};font-size:1.3rem;margin-bottom:1.5rem;padding-bottom:0.75rem;border-bottom:1px solid #334155}}
    h2{{color:#94a3b8;font-size:0.95rem;margin:1.5rem 0 0.5rem;text-transform:uppercase;letter-spacing:.05em}}
    table{{border-collapse:collapse;width:100%;margin-top:0.5rem;font-size:0.875rem}}
    th,td{{padding:0.5rem 0.75rem;border-bottom:1px solid #334155;text-align:left}}
    th{{color:#64748b;font-weight:600}}
    code{{background:#0f172a;padding:2px 6px;border-radius:4px;font-size:0.82rem;color:#93c5fd}}
    .mermaid{{background:#0f172a;padding:1.5rem;border-radius:8px;margin-top:0.5rem}}
    .legend{{display:flex;gap:1.5rem;font-size:0.8rem;color:#94a3b8;margin-bottom:1rem}}
    .legend span{{display:flex;align-items:center;gap:0.4rem}}
  </style>
</head>
<body>
  <div class="card">
    <h1>{header_text}</h1>
    {drift_table}
    {stale_table}
    <h2>Architecture Flow</h2>
    <div class="legend">
      <span>🟢 Declared edge</span>
      {"<span>🔴 Drift edge (undeclared)</span>" if is_drift else ""}
      {"<span>🟠 Drift source module</span>" if is_drift else ""}
      {"<span>🟡 Stale edge (drawn, unused)</span>" if has_stale else ""}
    </div>
    <div class="mermaid">
{mermaid_code}
    </div>
  </div>
</body>
</html>"""

    Path(output_html).write_text(html_content, encoding="utf-8")
    return mermaid_code
