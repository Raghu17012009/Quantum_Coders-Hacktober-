from pathlib import Path

def generate_drift_assets(
    declared_edges: list[list[str]], 
    drift_records: list[dict], 
    output_mermaid: str = "drift_report.mermaid", 
    output_html: str = "drift_report.html"
) -> str:
    lines = ["flowchart TD"]
    link_i = 0
    drift_idx = []

    # 1. Declared edges (Green / Solid)
    for src, dst in declared_edges:
        lines.append(f"    {src} --> {dst}")
        link_i += 1

    # 2. Undeclared drift edges (Red / Dashed)
    for item in drift_records:
        lines.append(f"    {item['source']} -.->|DRIFT: line {item['line']}| {item['target']}")
        drift_idx.append(link_i)
        link_i += 1

    # 3. Apply style strictly to drift link indices
    for idx in drift_idx:
        lines.append(f"    linkStyle {idx} stroke:#ff0000,stroke-width:3px,stroke-dasharray: 5 5;")

    mermaid_code = "\n".join(lines)

    # 4. Save raw Mermaid file (renderable in VS Code Markdown Preview)
    Path(output_mermaid).write_text(f"```mermaid\n{mermaid_code}\n```\n", encoding="utf-8")

    # 5. Dual Pass/Fail HTML viewer
    is_drift = len(drift_records) > 0
    title_color = "#ef4444" if is_drift else "#22c55e"
    header_text = (
        f"⚠️ Architectural Drift Detected ({len(drift_records)} undeclared edge)"
        if is_drift else "✅ 100% Architectural Conformance"
    )
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <title>ArchGuard Conformance Report</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({{startOnLoad: true, theme: 'neutral'}});</script>
  <style>
    body {{ font-family: system-ui, -apple-system, sans-serif; padding: 2rem; background: #0f172a; color: #f8fafc; }}
    .card {{ background: #1e293b; border-radius: 12px; padding: 2rem; max-width: 800px; margin: 0 auto; }}
    h1 {{ color: {title_color}; margin-top: 0; }}
    pre.mermaid {{ background: #0f172a; padding: 1.5rem; border-radius: 8px; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>{header_text}</h1>
    <pre class="mermaid">
{mermaid_code}
    </pre>
  </div>
</body>
</html>"""

    Path(output_html).write_text(html_content, encoding="utf-8")
    return mermaid_code
