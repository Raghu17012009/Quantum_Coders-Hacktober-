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


def normalize_name(name: str) -> str:
    return name.lower().strip().replace(" ", "_").replace("-", "_")


def _load_fallback(path: str | Path) -> list[list[str]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [[normalize_name(u), normalize_name(v)] for u, v in data.get("declared_edges", [])]


def _parse_model_json(raw: str) -> list:
    """Strip ```json fences / chatter and return the declared_edges list."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"Model did not return JSON:\n{raw}")
    return json.loads(match.group(0)).get("declared_edges", [])


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
        return _load_fallback(fallback_file)

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
    known = {normalize_name(m) for m in module_names}
    edges: list[list[str]] = []
    for pair in _parse_model_json(response.text):
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            continue
        u, v = normalize_name(str(pair[0])), normalize_name(str(pair[1]))
        if u in known and v in known and u != v and [u, v] not in edges:
            edges.append([u, v])
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
