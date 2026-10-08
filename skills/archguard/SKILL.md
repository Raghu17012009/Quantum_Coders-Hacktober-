---
name: archguard
description: >
  Audits a Python repository for architectural drift against a visual architecture
  diagram. Use when checking design boundaries or linting module imports against
  architecture.png. Reports undeclared edges (imports that exist in code but are
  absent from the architecture diagram). Exits 1 on drift, 0 on conformance.
---

# ArchGuard Skill

## When to use this skill

Use ArchGuard when you want to verify that the Python package imports in a
repository match the architecture documented by the repository's diagram
(`architecture.png`).

Trigger on requests like:
- "Check if the code matches the architecture diagram"
- "Find architecture drift"
- "Lint the module imports against the design"
- "Does the code respect the documented boundaries?"

## How to run ArchGuard

### Offline / timed demo (no API key required)

```bash
python -m archguard.cli check \
  --diagram demo_repo/architecture.png \
  --repo ./demo_repo \
  --edges demo_repo/declared_edges.json
```

The `--edges` flag bypasses the Gemma 4 visual extraction and uses the
pre-extracted contract file directly. This always works offline.

### Live Gemma 4 run (requires GEMMA_API_KEY or GOOGLE_API_KEY)

```bash
python -m archguard.cli check \
  --diagram demo_repo/architecture.png \
  --repo ./demo_repo
```

Gemma 4 reads `architecture.png`, identifies the directed edges, and returns
them as structured JSON. The scanner then runs and compares.

## Interpreting results

### Drift detected (exit code 1)

```
⚠️  Architectural drift detected: 1 undeclared edge(s)
   ! order_service -> database in order_service/checkout.py:2
```

Open `drift_report.md` in VS Code Markdown Preview to see the Mermaid diagram
with the dashed red drift arrow highlighted.

### Conformance (exit code 0)

```
✅ 0 undeclared edges. Codebase conforms 100% to architecture.png.
```

## What ArchGuard does NOT do

- It does **not** patch or rewrite code automatically.
- It does **not** forbid edges not shown in the diagram — it only flags them.
- It does **not** suggest an adapter or refactoring strategy.
- It does **not** scan non-Python files.

Stop at the fail, the file, and the red arrow. The human decides what to do next.
