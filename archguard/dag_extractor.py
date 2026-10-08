"""Extract architecture edges from a diagram with Google's Generative AI API."""

import json
import mimetypes
import os
import re
from pathlib import Path
from typing import Any


PROMPT = """\
You are an architectural graph extractor.
Inspect the attached system architecture diagram.
The repository contains these top-level modules:
{module_names}
Extract every directed dependency arrow (caller module to callee module)
where both ends map to one of the listed modules.
Output strictly valid JSON:
{{"declared_edges": [["caller_module", "callee_module"]]}}
No explanation. No markdown fences.
"""


def normalize_name(name: str) -> str:
    """Normalize a diagram label to the repository's module naming convention."""
    return name.lower().strip().replace(" ", "_").replace("-", "_")


def _validate_edges(data: Any, module_names: list[str]) -> list[list[str]]:
    if not isinstance(data, dict) or not isinstance(data.get("declared_edges"), list):
        raise ValueError("Gemma response must contain a 'declared_edges' list")

    known = set(module_names)
    edges: list[list[str]] = []
    for edge in data["declared_edges"]:
        if not isinstance(edge, list) or len(edge) != 2 or not all(
            isinstance(item, str) for item in edge
        ):
            raise ValueError("Each declared edge must be a two-item string list")
        source, target = (normalize_name(item) for item in edge)
        if source in known and target in known:
            edges.append([source, target])
    return edges


def _parse_response(raw: str, module_names: list[str]) -> list[list[str]]:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("Gemma response did not contain a JSON object")
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ValueError("Gemma response contained invalid JSON") from exc
    return _validate_edges(data, module_names)


def _load_fallback(path: Path, module_names: list[str]) -> list[list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid edge contract JSON: {path}") from exc
    return _validate_edges(data, module_names)


def _build_client(api_key: str) -> Any:
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError(
            "The live extractor requires the google-genai package; "
            "install it or use --edges for the offline run."
        ) from exc
    return genai.Client(api_key=api_key)


def extract_declared_edges(
    image_path: str,
    module_names: list[str],
    client: Any = None,
    model_name: str | None = None,
    fallback_file: str | None = None,
) -> list[list[str]]:
    """Return normalized, repository-valid edges from a fallback or live extraction."""
    if fallback_file is not None:
        fallback_path = Path(fallback_file)
        if not fallback_path.is_file():
            raise FileNotFoundError(f"Edge contract does not exist: {fallback_file}")
        edges = _load_fallback(fallback_path, module_names)
        print(f"Extracted declared edges from {fallback_path}: {edges}")
        return edges

    image = Path(image_path)
    if not image.is_file():
        raise FileNotFoundError(f"Architecture diagram does not exist: {image_path}")

    api_key = os.environ.get("GEMMA_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set GEMMA_API_KEY or GOOGLE_API_KEY for live extraction, "
            "or provide --edges for the offline run."
        )
    if client is None:
        client = _build_client(api_key)

    try:
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError(
            "The live extractor requires the google-genai package; "
            "install it or use --edges for the offline run."
        ) from exc

    image_part = types.Part.from_bytes(
        data=image.read_bytes(),
        mime_type=mimetypes.guess_type(image.name)[0] or "image/png",
    )
    response = client.models.generate_content(
        model=model_name or os.environ.get("ARCHGUARD_MODEL", "gemma-3-27b-it"),
        contents=[
            image_part,
            PROMPT.format(module_names=json.dumps(module_names)),
        ],
    )
    raw = getattr(response, "text", None)
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("Gemma returned an empty response")
    edges = _parse_response(raw, module_names)
    print(f"Extracted declared edges from {image_path}: {edges}")
    return edges
