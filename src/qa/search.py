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
# Re-ranking: a model reads the question with each shortlisted passage and
# scores how well the passage answers it; the shortlist is then reordered by
# blending that ranking with the search ranking.
RERANK_MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"
RERANK_MODEL_DIR = ROOT / "data" / "models"
# How many passages the first search hands to the re-ranker (at least top_k).
RERANK_SHORTLIST = 20
# The model reads at most 512 tokens (question included), so each passage is
# scored in overlapping windows and keeps its best window's score.
WINDOW_TOKENS = 400
WINDOW_OVERLAP = 100
_reranker = None  # loaded on first use, then reused


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


class Reranker:
    """Scores passages against a question with a local cross-encoder model."""

    def __init__(self, model_name: str = RERANK_MODEL, cache_dir: Path = RERANK_MODEL_DIR):
        from fastembed.rerank.cross_encoder import TextCrossEncoder
        from tokenizers import Tokenizer

        self.encoder = TextCrossEncoder(model_name, cache_dir=str(cache_dir))
        # A copy of the model's tokenizer that doesn't cut text at 512 tokens,
        # used only to split passages into windows.
        self.tokenizer = Tokenizer.from_str(self.encoder.model.tokenizer.to_str())
        self.tokenizer.no_truncation()
        self.tokenizer.no_padding()

    def windows(self, text: str) -> list[str]:
        """text cut into overlapping windows of up to WINDOW_TOKENS tokens."""
        spans = self.tokenizer.encode(text, add_special_tokens=False).offsets
        return window_texts(text, spans)

    def scores(self, query: str, texts: list[str]) -> list[float]:
        return [float(score) for score in self.encoder.rerank(query, texts)]


def window_texts(text: str, spans: list[tuple[int, int]]) -> list[str]:
    """Slices of text covering WINDOW_TOKENS tokens each, overlapping by
    WINDOW_OVERLAP; spans are each token's (start, end) character positions."""
    if not spans:
        return [text]
    step = WINDOW_TOKENS - WINDOW_OVERLAP
    windows = []
    for first in range(0, len(spans), step):
        last = min(first + WINDOW_TOKENS, len(spans)) - 1
        windows.append(text[spans[first][0]:spans[last][1]])
        if last == len(spans) - 1:
            break
    return windows


def get_reranker() -> Reranker:
    """The re-ranking model, loaded (and downloaded the first time) on first use."""
    global _reranker
    if _reranker is None:
        try:
            _reranker = Reranker()
        except ImportError as error:
            raise QAError(
                "Re-ranking needs the fastembed package. Run pip install -r requirements.txt."
            ) from error
        except Exception as error:  # download or file problems; fastembed has no single error type
            raise QAError(
                "Couldn't load the re-ranking model. Check the internet connection and try again."
            ) from error
    return _reranker


def _rerank(query: str, records: list[dict], reranker: Reranker) -> list[dict]:
    """records (in search order, best first) reordered by blending the search
    ranking with the re-ranking model's ranking.

    Each record scores its best window; each ranking then gives it
    1 / (RRF_K + rank) points, and the two are added. A record ranked high by
    either keeps a high place, so pages the search finds by exact numbers or
    terms aren't pushed out by the model.
    """
    windows = [reranker.windows(record.get("embed_text") or "") for record in records]
    flat = reranker.scores(query, [window for group in windows for window in group])
    best, start = [], 0
    for group in windows:
        best.append(max(flat[start:start + len(group)]))
        start += len(group)
    search_points = _rank_points(-np.arange(len(records), dtype=float))  # already in search order
    blended = search_points + _rank_points(np.array(best))
    order = np.argsort(-blended, kind="stable")  # ties keep search order
    return [{**records[i], "rerank_score": best[i]} for i in order]


def retrieve(
    query: str,
    *,
    top_k: int = DEFAULT_TOP_K,
    filters: dict | None = None,
    method: str = "hybrid",
    rerank: bool = True,
    client: OpenAI | None = None,
) -> list[dict]:
    """Return the top_k chunks that best match query, best first.

    method "hybrid" (the default) ranks chunks by meaning and by keywords and
    merges the two rankings by rank (reciprocal rank fusion); "meaning" and
    "keyword" use one ranking only, for testing. Each result's "similarity" is
    its meaning (cosine) similarity, or None for "keyword".

    rerank=True (the default) takes the best RERANK_SHORTLIST chunks (or
    top_k, if larger), has the re-ranking model score each against the
    query, and returns the top_k after blending the search ranking with the
    model's ranking (see _rerank). Each result's "rerank_score" is the
    model's score (higher is better), or None when not re-ranked;
    rerank=False is for testing.

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

    keep = max(top_k, RERANK_SHORTLIST) if rerank else top_k
    order = np.argsort(-ranking, kind="stable")[:keep]
    results = [
        {
            **metadata[candidates[i]],
            "similarity": float(similarity[i]) if similarity is not None else None,
            "rerank_score": None,
        }
        for i in order
    ]
    if rerank:
        results = _rerank(query, results, get_reranker())
    return results[:top_k]
