"""Milestone 1 search and metadata-filtering interface.

The metadata CSV narrows the candidate filings first. The corresponding clean
text files are then searched, and each match is returned with source metadata,
a short evidence snippet, and a structured reference to where in the filing it
was found (file, line, position, and the table it sits in, if any).

Examples:
    python filing_search.py --query custody
    python filing_search.py --query paper --query custody --match all
    python filing_search.py --query "paper\\s+(?:or\\s+physical\\s+)?custody" --regex --year 2024
    python filing_search.py --asset-type auto_loans --year 2024        (filter only)
"""

import argparse
import bisect
import json
import re
import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).parent.parent
DEFAULT_INDEX = ROOT_DIR / "data" / "filings_index.csv"
DEFAULT_CLEAN_DIR = ROOT_DIR / "data" / "clean_text"

# The clean text wraps every table as [TABLE_n] ... [/TABLE_n].
TABLE_BLOCK = re.compile(r"\[TABLE_(\d+)\].*?\[/TABLE_\1\]", re.DOTALL)

# Extraction writes [PAGE n] or [PAGE n | printed LABEL] at the start of each page.
PAGE_MARKER = re.compile(r"^\[PAGE (\d+)(?: \| printed ([^\]]+))?\]$", re.MULTILINE)
PAGE_MARKER_INLINE = re.compile(r"\[PAGE \d+(?: \| printed [^\]]+)?\]")


def load_index(index_path: Path = DEFAULT_INDEX) -> pd.DataFrame:
    """Load the metadata index and validate filter fields."""
    # Keep values as strings because dates, identifiers, and filenames are not
    # intended to be converted into numeric data during retrieval.
    index = pd.read_csv(index_path, dtype=str).fillna("")
    required = {"filename", "company", "asset_type", "filing_date"}
    missing = required.difference(index.columns)
    if missing:
        raise ValueError(f"Index is missing required columns: {', '.join(sorted(missing))}")
    return index


# ---------------------------------------------------------------------------
# Query handling
# ---------------------------------------------------------------------------
def _compile_queries(queries, use_regex: bool, case_sensitive: bool) -> list[re.Pattern]:
    """
    Turn one query or a list of queries into compiled patterns.

    Plain searches are escaped so punctuation stays literal, but whitespace
    inside a phrase becomes \\s+. The extracted text has line breaks in the
    middle of sentences (e.g. 'Class A-2' and 'Notes' on separate lines), and a
    literal-space match would silently miss those occurrences.
    """
    if not queries:
        return []
    if isinstance(queries, str):
        queries = [queries]

    flags = re.MULTILINE | (0 if case_sensitive else re.IGNORECASE)
    patterns = []
    for query in queries:
        if not query or not query.strip():
            continue
        if use_regex:
            pattern = query
        else:
            pattern = r"\s+".join(re.escape(word) for word in query.split())
        patterns.append(re.compile(pattern, flags))
    return patterns


def _find_spans(text: str, patterns: list[re.Pattern], match_mode: str):
    """
    Return sorted (start, end) spans for every hit, or None if the filing does
    not satisfy the query. 'all' needs every query to match somewhere; 'any'
    needs at least one.
    """
    per_query = [
        [(m.start(), m.end()) for m in p.finditer(text) if m.end() > m.start()]
        for p in patterns
    ]
    if match_mode == "all" and not all(per_query):
        return None
    if match_mode == "any" and not any(per_query):
        return None
    return sorted({span for found in per_query for span in found}) or None


# ---------------------------------------------------------------------------
# Locating a hit inside a filing
# ---------------------------------------------------------------------------
class _TextLocator:
    """Maps a character offset to a line number and the table it falls in."""

    def __init__(self, text: str):
        self.line_starts = [0] + [m.end() for m in re.finditer(r"\n", text)]
        self.tables = [(m.start(), m.end(), m.group(1)) for m in TABLE_BLOCK.finditer(text)]
        self.table_starts = [t[0] for t in self.tables]
        markers = list(PAGE_MARKER.finditer(text))
        self.marker_spans = [(m.start(), m.end()) for m in markers]
        self.pages = [(m.start(), int(m.group(1)), m.group(2)) for m in markers]
        self.page_starts = [p[0] for p in self.pages]

    def page_at(self, offset: int):
        """(physical page, printed label or None) for an offset, or (None, None)
        when the text has no page markers or the offset precedes the first one."""
        i = bisect.bisect_right(self.page_starts, offset) - 1
        if i < 0:
            return None, None
        return self.pages[i][1], self.pages[i][2]

    def line_of(self, offset: int) -> int:
        """1-based line number, matching what grep -n reports for the same file."""
        return bisect.bisect_right(self.line_starts, offset)

    def table_at(self, offset: int):
        """Table id if the offset is inside a [TABLE_n] block, otherwise None."""
        i = bisect.bisect_right(self.table_starts, offset) - 1
        if i >= 0 and offset < self.tables[i][1]:
            return self.tables[i][2]
        return None


def _snippet(text: str, start: int, end: int, context: int, marker_spans=()) -> str:
    # Include surrounding text so results can be reviewed without opening the
    # entire prospectus. The matched text is marked with << >>. Page markers are
    # removed from the snippet (the page is reported in the reference instead).
    left = max(0, start - context)
    right = min(len(text), end + context)
    for marker_start, marker_end in marker_spans:  # never cut a marker in half
        if marker_start < left < marker_end:
            left = marker_start
        if marker_start < right < marker_end:
            right = marker_end

    def tidy(piece: str) -> str:
        return " ".join(PAGE_MARKER_INLINE.sub("", piece).split())

    before = tidy(text[left:start])
    hit = tidy(text[start:end])
    after = tidy(text[end:right])
    prefix = "..." if left > 0 else ""
    suffix = "..." if right < len(text) else ""
    return f"{prefix}{before} <<{hit}>> {after}{suffix}".replace("  ", " ").strip()


def _build_hit(text, locator, start, end, context, label, filing_date, text_filename) -> dict:
    """One hit: the evidence snippet plus a structured reference to its location."""
    line = locator.line_of(start)
    percent = round(100 * start / max(len(text), 1))
    table_id = locator.table_at(start)
    page, printed = locator.page_at(start)

    where = f"line {line} of {text_filename} (~{percent}% through the filing)"
    if page is not None:
        where = f"page {page}" + (f" (printed {printed})" if printed else "") + ", " + where
    if table_id is not None:
        where += f", inside table [TABLE_{table_id}]"

    return {
        "snippet": _snippet(text, start, end, context, locator.marker_spans),
        "location": {
            "filename": text_filename,
            "page": page,
            "printed_page": printed,
            "line": line,
            "percent_through": percent,
            "table_id": table_id,
        },
        "citation": f"{label} | filed {filing_date} | {where}",
    }


def _resolve_text_path(filename: str, clean_dir: Path):
    """Support both index formats: source filenames (.htm) and clean-text filenames."""
    candidate = clean_dir / f"{Path(filename).stem}_clean.txt"
    if candidate.exists():
        return candidate
    candidate = clean_dir / str(filename)
    return candidate if candidate.exists() else None


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------
def search_filings(
    query=None,
    *,
    index: pd.DataFrame,
    clean_dir: Path = DEFAULT_CLEAN_DIR,
    use_regex: bool = False,
    match: str = "all",
    case_sensitive: bool = False,
    company: str | None = None,
    asset_type: str | None = None,
    year: int | None = None,
    context: int = 180,
    max_hits: int = 3,
    max_results: int | None = None,
) -> list[dict]:
    """
    Search filing text after applying metadata filters.

    query may be one string or a list of strings; with several, `match` decides
    whether a filing must contain all of them or any of them. Each result has
    match_count (total hits in the filing) and hits (up to max_hits entries,
    each with a snippet, a structured location, and a ready-to-display citation).
    """
    patterns = _compile_queries(query, use_regex, case_sensitive)

    # Apply inexpensive metadata filters before reading large text files.
    filtered = index.copy()
    if company:
        filtered = filtered[filtered["company"].str.casefold() == company.casefold()]
    if asset_type:
        filtered = filtered[filtered["asset_type"].str.casefold() == asset_type.casefold()]
    if year is not None:
        filtered = filtered[filtered["filing_date"].str.startswith(f"{year:04d}-")]

    results = []
    for _, row in filtered.iterrows():
        source_path = _resolve_text_path(row["filename"], clean_dir)
        if source_path is None:
            # Say so instead of dropping the filing silently.
            print(f"[WARN] No clean text found for {row['filename']}; skipped.", file=sys.stderr)
            continue

        result = {
            "company": row["company"],
            "deal_name": row.get("deal_name", ""),
            "asset_type": row["asset_type"],
            "filing_date": row["filing_date"],
            "filename": row["filename"],
            "source_path": str(source_path),
            "match_count": 0,
            "hits": [],
        }

        # Filter-only searches never need the text.
        if not patterns:
            results.append(result)
            continue

        text = source_path.read_text(encoding="utf-8", errors="replace")
        spans = _find_spans(text, patterns, match)
        if not spans:
            continue

        locator = _TextLocator(text)
        label = result["deal_name"] or result["company"]
        result["match_count"] = len(spans)
        result["hits"] = [
            _build_hit(text, locator, s, e, context, label, row["filing_date"], source_path.name)
            for s, e in spans[:max_hits]
        ]
        results.append(result)

    # Rank filings with more evidence first, then use stable date/name ordering.
    results.sort(key=lambda result: (-result["match_count"], result["filing_date"], result["filename"]))
    return results[:max_results] if max_results else results


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search ABS filings and filter by metadata.")
    parser.add_argument("--query", action="append",
                        help="Keyword, phrase, or regular expression. Repeat for several.")
    parser.add_argument("--match", choices=["all", "any"], default="all",
                        help="With several --query values: require all (default) or any.")
    parser.add_argument("--regex", action="store_true",
                        help="Interpret --query as a regular expression (use \\s+ rather than a literal space).")
    parser.add_argument("--case-sensitive", action="store_true", help="Default is case-insensitive.")
    parser.add_argument("--company", help="Company label, such as TOYOTA or BMW.")
    parser.add_argument("--asset-type", help="Asset type, such as auto_loans or cmbs.")
    parser.add_argument("--year", type=int, help="Filing year, such as 2025.")
    parser.add_argument("--max-results", type=int, default=10, help="Filings to show (0 shows all).")
    parser.add_argument("--max-hits", type=int, default=3, help="Hits shown per filing.")
    parser.add_argument("--context", type=int, default=180, help="Characters of context around each hit.")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--clean-dir", type=Path, default=DEFAULT_CLEAN_DIR)
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print machine-readable JSON.")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    # A completely unfiltered full-corpus scan is usually accidental.
    if not args.query and not any((args.company, args.asset_type, args.year)):
        raise SystemExit("Provide --query or at least one metadata filter.")

    try:
        results = search_filings(
            args.query,
            index=load_index(args.index),
            clean_dir=args.clean_dir,
            use_regex=args.regex,
            match=args.match,
            case_sensitive=args.case_sensitive,
            company=args.company,
            asset_type=args.asset_type,
            year=args.year,
            context=args.context,
            max_hits=args.max_hits,
        )
    except re.error as error:
        raise SystemExit(f"Invalid regular expression: {error}")

    # Report the true total before any cap is applied.
    total = len(results)
    shown = results[: args.max_results] if args.max_results else results
    truncated = len(shown) < total

    if args.as_json:
        print(json.dumps(shown, indent=2))
        if truncated:
            print(f"[NOTE] {total} filings matched; showing {len(shown)}. Use --max-results 0 for all.", file=sys.stderr)
        return

    # Human-readable output is useful for exploratory work in a terminal.
    summary = f"Results: {total} filing(s) matched"
    if truncated:
        summary += f", showing top {len(shown)} (use --max-results 0 for all)"
    print(summary)
    for result in shown:
        print(f"\n{result['company']} | {result['filing_date']} | {result['asset_type']} | matches={result['match_count']}")
        print(f"Deal: {result['deal_name']}")
        print(f"Source: {result['source_path']}")
        for number, hit in enumerate(result["hits"], start=1):
            print(f"  [{number}] {hit['citation']}")
            print(f"      {hit['snippet']}")


if __name__ == "__main__":
    main()