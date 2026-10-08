---
name: archguard
description: Audits a repo for architectural drift against a visual architecture diagram. Use when checking design boundaries or linting module imports against architecture.png.
---

# ArchGuard

ArchGuard treats the architecture diagram as the contract. It compares the arrows in the diagram with the real imports between top-level packages and reports any import the diagram does not draw.

## When to use

Use this skill when the user asks to verify, audit, or lint the architecture or module boundaries against `architecture.png`.

## Steps

1. Find the diagram: `demo_repo/architecture.png` (otherwise look in the repo root or `docs/`).
2. Run this command from the repository root. Do not reimplement the scan yourself:

```bash
python -m archguard.cli check --diagram demo_repo/architecture.png --repo ./demo_repo --edges demo_repo/declared_edges.json
```

3. Exit code 1: architectural drift was found. Report each line printed in the form `source -> target file:line`, then open `drift_report.md`, where the undeclared edge is the dashed red arrow.
4. Exit code 0: tell the user the code matches the diagram (`0 undeclared edges`).
5. Exit code 2: the check could not run (missing file or bad input). Report the error message and stop.

## Rules

- An undeclared edge means the code imports a module the diagram did not draw. A missing arrow is not a stated ban, so do not call it a forbidden or illegal dependency.
- Do not invent edges, severities, or rules that the diagram does not show.
- Do not patch, edit, or suggest adapters for the code. Stop at the fail, the file and line, and the report.
- To read the diagram live with Gemma 4 instead of the checked-in contract, omit `--edges` and set `GEMMA_API_KEY` and `GEMMA_MODEL_ID` in the environment. Never print or commit these values.
