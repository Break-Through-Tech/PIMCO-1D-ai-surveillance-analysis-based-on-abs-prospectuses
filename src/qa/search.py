"""Find the filing passages closest to a question in the embedding index.

Part of the Q/A backend in src/qa/. The command line for this module is
notebooks/search_embeddings.py.
"""

import json
import math
import os
import re
from collections import Counter
from pathlib import Path

import numpy as np
import openai
from openai import OpenAI


ROOT = Path(__file__).parent.parent.parent
EMBEDDINGS_DIR = ROOT / "data" / "embeddings"
# Filters a caller may pass to retrieve(); "year" is read from filing_date.
FILTER_FIELDS = ("company", "asset_type", "year")
# How many passages a search returns (and the answer is based on) by default.
DEFAULT_TOP_K = 10
# "hybrid" merges meaning and keyword rankings; the other two are for testing.
METHODS = ("hybrid", "meaning", "keyword")
# Reciprocal rank fusion: a passage ranked r in a list earns 1 / (RRF_K + r).
RRF_K = 60
# BM25 keyword scoring settings (the usual defaults).
BM25_K1 = 1.5
BM25_B = 0.75
# Words too common to say which passage answers a question.
STOP_WORDS = frozenset(
    "a an the of to in on for by and or is are be was were do does did will may can with as at from "
    "that this it its any all than more less into which what whose who whom how if not no yes approximately".split()
)
# Words, plus numbers and amounts such as "$1,316,861,669.06", "16.18%" and "a-1".
_TOKEN = re.compile(r"[a-z0-9$%][a-z0-9$%.,\-]*[a-z0-9%]|[a-z0-9]")


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


def _tokens(text: str) -> list[str]:
    return [word for word in _TOKEN.findall(str(text).lower()) if word not in STOP_WORDS]


def _meaning_scores(query: str, vectors: np.ndarray, model: str, client: OpenAI | None) -> np.ndarray:
    """Cosine similarity between the query and each of vectors."""
    client = client or openai_client()
    try:
        response = client.embeddings.create(model=model, input=[query])
    except openai.OpenAIError as error:
        raise openai_error(error) from error
    query_vector = np.asarray(response.data[0].embedding, dtype=np.float32)
    if vectors.shape[1] != query_vector.shape[0]:
        raise QAError("The search index doesn't match the embedding model. Rebuild it with embed_chunks.py.")
    return vectors @ normalize(query_vector)


def _keyword_scores(query: str, metadata: list[dict], candidates: np.ndarray) -> np.ndarray:
    """BM25 score of each candidate: rare query words count more than common ones.

    Word rarity is measured across the whole index, not only the candidates.
    """
    documents = [Counter(_tokens(record.get("embed_text") or "")) for record in metadata]
    lengths = np.array([sum(document.values()) for document in documents], dtype=float)
    average_length = max(lengths.mean(), 1.0)
    containing = Counter(word for document in documents for word in document)
    total = len(documents)

    scores = np.zeros(len(candidates))
    for word in set(_tokens(query)):
        if not containing[word]:
            continue
        rarity = math.log(1 + (total - containing[word] + 0.5) / (containing[word] + 0.5))
        for position, index in enumerate(candidates):
            count = documents[index][word]
            if count:
                length_factor = 1 - BM25_B + BM25_B * lengths[index] / average_length
                scores[position] += rarity * count * (BM25_K1 + 1) / (count + BM25_K1 * length_factor)
    return scores


def _rank_points(scores: np.ndarray, matched: np.ndarray | None = None) -> np.ndarray:
    """1 / (RRF_K + rank) for each score, best rank 1; unmatched entries get 0."""
    ranks = np.empty(len(scores))
    ranks[np.argsort(-scores, kind="stable")] = np.arange(1, len(scores) + 1)
    points = 1 / (RRF_K + ranks)
    return points if matched is None else np.where(matched, points, 0.0)


def retrieve(
    query: str,
    *,
    top_k: int = DEFAULT_TOP_K,
    filters: dict | None = None,
    method: str = "hybrid",
    client: OpenAI | None = None,
) -> list[dict]:
    """Return the top_k chunks that best match query, best first.

    method "hybrid" (the default) ranks chunks by meaning and by keywords and
    merges the two rankings by rank (reciprocal rank fusion); "meaning" and
    "keyword" use one ranking only, for testing. Each result's "similarity" is
    its meaning (cosine) similarity, or None for "keyword".

    filters, e.g. {"company": ["TOYOTA"], "year": [2024]}, are applied before
    the search, so top_k results come back whenever at least top_k chunks
    match. Values within one filter are OR'd; different filters are AND'd.
    """
    if top_k < 1:
        raise ValueError("top_k must be positive")
    if method not in METHODS:
        raise ValueError(f"Unknown search method {method!r}; expected one of {METHODS}.")
    vectors, metadata, model = load_index()
    filters = _clean_filters(filters)
    candidates = np.flatnonzero([_matches(record, filters) for record in metadata])
    if len(candidates) == 0:
        return []  # nothing matches, so skip the paid embedding call

    similarity = None
    if method in ("hybrid", "meaning"):
        similarity = _meaning_scores(query, vectors[candidates], model, client)
    if method in ("hybrid", "keyword"):
        keyword = _keyword_scores(query, metadata, candidates)

    if method == "meaning":
        ranking = similarity
    elif method == "keyword":
        ranking = keyword
    else:
        ranking = _rank_points(similarity) + _rank_points(keyword, matched=keyword > 0)

    order = np.argsort(-ranking, kind="stable")[:top_k]
    return [
        {**metadata[candidates[i]], "similarity": float(similarity[i]) if similarity is not None else None}
        for i in order
    ]
