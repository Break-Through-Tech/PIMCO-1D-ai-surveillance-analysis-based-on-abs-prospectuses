"""Unit tests for semantic retrieval scope filters."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from notebooks import search_embeddings


class SearchEmbeddingFilterTests(unittest.TestCase):
    def setUp(self):
        self.vectors = np.asarray([[1.0, 0.0], [0.9, 0.1], [0.0, 1.0]], dtype=np.float32)
        self.metadata = [
            {"chunk_id": "toyota-2025", "company": "TOYOTA", "asset_type": "auto_loans", "filing_date": "2025-04-01"},
            {"chunk_id": "toyota-2024", "company": "TOYOTA", "asset_type": "auto_loans", "filing_date": "2024-04-01"},
            {"chunk_id": "honda-2025", "company": "HONDA", "asset_type": "auto_loans", "filing_date": "2025-05-01"},
        ]
        self.client = SimpleNamespace(
            embeddings=SimpleNamespace(
                create=lambda **kwargs: SimpleNamespace(
                    data=[SimpleNamespace(embedding=[1.0, 0.0])]
                )
            )
        )

    def retrieve(self, filters):
        with (
            patch.object(search_embeddings.np, "load", return_value=self.vectors),
            patch.object(search_embeddings, "load_metadata", return_value=self.metadata),
            patch.object(search_embeddings.Path, "read_text", return_value='{"model":"test"}'),
        ):
            return search_embeddings.retrieve("custody", top_k=5, client=self.client, filters=filters)

    def test_company_and_year_scope_is_applied_before_ranking(self):
        results = self.retrieve({"company": "toyota", "year": "2025"})
        self.assertEqual([item["chunk_id"] for item in results], ["toyota-2025"])

    def test_asset_class_scope_is_applied(self):
        self.metadata[1]["asset_type"] = "cmbs"
        results = self.retrieve({"asset_type": "auto_loans"})
        self.assertEqual({item["chunk_id"] for item in results}, {"toyota-2025", "honda-2025"})

    def test_empty_scope_returns_no_passages(self):
        results = self.retrieve({"company": "UNKNOWN"})
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
