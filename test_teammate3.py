import json
import sys
from pathlib import Path

# Add archguard to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from archguard.ast_scanner import discover_modules, scan_module_imports
from archguard.diff_engine import find_drift

def main():
    repo_root = Path(__file__).parent / "demo_repo"
    contract_file = repo_root / "declared_edges.json"

    print("=" * 60)
    print("ArchGuard Teammate 3 Verification Test")
    print("=" * 60)

    # 1. Discover modules
    modules = discover_modules(str(repo_root))
    print(f"[*] Discovered modules ({len(modules)}): {modules}")

    # 2. Scan actual imports
    actual_records = scan_module_imports(str(repo_root), modules)
    print(f"[*] Scanned actual imports ({len(actual_records)}):")
    for src, dst, rel_path, line in actual_records:
        print(f"    - {src} -> {dst} in {rel_path}:{line}")

    # 3. Load declared edges contract
    with open(contract_file, "r", encoding="utf-8") as f:
        declared_edges = json.load(f)["declared_edges"]
    print(f"[*] Loaded declared contract edges ({len(declared_edges)}): {declared_edges}")

    # 4. Diff engine
    drift = find_drift(declared_edges, actual_records)

    print("\n" + "=" * 60)
    if drift:
        print(f"[FAIL] ARCHITECTURAL DRIFT DETECTED: {len(drift)} undeclared edge(s)")
        for item in drift:
            print(f"    ! {item['source']} -> {item['target']} in {item['file']}:{item['line']}")
        print("=" * 60)
        print("Teammate 3 Done-Condition MET: checkout.py reported before dag_extractor exists!")
        return 1
    else:
        print("[PASS] 0 undeclared edges. Codebase conforms 100% to contract.")
        print("=" * 60)
        return 0

if __name__ == "__main__":
    sys.exit(main())
