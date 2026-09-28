import contextlib
import io
import os
import re
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from notebooks.search_filings import search_filings


def _index(filename):
    """One-row metadata index for a tiny test corpus."""
    return pd.DataFrame([{
        "company": "TOYOTA",
        "deal_name": "Toyota Auto Receivables 2025-A Owner Trust",
        "asset_type": "auto_loans",
        "filing_date": "2025-01-15",
        "filename": filename,
    }])


class SearchFilingsTests(unittest.TestCase):
    """Search behavior on tiny corpora written to a temporary folder, so the
    tests do not depend on the size or contents of the real filings."""

    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.clean_dir = Path(temporary_directory.name)
        self.filename = "TOYOTA_AUTO_FINANCE_RECEIVABLES_LLC_2025-01-15_424H_clean.txt"
        self.index = _index(self.filename)

    def _write(self, text):
        (self.clean_dir / self.filename).write_text(text, encoding="utf-8")

    # --- Keyword, regex, and metadata filters ---------------------------------

    def test_keyword_regex_and_metadata_filters(self):
        self._write("The trust uses physical custody procedures for receivables.")

        # Verify literal phrase search plus case-insensitive company/year
        # filtering.
        keyword_results = search_filings(
            "physical custody", index=self.index, clean_dir=self.clean_dir,
            year=2025, company="toyota",
        )
        # Verify regex matching plus asset-type filtering.
        regex_results = search_filings(
            r"physical\s+custody", index=self.index, clean_dir=self.clean_dir,
            use_regex=True, asset_type="auto_loans",
        )

        # Confirm the result includes evidence, match metadata, and where in the
        # filing the match was found. The matched text is marked with << >>.
        self.assertEqual(len(keyword_results), 1)
        self.assertEqual(keyword_results[0]["match_count"], 1)
        hit = keyword_results[0]["hits"][0]
        self.assertIn("<<physical custody>>", hit["snippet"])
        self.assertEqual(hit["location"]["line"], 1)
        self.assertIn("line 1", hit["citation"])
        self.assertEqual(len(regex_results), 1)

    def test_filters_exclude_non_matching_filings(self):
        self._write("The trust uses physical custody procedures for receivables.")

        for filters in ({"year": 2024}, {"asset_type": "cmbs"}, {"company": "ford"}):
            with self.subTest(filters=filters):
                results = search_filings(
                    "physical custody", index=self.index, clean_dir=self.clean_dir, **filters
                )
                self.assertEqual(results, [])

    def test_query_not_in_the_text_finds_nothing(self):
        self._write("The trust uses physical custody procedures for receivables.")
        results = search_filings(
            "servicer advances", index=self.index, clean_dir=self.clean_dir
        )
        self.assertEqual(results, [])

    def test_filter_only_search_lists_filings_without_hits(self):
        self._write("The trust uses physical custody procedures for receivables.")
        results = search_filings(index=self.index, clean_dir=self.clean_dir, company="Toyota")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["match_count"], 0)
        self.assertEqual(results[0]["hits"], [])

    # --- Matching behavior ------------------------------------------------------

    def test_phrase_matches_across_a_line_break(self):
        # The extracted text breaks lines mid-sentence, so a phrase can be split
        # across two lines. A literal-space match would miss it.
        self._write("The indenture trustee will hold the paper\ncustody records for the trust.")
        results = search_filings("paper custody", index=self.index, clean_dir=self.clean_dir)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["match_count"], 1)
        self.assertIn("<<paper custody>>", results[0]["hits"][0]["snippet"])

    def test_several_queries_all_versus_any(self):
        self._write("Custody procedures apply to the receivables.")
        queries = ["custody", "servicer"]

        require_all = search_filings(
            queries, index=self.index, clean_dir=self.clean_dir, match="all"
        )
        allow_any = search_filings(
            queries, index=self.index, clean_dir=self.clean_dir, match="any"
        )

        self.assertEqual(require_all, [])
        self.assertEqual(len(allow_any), 1)
        self.assertEqual(allow_any[0]["match_count"], 1)

    def test_case_sensitive_flag(self):
        self._write("The trust uses physical custody procedures.")

        case_insensitive = search_filings(
            "PHYSICAL CUSTODY", index=self.index, clean_dir=self.clean_dir
        )
        case_sensitive = search_filings(
            "PHYSICAL CUSTODY", index=self.index, clean_dir=self.clean_dir,
            case_sensitive=True,
        )

        self.assertEqual(len(case_insensitive), 1)
        self.assertEqual(case_sensitive, [])

    # --- Where in the filing a hit is -------------------------------------------

    def test_hit_reports_line_and_the_table_it_is_inside(self):
        self._write(
            "Intro\n"
            "The trust uses physical custody procedures.\n"
            "[TABLE_0]\n"
            "Barclays Capital Inc. | $1,000\n"
            "[/TABLE_0]\n"
        )

        prose = search_filings("physical custody", index=self.index, clean_dir=self.clean_dir)
        in_table = search_filings("Barclays", index=self.index, clean_dir=self.clean_dir)

        prose_location = prose[0]["hits"][0]["location"]
        self.assertEqual(prose_location["line"], 2)
        self.assertIsNone(prose_location["table_id"])

        table_hit = in_table[0]["hits"][0]
        self.assertEqual(table_hit["location"]["line"], 4)
        self.assertEqual(table_hit["location"]["table_id"], "0")
        self.assertIn("inside table [TABLE_0]", table_hit["citation"])

    def test_hit_reports_page_from_page_markers(self):
        # Extraction writes [PAGE n] (or [PAGE n | printed LABEL]) at the start of
        # each page.
        self._write(
            "[PAGE 1 | printed 1]\nCover text\n\n"
            "[PAGE 2 | printed A-13]\nThe trust uses physical custody procedures.\n"
        )

        results = search_filings("physical custody", index=self.index, clean_dir=self.clean_dir)

        hit = results[0]["hits"][0]
        self.assertEqual(hit["location"]["page"], 2)
        self.assertEqual(hit["location"]["printed_page"], "A-13")
        self.assertIn("page 2 (printed A-13)", hit["citation"])
        # Markers are not part of the evidence shown to the reader.
        self.assertNotIn("[PAGE", hit["snippet"])

    def test_text_without_page_markers_has_no_page(self):
        self._write("The trust uses physical custody procedures.")

        results = search_filings("physical custody", index=self.index, clean_dir=self.clean_dir)

        hit = results[0]["hits"][0]
        self.assertIsNone(hit["location"]["page"])
        self.assertNotIn("page ", hit["citation"].split("|")[-1])

    # --- Index handling ---------------------------------------------------------

    def test_missing_text_file_is_reported_not_silently_dropped(self):
        missing = "GHOST_2025-01-15_424H_clean.txt"
        warnings = io.StringIO()

        with contextlib.redirect_stderr(warnings):
            results = search_filings("custody", index=_index(missing), clean_dir=self.clean_dir)

        self.assertEqual(results, [])
        self.assertIn(missing, warnings.getvalue())

    def test_index_may_store_the_source_filename(self):
        # The index can list the raw .htm name; the clean text is found from it.
        self._write("The trust uses physical custody procedures.")
        source_name = "TOYOTA_AUTO_FINANCE_RECEIVABLES_LLC_2025-01-15_424H.htm"

        results = search_filings(
            "physical custody", index=_index(source_name), clean_dir=self.clean_dir
        )

        self.assertEqual(len(results), 1)


# ---------------------------------------------------------------------------
# Real cleaned filings
# ---------------------------------------------------------------------------
# data/ is gitignored, so these tests run only where the cleaned filings exist
# and are skipped elsewhere; set FILINGS_CLEAN_DIR to run them from another
# folder. Each check compares the search result with an independent scan of the
# same file (plain line splitting and regexes), so it does not just re-run the
# code under test. A few files, spread across issuers, keep the run short.
REAL_CLEAN_DIR = Path(
    os.environ.get("FILINGS_CLEAN_DIR")
    or Path(__file__).resolve().parent.parent / "data" / "clean_text"
)
REAL_FILE_LIMIT = 3

TABLE_BLOCK = re.compile(r"\[TABLE_(\d+)\]\n(.*?)\n\[/TABLE_\1\]", re.DOTALL)
PAGE_MARKER = re.compile(r"^\[PAGE (\d+)(?: \| printed [^\]]+)?\]$", re.MULTILINE)


def _real_files():
    """A few cleaned filings, spread across the sorted list so they cover
    different issuers (files sort by issuer name)."""
    if not REAL_CLEAN_DIR.is_dir():
        return []
    files = sorted(REAL_CLEAN_DIR.glob("*_clean.txt"))
    step = max(1, len(files) // REAL_FILE_LIMIT)
    return files[::step][:REAL_FILE_LIMIT]


def _read(path):
    return path.read_text(encoding="utf-8", errors="replace")


def _line_of(text, offset):
    """1-based line number of a character offset."""
    return text.count("\n", 0, offset) + 1


def _search_real(path, query):
    """Every hit for a query in one real file (no cap, so the full result can
    be checked)."""
    results = search_filings(
        query, index=_index(path.name), clean_dir=path.parent, max_hits=10**6
    )
    return results[0]["hits"] if results else []


def _middle_line_break_phrase(text):
    """(phrase, line) for two words split across a line break, taken from the
    middle of the file so line counting is checked far from the top. None if
    the file has no such phrase."""
    splits = list(re.finditer(r"([A-Za-z]{4,})\n([A-Za-z]{4,})", text))
    if not splits:
        return None
    split = splits[len(splits) // 2]
    return f"{split.group(1)} {split.group(2)}", _line_of(text, split.start(1))


def _middle_table_cell(text):
    """(table id, first cell text) for a table from the middle of the file, not
    the cover-page layout table. None if the file has no usable table."""
    candidates = []
    for block in TABLE_BLOCK.finditer(text):
        first_cell = block.group(2).split("\n")[0].split("|")[0].strip()
        if len(first_cell) >= 8 and re.search(r"[A-Za-z]", first_cell):
            candidates.append((block.group(1), first_cell))
    return candidates[len(candidates) // 2] if candidates else None


def _expected_page(marker_lines, line):
    """The page whose marker is the last one at or before a line, or None if the
    line comes before the first marker."""
    pages = [page for marker_line, page in marker_lines if marker_line <= line]
    return pages[-1] if pages else None


@unittest.skipUnless(_real_files(), "no cleaned filings found; set FILINGS_CLEAN_DIR to run")
class RealFilingTests(unittest.TestCase):
    def test_reported_lines_match_an_independent_line_scan(self):
        for path in _real_files():
            with self.subTest(file=path.name):
                lines = _read(path).split("\n")
                expected = {
                    number for number, line in enumerate(lines, start=1)
                    if "trust" in line.lower()
                }
                found = {hit["location"]["line"] for hit in _search_real(path, "trust")}

                self.assertTrue(expected, "expected the word 'trust' in a real filing")
                self.assertEqual(found, expected)

    def test_snippets_contain_the_matched_text(self):
        for path in _real_files():
            with self.subTest(file=path.name):
                hits = _search_real(path, "trust")

                self.assertTrue(hits)
                for hit in hits:
                    self.assertIn("<<trust>>", hit["snippet"].lower())

    def test_phrase_split_across_a_line_break_is_found_at_the_right_line(self):
        for path in _real_files():
            with self.subTest(file=path.name):
                found = _middle_line_break_phrase(_read(path))
                if found is None:
                    self.skipTest("no phrase split across lines in this file")
                phrase, expected_line = found

                lines = {hit["location"]["line"] for hit in _search_real(path, phrase)}

                self.assertIn(expected_line, lines)

    def test_hit_inside_a_table_reports_that_table(self):
        for path in _real_files():
            with self.subTest(file=path.name):
                found = _middle_table_cell(_read(path))
                if found is None:
                    self.skipTest("no table with a usable first cell in this file")
                table_id, cell = found

                tables_seen = {hit["location"]["table_id"] for hit in _search_real(path, cell)}

                self.assertIn(table_id, tables_seen)

    def test_pages_match_an_independent_marker_scan(self):
        for path in _real_files():
            with self.subTest(file=path.name):
                text = _read(path)
                marker_lines = [
                    (_line_of(text, marker.start()), int(marker.group(1)))
                    for marker in PAGE_MARKER.finditer(text)
                ]
                if not marker_lines:
                    self.skipTest("no [PAGE n] markers in this file (extraction not re-run yet)")

                for hit in _search_real(path, "trust"):
                    line = hit["location"]["line"]
                    self.assertEqual(hit["location"]["page"], _expected_page(marker_lines, line))


if __name__ == "__main__":
    unittest.main()