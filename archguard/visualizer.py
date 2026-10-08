from __future__ import annotations

import html
import re
from pathlib import Path

MERMAID_CDN = "https://cdn.jsdelivr.net/npm/mermaid@10.9.3/dist/mermaid.min.js"


def _node_id(name: str) -> str:
    # Prefix so names like "end" / "graph" never collide with Mermaid keywords.
    return "n_" + re.sub(r"\W", "_", name)


def _label(text: str) -> str:
    return text.replace('"', "'")


def build_mermaid(
    declared_edges: list[list[str]],
    drift_records: list[dict],
    stale_edges: list[dict] | None = None,
) -> str:
    """Mermaid flowchart: declared edges solid, stale amber dotted, drift red dashed."""
    stale_pairs = {(s["source"], s["target"]) for s in (stale_edges or [])}

    # One arrow per (source, target); keep the first site and count the rest.
    drift_by_pair: dict[tuple[str, str], list[dict]] = {}
    for item in drift_records:
        drift_by_pair.setdefault((item["source"], item["target"]), []).append(item)

    names: list[str] = []
    for src, dst in declared_edges:
        names += [src, dst]
    for src, dst in drift_by_pair:
        names += [src, dst]
    names = list(dict.fromkeys(names))

    lines = ["flowchart TD"]
    for name in names:
        lines.append(f'    {_node_id(name)}["{_label(name)}"]')

    link_i = 0
    stale_idx: list[int] = []
    drift_idx: list[int] = []

    for src, dst in declared_edges:
        lines.append(f"    {_node_id(src)} --> {_node_id(dst)}")
        if (src, dst) in stale_pairs:
            stale_idx.append(link_i)
        link_i += 1

    for (src, dst), items in drift_by_pair.items():
        first = items[0]
        more = f" (+{len(items) - 1} more)" if len(items) > 1 else ""
        label = _label(f"DRIFT: {first['file']}:{first['line']}{more}")
        lines.append(f'    {_node_id(src)} -.->|"{label}"| {_node_id(dst)}')
        drift_idx.append(link_i)
        link_i += 1

    for idx in stale_idx:
        lines.append(f"    linkStyle {idx} stroke:#f59e0b,stroke-width:3px,stroke-dasharray: 2 4;")
    for idx in drift_idx:
        lines.append(f"    linkStyle {idx} stroke:#ff0000,stroke-width:3px,stroke-dasharray: 5 5;")

    return "\n".join(lines)


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
    else:
        header_text = "✅ 100% Architectural Conformance"
        title_color = "#22c55e"

    details = ""
    if drift_records:
        rows = "".join(
            f"<li><code>{html.escape(r['source'])} → {html.escape(r['target'])}</code> "
            f"in {html.escape(r['file'])}:{r['line']}</li>"
            for r in drift_records
        )
        details += f"<h2>Undeclared imports</h2><ul>{rows}</ul>"
    if stale_edges:
        rows = "".join(
            f"<li><code>{html.escape(s['source'])} → {html.escape(s['target'])}</code> "
            f"is drawn in the diagram but no import was found</li>"
            for s in stale_edges
        )
        details += f"<h2>Stale diagram edges</h2><ul>{rows}</ul>"

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>ArchGuard Conformance Report</title>
  <script src="{MERMAID_CDN}"></script>
  <script>mermaid.initialize({{startOnLoad: true, theme: 'neutral'}});</script>
  <style>
    body {{ font-family: system-ui, -apple-system, sans-serif; padding: 2rem; background: #0f172a; color: #f8fafc; }}
    .card {{ background: #1e293b; border-radius: 12px; padding: 2rem; max-width: 800px; margin: 0 auto; }}
    h1 {{ color: {title_color}; margin-top: 0; }}
    h2 {{ font-size: 1.1rem; margin-top: 1.5rem; }}
    pre.mermaid {{ background: #f8fafc; padding: 1.5rem; border-radius: 8px; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>{header_text}</h1>
    <pre class="mermaid">
{html.escape(mermaid_code, quote=False)}
    </pre>
    {details}
  </div>
</body>
</html>"""

    Path(output_html).write_text(html_content, encoding="utf-8")
    return mermaid_code
