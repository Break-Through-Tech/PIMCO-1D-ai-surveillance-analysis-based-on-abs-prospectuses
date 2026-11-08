"""Find the filing passages closest to a question in the embedding index.

Part of the Q/A backend in src/qa/. The command line for this module is
notebooks/search_embeddings.py.
"""

import json
import os
from pathlib import Path

import numpy as np
import openai
from openai import OpenAI


ROOT = Path(__file__).parent.parent.parent
EMBEDDINGS_DIR = ROOT / "data" / "embeddings"
# Filters a caller may pass to retrieve(); "year" is read from filing_date.
FILTER_FIELDS = ("company", "asset_type", "year")


class QAError(Exception):
    """A problem the user can be told about, with a plain-language message."""


def normalize(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector, axis=-1, keepdims=True)
    return vector / np.maximum(norm, 1e-12)


def load_metadata() -> list[dict]:
    path = EMBEDDINGS_DIR / "metadata.jsonl"
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_index() -> tuple[np.ndarray, list[dict], str]:
    """Load (normalized vectors, metadata, embedding model) from EMBEDDINGS_DIR."""
    try:
        vectors = np.load(EMBEDDINGS_DIR / "vectors.npy")
        metadata = load_metadata()
        manifest = json.loads((EMBEDDINGS_DIR / "manifest.json").read_text(encoding="utf-8"))
        model = manifest["model"]
    except FileNotFoundError as error:
        raise QAError("The search index hasn't been built yet. Run embed_chunks.py first.") from error
    except (ValueError, KeyError) as error:
        raise QAError("The search index is damaged. Rebuild it with embed_chunks.py.") from error
    if len(vectors) != len(metadata):
        raise QAError("The search index is damaged. Rebuild it with embed_chunks.py.")
    return normalize(vectors), metadata, model


def openai_client() -> OpenAI:
    if not os.getenv("OPENAI_API_KEY"):
        raise QAError("The OpenAI API key isn't set.")
    return OpenAI()


def openai_error(error: openai.OpenAIError) -> QAError:
    """Turn an OpenAI failure into a plain-language QAError; raise it from error."""
    if isinstance(error, openai.AuthenticationError):
        return QAError("OpenAI rejected the API key. Check OPENAI_API_KEY.")
    if isinstance(error, openai.RateLimitError):
        return QAError("OpenAI is limiting requests right now. Please wait a moment and try again.")
    return QAError("Couldn't reach OpenAI. Please try again.")


def _filter_value(record: dict, field: str) -> str | None:
    value = record.get("filing_date") if field == "year" else record.get(field)
    if not isinstance(value, str) or not value:
        return None  # missing values come through as None or NaN
    return value[:4] if field == "year" else value


def _clean_filters(filters: dict | None) -> dict[str, set[str]]:
    """Drop empty filters and turn each one into a set of strings."""
    cleaned = {}
    for field, allowed in (filters or {}).items():
        if field not in FILTER_FIELDS:
            raise ValueError(f"Unknown filter {field!r}; expected one of {FILTER_FIELDS}.")
        if allowed is None or allowed == []:
            continue
        if isinstance(allowed, (str, int)):
            allowed = [allowed]
        cleaned[field] = {str(value) for value in allowed}
    return cleaned


def _matches(record: dict, filters: dict[str, set[str]]) -> bool:
    # A record with a missing value never matches that filter.
    return all(_filter_value(record, field) in allowed for field, allowed in filters.items())


def filter_options() -> dict[str, list]:
    """The values present in the index for each filter, for building a sidebar."""
    _, metadata, _ = load_index()
    options = {}
    for field in FILTER_FIELDS:
        values = {_filter_value(record, field) for record in metadata} - {None}
        options[field] = sorted(int(v) for v in values) if field == "year" else sorted(values)
    return options


def retrieve(
    query: str,
    *,
    top_k: int = 5,
    filters: dict | None = None,
    client: OpenAI | None = None,
) -> list[dict]:
    """Return the top_k chunks most similar to query, best first.

    filters, e.g. {"company": ["TOYOTA"], "year": [2024]}, are applied before
    the similarity search, so top_k results come back whenever at least top_k
    chunks match. Values within one filter are OR'd; different filters are AND'd.
    """
    if top_k < 1:
        raise ValueError("top_k must be positive")
    vectors, metadata, model = load_index()
    filters = _clean_filters(filters)
    candidates = np.flatnonzero([_matches(record, filters) for record in metadata])
    if len(candidates) == 0:
        return []  # nothing matches, so skip the paid embedding call

    client = client or openai_client()
    try:
        response = client.embeddings.create(model=model, input=[query])
    except openai.OpenAIError as error:
        raise openai_error(error) from error
    query_vector = np.asarray(response.data[0].embedding, dtype=np.float32)
    if vectors.shape[1] != query_vector.shape[0]:
        raise QAError("The search index doesn't match the embedding model. Rebuild it with embed_chunks.py.")

    scores = vectors[candidates] @ normalize(query_vector)
    order = np.argsort(scores)[::-1][:top_k]
    return [{**metadata[candidates[i]], "similarity": float(scores[i])} for i in order]
