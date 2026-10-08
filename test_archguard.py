import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from archguard.dag_extractor import extract_declared_edges, normalize_name
from archguard.ast_scanner import scan_module_imports


ROOT = Path(__file__).parent
DEMO_REPO = ROOT / "demo_repo"
CONTRACT = DEMO_REPO / "declared_edges.json"


class ArchGuardIntegrationTests(unittest.TestCase):
    def test_scanner_records_multiple_absolute_imports_and_ignores_relative_imports(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            for module in ("source", "inventory_service", "database"):
                package = repo / module
                package.mkdir()
                (package / "__init__.py").write_text("", encoding="utf-8")
            (repo / "source" / "module.py").write_text(
                "import inventory_service, database\n"
                "from .database import local_only\n",
                encoding="utf-8",
            )
            records = scan_module_imports(
                str(repo), ["source", "inventory_service", "database"]
            )
            self.assertEqual(
                {(source, target) for source, target, _, _ in records},
                {("source", "inventory_service"), ("source", "database")},
            )

    def test_normalize_name(self):
        self.assertEqual(normalize_name(" Order-Service "), "order_service")

    def test_fallback_filters_unknown_edges_and_normalizes_names(self):
        with tempfile.TemporaryDirectory() as directory:
            contract = Path(directory) / "edges.json"
            contract.write_text(
                json.dumps(
                    {
                        "declared_edges": [
                            ["API Gateway", "order-service"],
                            ["unknown", "database"],
                        ]
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                extract_declared_edges(
                    str(DEMO_REPO / "architecture.png"),
                    ["api_gateway", "order_service", "database"],
                    fallback_file=str(contract),
                ),
                [["api_gateway", "order_service"]],
            )

    def test_demo_fails_with_planted_drift(self):
        result = self._run_cli(CONTRACT)
        self.assertEqual(result.returncode, 1)
        self.assertIn("order_service -> database", result.stdout)
        self.assertIn("checkout.py:2", result.stdout)

    def test_demo_passes_when_planted_import_is_removed(self):
        checkout = DEMO_REPO / "order_service" / "checkout.py"
        original = checkout.read_text(encoding="utf-8")
        try:
            checkout.write_text(
                "\n".join(
                    line
                    for line in original.splitlines()
                    if "from database.connection import raw_sql_query" not in line
                )
                + "\n",
                encoding="utf-8",
            )
            result = self._run_cli(CONTRACT)
            self.assertEqual(result.returncode, 0)
            self.assertIn("0 undeclared edges", result.stdout)
        finally:
            checkout.write_text(original, encoding="utf-8")

    @staticmethod
    def _run_cli(contract: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "archguard.cli",
                "check",
                "--diagram",
                str(DEMO_REPO / "architecture.png"),
                "--repo",
                str(DEMO_REPO),
                "--edges",
                str(contract),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )


if __name__ == "__main__":
    unittest.main()
