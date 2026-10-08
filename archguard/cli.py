import argparse
import json
import sys
from pathlib import Path

from .ast_scanner import discover_modules, scan_module_imports
from .diff_engine import find_drift
from .visualizer import generate_drift_assets


def main():
    parser = argparse.ArgumentParser(
        description="ArchGuard: Visual Architecture Linter & Conformance Engine"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser(
        "check", help="Verify architecture conformance against a diagram or contract"
    )
    check_parser.add_argument(
        "--diagram",
        type=str,
        default="demo_repo/architecture.png",
        help="Path to architecture diagram image"
    )
    check_parser.add_argument(
        "--repo",
        type=str,
        required=True,
        help="Root path of the repository to scan"
    )
    check_parser.add_argument(
        "--edges",
        type=str,
        default=None,
        help="Path to pre-extracted/cached declared_edges.json (offline fallback)"
    )
    check_parser.add_argument(
        "--output-md",
        type=str,
        default="drift_report.md",
        help="Path for generated Mermaid markdown report"
    )
    check_parser.add_argument(
        "--output-html",
        type=str,
        default="drift_report.html",
        help="Path for generated HTML visual report"
    )

    args = parser.parse_args()

    if args.command == "check":
        repo_path = Path(args.repo)
        if not repo_path.is_dir():
            print(f"[ERROR] Target repository directory does not exist: {args.repo}", file=sys.stderr)
            sys.exit(2)

        # 1. Discover modules
        modules = discover_modules(str(repo_path))
        if not modules:
            print(f"[ERROR] No top-level Python modules with __init__.py found in {args.repo}", file=sys.stderr)
            sys.exit(2)

        # 2. Extract declared edges
        if args.edges and Path(args.edges).exists():
            with open(args.edges, "r", encoding="utf-8") as f:
                declared_edges = json.load(f).get("declared_edges", [])
        else:
            try:
                from .dag_extractor import extract_declared_edges
                declared_edges = extract_declared_edges(args.diagram, modules)
            except (ImportError, Exception) as e:
                print(f"[ERROR] Gemma 4 API bridge failed ({e}). Provide --edges <contract.json> for offline fallback.", file=sys.stderr)
                sys.exit(2)

        # 3. Scan imports
        actual_records = scan_module_imports(str(repo_path), modules)

        # 4. Detect drift
        drift = find_drift(declared_edges, actual_records)

        # 5. Generate visual reports
        generate_drift_assets(declared_edges, drift, args.output_md, args.output_html)

        # 6. Report and exit codes
        if drift:
            print(f"⚠️  Architectural drift detected: {len(drift)} undeclared edge(s)")
            for item in drift:
                print(f"   ! {item['source']} -> {item['target']} in {item['file']}:{item['line']}")
            print(f"\nReports generated: {args.output_md}, {args.output_html}")
            sys.exit(1)
        else:
            print(f"✅ 0 undeclared edges. Codebase conforms 100% to {Path(args.diagram).name}.")
            print(f"Reports generated: {args.output_md}, {args.output_html}")
            sys.exit(0)


if __name__ == "__main__":
    main()
