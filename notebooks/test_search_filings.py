import tempfile
import unittest
from pathlib import Path

import pandas as pd

from notebooks.search_filings import search_filings


class SearchFilingsTests(unittest.TestCase):
    def test_keyword_regex_and_metadata_filters(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            # Use a tiny isolated corpus so the test does not depend on the
            # size or contents of the real filing collection.
            clean_dir = Path(temporary_directory)
            filename = "TOYOTA_AUTO_FINANCE_RECEIVABLES_LLC_2025-01-15_424H_clean.txt"
            (clean_dir / filename).write_text(
                "The trust uses physical custody procedures for receivables.",
                encoding="utf-8",
            )
            index = pd.DataFrame([{
                "company": "TOYOTA",
                "deal_name": "Toyota Auto Receivables 2025-A Owner Trust",
                "asset_type": "auto_loans",
                "filing_date": "2025-01-15",
                "filename": filename,
            }])

            # Verify literal phrase search plus case-insensitive company/year
            # filtering.
            keyword_results = search_filings(
                "physical custody", index=index, clean_dir=clean_dir,
                year=2025, company="toyota",
            )
            # Verify regex matching plus asset-type filtering.
            regex_results = search_filings(
                r"physical\s+custody", index=index, clean_dir=clean_dir,
                use_regex=True, asset_type="auto_loans",
            )

            # Confirm the result includes both evidence and match metadata.
            self.assertEqual(len(keyword_results), 1)
            self.assertEqual(keyword_results[0]["match_count"], 1)
            self.assertIn("physical custody", keyword_results[0]["snippets"][0])
            self.assertEqual(len(regex_results), 1)


if __name__ == "__main__":
    unittest.main()