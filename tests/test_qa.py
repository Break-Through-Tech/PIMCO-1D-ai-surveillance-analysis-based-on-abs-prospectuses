"""Tests for the Q/A backend in src/qa/.

They use a fake OpenAI client and a tiny index in a temporary folder, so they
need no API key and no real embeddings. Run from the repository root:

    python -m unittest tests/test_qa.py
"""

import json
import math
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np
import openai

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.qa import search
from src.qa.search import QAError


# (chunk_id, company, asset_type, filing_date, vector). With the query vector
# [1, 0, 0] the similarity order is t1, x1, f1, t2, b1, f2, w1.
RECORDS = [
    ("t1", "TOYOTA", "auto_loans", "2024-04-18", [1.0, 0.0, 0.0]),
    ("f1", "FORD", "auto_loans", "2024-03-11", [0.9, 0.1, 0.0]),
    ("t2", "TOYOTA", "auto_loans", "2025-01-15", [0.8, 0.2, 0.0]),
    ("b1", "BMW", "auto_leases", "2025-05-29", [0.7, 0.3, 0.0]),
    ("f2", "FORD", "auto_loans", "2025-09-18", [0.6, 0.4, 0.0]),
    ("w1", "WELLS_FARGO", "cmbs", "2026-02-11", [0.0, 1.0, 0.0]),
    # Missing metadata comes through as NaN, as in the real index.
    ("x1", math.nan, math.nan, math.nan, [0.95, 0.05, 0.0]),
]
QUERY_VECTOR = [1.0, 0.0, 0.0]


def openai_failure(error_class, message):
    """An OpenAI error built without a real HTTP request or response, since the
    constructors' arguments differ between openai versions."""
    error = error_class.__new__(error_class)
    Exception.__init__(error, message)
    return error


def write_index(folder: Path, records=RECORDS, model="fake-embedding-model") -> None:
    metadata = [
        {
            "chunk_id": chunk_id,
            "filing_stem": f"{chunk_id}_filing",
            "page_num": number + 1,
            "printed_label": str(number + 1),
            "toc_section": "RISK FACTORS",
            "embed_text": f"Passage {chunk_id}",
            "company": company,
            "deal_name": f"Deal {chunk_id}",
            "asset_type": asset_type,
            "filing_date": filing_date,
        }
        for number, (chunk_id, company, asset_type, filing_date, _) in enumerate(records)
    ]
    np.save(folder / "vectors.npy", np.asarray([r[4] for r in records], dtype=np.float32))
    (folder / "metadata.jsonl").write_text(
        "\n".join(json.dumps(record) for record in metadata), encoding="utf-8"
    )
    (folder / "manifest.json").write_text(json.dumps({"model": model}), encoding="utf-8")


class FakeEmbeddings:
    def __init__(self, vector, error=None):
        self.vector = vector
        self.error = error
        self.calls = []

    def create(self, model, input):
        self.calls.append((model, input))
        if self.error:
            raise self.error
        return SimpleNamespace(data=[SimpleNamespace(embedding=list(self.vector))])


class FakeClient:
    def __init__(self, vector=QUERY_VECTOR, error=None):
        self.embeddings = FakeEmbeddings(vector, error)


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        write_index(self.folder)
        patcher = mock.patch.object(search, "EMBEDDINGS_DIR", self.folder)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = FakeClient()

    def ids(self, **kwargs):
        kwargs.setdefault("client", self.client)
        return [r["chunk_id"] for r in search.retrieve("reserve account", **kwargs)]

    def test_returns_top_k_best_first(self):
        self.assertEqual(self.ids(top_k=3), ["t1", "x1", "f1"])
        self.assertEqual(self.client.embeddings.calls, [("fake-embedding-model", ["reserve account"])])

    def test_passes_chunk_and_index_metadata_through(self):
        result = search.retrieve("q", top_k=1, client=self.client)[0]
        for field in ("chunk_id", "filing_stem", "page_num", "printed_label", "toc_section",
                      "embed_text", "company", "deal_name", "asset_type", "filing_date"):
            self.assertIn(field, result)
        self.assertAlmostEqual(result["similarity"], 1.0, places=5)

    def test_filters_apply_before_search(self):
        # t2 is only 4th overall, but it is the 2nd best TOYOTA chunk.
        self.assertEqual(self.ids(top_k=2, filters={"company": ["TOYOTA"]}), ["t1", "t2"])

    def test_or_within_a_filter_and_across_filters(self):
        filters = {"company": ["TOYOTA", "FORD"], "year": [2025]}
        self.assertEqual(self.ids(top_k=5, filters=filters), ["t2", "f2"])

    def test_single_values_and_string_years(self):
        self.assertEqual(self.ids(top_k=5, filters={"company": "BMW"}), ["b1"])
        self.assertEqual(self.ids(top_k=5, filters={"year": "2026"}), ["w1"])

    def test_fewer_than_top_k_only_when_fewer_chunks_match(self):
        self.assertEqual(len(self.ids(top_k=5)), 5)
        self.assertEqual(self.ids(top_k=5, filters={"asset_type": ["auto_leases"]}), ["b1"])

    def test_no_match_returns_nothing_and_skips_the_embedding_call(self):
        self.assertEqual(self.ids(top_k=5, filters={"company": ["NOT_A_COMPANY"]}), [])
        self.assertEqual(self.client.embeddings.calls, [])

    def test_empty_filters_mean_all(self):
        self.assertEqual(self.ids(top_k=7, filters={"company": [], "year": None}), self.ids(top_k=7))

    def test_missing_values_never_match_a_filter(self):
        everyone = {"company": ["TOYOTA", "FORD", "BMW", "WELLS_FARGO"]}
        self.assertNotIn("x1", self.ids(top_k=7, filters=everyone))
        self.assertNotIn("x1", self.ids(top_k=7, filters={"year": [2024, 2025, 2026]}))

    def test_unknown_filter_is_rejected(self):
        with self.assertRaises(ValueError):
            self.ids(top_k=5, filters={"colour": ["red"]})

    def test_filter_options_lists_index_values(self):
        self.assertEqual(search.filter_options(), {
            "company": ["BMW", "FORD", "TOYOTA", "WELLS_FARGO"],
            "asset_type": ["auto_leases", "auto_loans", "cmbs"],
            "year": [2024, 2025, 2026],
        })


class SearchErrorTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        patcher = mock.patch.object(search, "EMBEDDINGS_DIR", self.folder)
        patcher.start()
        self.addCleanup(patcher.stop)

    def assertQAError(self, text, **kwargs):
        with self.assertRaises(QAError) as caught:
            search.retrieve("q", **kwargs)
        self.assertIn(text, str(caught.exception))
        return caught.exception

    def test_missing_index(self):
        error = self.assertQAError("hasn't been built yet", client=FakeClient())
        self.assertIsInstance(error.__cause__, FileNotFoundError)

    def test_damaged_index(self):
        write_index(self.folder)
        np.save(self.folder / "vectors.npy", np.zeros((2, 3), dtype=np.float32))
        self.assertQAError("damaged", client=FakeClient())

    def test_wrong_embedding_size(self):
        write_index(self.folder)
        self.assertQAError("doesn't match the embedding model", client=FakeClient(vector=[1.0, 0.0]))

    def test_missing_api_key(self):
        write_index(self.folder)
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertQAError("API key isn't set")

    def test_openai_failures_become_plain_messages(self):
        write_index(self.folder)
        cases = [
            (openai_failure(openai.AuthenticationError, "bad key"), "rejected the API key"),
            (openai_failure(openai.RateLimitError, "slow down"), "limiting requests"),
            (openai_failure(openai.APIConnectionError, "no network"), "Couldn't reach OpenAI"),
        ]
        for original, text in cases:
            with self.subTest(text=text):
                error = self.assertQAError(text, client=FakeClient(error=original))
                self.assertIs(error.__cause__, original)


if __name__ == "__main__":
    unittest.main()
