import argparse
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows (avoids cp1252 crash with emoji)
# Keep status output reliable on Windows consoles using a legacy code page.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from .ast_scanner import discover_modules, scan_module_imports
from .diff_engine import find_drift, find_stale
from .visualizer import generate_drift_assets


def main(argv=None) -> int:
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
    check_parser.add_argument(
        "--interactive",
        action="store_true",
        help="Ask whether each drift is intentional after generating reports"
    )
    check_parser.add_argument(
        "--allow-stale",
        action="store_true",
        help="Report stale diagram edges (drawn but unused) as warnings instead of failures"
    )

    args = parser.parse_args(argv)

    if args.command == "check":
        repo_path = Path(args.repo)
        if not repo_path.is_dir():
            print(f"[ERROR] Target repository directory does not exist: {args.repo}", file=sys.stderr)
            return 2

        # 1. Discover modules
        modules = discover_modules(str(repo_path))
        if not modules:
            print(f"[ERROR] No top-level Python modules with __init__.py found in {args.repo}", file=sys.stderr)
            return 2

        # 2. Extract declared edges
        try:
            from .dag_extractor import extract_declared_edges
            declared_edges = extract_declared_edges(
                args.diagram,
                modules,
                fallback_file=args.edges,
            )
        except (FileNotFoundError, ImportError, OSError, RuntimeError, ValueError) as exc:
            print(f"[ERROR] Unable to extract declared edges: {exc}", file=sys.stderr)
            return 2

        # 3. Scan imports
        actual_records = scan_module_imports(str(repo_path), modules)

        # 4. Detect drift (undeclared imports) and stale edges (drawn but unused)
        drift = find_drift(declared_edges, actual_records)
        stale = find_stale(declared_edges, actual_records)
        stale_fails = bool(stale) and not args.allow_stale

        # 5. Generate visual reports
        generate_drift_assets(
            declared_edges,
            drift,
            args.output_md,
            args.output_html,
            stale_edges=stale,
            stale_is_failure=not args.allow_stale,
        )

        # 6. Report and exit codes
        if drift:
            print(f"⚠️  Architectural drift detected: {len(drift)} undeclared edge(s)")
            for item in drift:
                print(f"   ! {item['source']} -> {item['target']} in {item['file']}:{item['line']}")
            if stale:
                _print_stale(stale, args.allow_stale)
            print(f"\nReports generated: {args.output_md}, {args.output_html}")
            if args.interactive:
                print("\nReview decision: is this dependency intentional?")
                print("  y = architecture changed; update the contract manually")
                print("  n = code should be corrected")
                answer = input("Choose [y/n]: ").strip().lower()
                if answer in {"y", "yes"}:
                    print("Decision recorded: review and update the architecture contract manually.")
                elif answer in {"n", "no"}:
                    print("Decision recorded: review and correct the source import manually.")
                else:
                    print("No decision recorded. Re-run with --interactive and choose y or n.")
            return 1
        elif stale:
            _print_stale(stale, args.allow_stale)
            print(f"\nReports generated: {args.output_md}, {args.output_html}")
            return 1 if stale_fails else 0
        else:
            print(f"✅ 0 undeclared edges. Codebase conforms 100% to {Path(args.diagram).name}.")
            print(f"Reports generated: {args.output_md}, {args.output_html}")
            return 0

    return 2


def _print_stale(stale: list[dict], allowed: bool) -> None:
    label = "warning" if allowed else "stale"
    print(f"⚠️  {len(stale)} stale diagram edge(s) ({label}): drawn in the diagram but no import found")
    for item in stale:
        print(f"   ~ {item['source']} -> {item['target']}")


if __name__ == "__main__":
    sys.exit(main())
