import argparse
import sys
from pathlib import Path

# Keep status output reliable on Windows consoles using a legacy code page.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from .ast_scanner import discover_modules, scan_module_imports
from .diff_engine import find_drift, find_stale
from .visualizer import generate_drift_assets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ArchGuard: Visual Architecture Linter & Conformance Engine"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser(
        "check", help="Verify architecture conformance against a diagram or contract"
    )
    check.add_argument(
        "--diagram",
        type=str,
        default="demo_repo/architecture.png",
        help="Path to architecture diagram image",
    )
    check.add_argument(
        "--repo", type=str, required=True, help="Root path of the repository to scan"
    )
    check.add_argument(
        "--edges",
        type=str,
        default=None,
        help="Path to pre-extracted/cached declared_edges.json (offline fallback)",
    )
    check.add_argument(
        "--output-md",
        type=str,
        default="drift_report.md",
        help="Path for generated Mermaid markdown report",
    )
    check.add_argument(
        "--output-html",
        type=str,
        default="drift_report.html",
        help="Path for generated HTML visual report",
    )
    check.add_argument(
        "--allow-stale",
        action="store_true",
        help="Report stale diagram edges (drawn but unused) as warnings instead of failures",
    )
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    repo_path = Path(args.repo)
    if not repo_path.is_dir():
        print(f"[ERROR] Target repository directory does not exist: {args.repo}", file=sys.stderr)
        return 2

    # 1. Discover modules
    modules = discover_modules(str(repo_path))
    if not modules:
        print(
            f"[ERROR] No top-level Python modules with __init__.py found in {args.repo}",
            file=sys.stderr,
        )
        return 2

    # 2. Declared edges: one code path for both the offline contract and the live model.
    if args.edges and not Path(args.edges).is_file():
        print(f"[ERROR] --edges file not found: {args.edges}", file=sys.stderr)
        return 2
    try:
        from .dag_extractor import extract_declared_edges

        declared_edges = extract_declared_edges(
            args.diagram, modules, fallback_file=args.edges
        )
    except Exception as e:
        if args.edges:
            print(f"[ERROR] Could not read --edges file {args.edges}: {e}", file=sys.stderr)
        else:
            print(
                f"[ERROR] Live diagram extraction failed ({e}). "
                "Provide --edges <contract.json> to run offline.",
                file=sys.stderr,
            )
        return 2

    # 3. Scan imports
    actual_records = scan_module_imports(str(repo_path), modules)

    # 4. Compare
    drift = find_drift(declared_edges, actual_records)
    stale = find_stale(declared_edges, actual_records)

    # 5. Reports
    generate_drift_assets(
        declared_edges, drift, args.output_md, args.output_html, stale_edges=stale
    )

    # 6. Output and exit codes
    failing = bool(drift) or (bool(stale) and not args.allow_stale)
    if drift:
        print(f"⚠️  Architectural drift detected: {len(drift)} undeclared import(s)")
        for item in drift:
            print(f"   ! {item['source']} -> {item['target']} in {item['file']}:{item['line']}")
    if stale:
        label = "warning" if args.allow_stale else "stale"
        print(f"⚠️  {len(stale)} stale diagram edge(s) ({label}): drawn but no import found")
        for item in stale:
            print(f"   ~ {item['source']} -> {item['target']}")

    if not drift and not stale:
        print(f"✅ 0 undeclared edges, 0 stale edges. Codebase conforms 100% to {Path(args.diagram).name}.")
    print(f"\nReports generated: {args.output_md}, {args.output_html}")
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
