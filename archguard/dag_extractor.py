"""archguard/dag_extractor.py  (Teammate 2)

Turns architecture.png into declared edges [[caller, callee], ...].

Two paths:
  * Offline : --edges declared_edges.json  -> never touches the network.
  * Live    : Gemma 4 reads the PNG via the Gemini API (google-genai SDK).

Env vars (never hardcode keys):
  GEMMA_API_KEY or GOOGLE_API_KEY   API key
  GEMMA_MODEL_ID                    model id from the MLH Gemma quickstart

Quick live test (prints the extracted edges for the demo beat):
  python -m archguard.dag_extractor demo_repo/architecture.png \
      --modules api_gateway order_service inventory_service database
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import sys
from pathlib import Path

from .edges import load_edges_file, normalize_edges, normalize_name  # noqa: F401

# Literal JSON braces are fine here because we use .replace(), not .format().
PROMPT = """
You are an architectural graph extractor.
Inspect the attached system architecture diagram.
The repository contains these top-level modules:
{module_names}
Extract every directed dependency arrow (caller to callee)
where both ends map to one of the listed modules.
Follow arrowheads: the arrow points from caller to callee.
Output strictly valid JSON:
{"declared_edges": [["caller_module", "callee_module"]]}
No explanation. No markdown fences.
"""


def _load_fallback(path: str | Path, module_names) -> list[list[str]]:
    """Offline contract: same normalization and filtering as the live path."""
    kept, dropped = normalize_edges(load_edges_file(path), module_names)
    for u, v in dropped:
        print(
            f"[WARN] ignoring declared edge {u} -> {v}: not a module in the repo",
            file=sys.stderr,
        )
    return kept


def _parse_model_json(raw: str) -> list:
    """Strip ```json fences / chatter and return the declared_edges list."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE)
    decoder = json.JSONDecoder()
    for m in re.finditer(r"\{", raw):
        try:
            obj, _end = decoder.raw_decode(raw, m.start())
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "declared_edges" in obj:
            edges = obj["declared_edges"]
            if not isinstance(edges, list):
                raise ValueError("Model returned 'declared_edges' that is not a list")
            return edges
    raise ValueError(f"Model did not return valid declared_edges JSON:\n{raw[:500]}")


def _make_client():
    api_key = os.environ.get("GEMMA_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMMA_API_KEY or GOOGLE_API_KEY (see .env.example).")
    from google import genai  # lazy: offline runs don't need the SDK installed

    return genai.Client(api_key=api_key)


def extract_declared_edges(
    image_path,
    module_names,
    client=None,
    model_name=None,
    fallback_file=None,
):
    # 1) Offline parachute: if --edges was given, do not call the API.
    if fallback_file and Path(fallback_file).exists():
        return _load_fallback(fallback_file, module_names)

    # 2) Live Gemma vision call.
    model_name = model_name or os.environ.get("GEMMA_MODEL_ID")
    if not model_name:
        raise RuntimeError("Set GEMMA_MODEL_ID to the model id from the MLH Gemma quickstart.")
    client = client or _make_client()

    from google.genai import types

    image_path = Path(image_path)
    mime = mimetypes.guess_type(image_path.name)[0] or "image/png"
    image_part = types.Part.from_bytes(data=image_path.read_bytes(), mime_type=mime)
    prompt = PROMPT.replace("{module_names}", json.dumps(list(module_names)))

    response = client.models.generate_content(
        model=model_name,
        contents=[image_part, prompt],
        config=types.GenerateContentConfig(temperature=0),
    )

    # 3) Parse, normalize, keep only edges whose ends are real folders.
    edges, _dropped = normalize_edges(_parse_model_json(response.text or ""), module_names)
    return edges


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract declared edges from an architecture diagram.")
    ap.add_argument("image")
    ap.add_argument("--modules", nargs="+", required=True)
    ap.add_argument("--edges", help="offline declared_edges.json (skips the API)")
    args = ap.parse_args()

    edges = extract_declared_edges(args.image, args.modules, fallback_file=args.edges)
    source = "offline file" if args.edges else "Gemma 4"
    print(f"Declared edges ({source}):")
    for u, v in edges:
        print(f"  {u} -> {v}")
    print(json.dumps({"declared_edges": edges}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
