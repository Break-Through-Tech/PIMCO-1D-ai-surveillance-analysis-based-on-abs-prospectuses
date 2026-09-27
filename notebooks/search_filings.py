"""Milestone 1 search and metadata-filtering interface.

The metadata CSV narrows the candidate filings first. The corresponding clean
text files are then searched, and each match is returned with source metadata
and short evidence snippets.
"""

import argparse
import json
import re
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).parent.parent
DEFAULT_INDEX = ROOT_DIR / "data" / "filings_index.csv"
DEFAULT_CLEAN_DIR = ROOT_DIR / "data" / "clean_text"


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


def _matches(text: str, query: str | None, use_regex: bool) -> list[re.Match[str]]:
    if not query:
        return []
    # Escape normal searches so punctuation in a user's query stays literal.
    pattern = query if use_regex else re.escape(query)
    return list(re.finditer(pattern, text, flags=re.IGNORECASE))


def _snippet(text: str, start: int, end: int, context: int) -> str:
    # Include surrounding text so results can be reviewed without opening the
    # entire prospectus.
    left = max(0, start - context)
    right = min(len(text), end + context)
    return re.sub(r"\s+", " ", text[left:right]).strip()


def search_filings(
    query: str | None = None,
    *,
    index: pd.DataFrame,
    clean_dir: Path = DEFAULT_CLEAN_DIR,
    use_regex: bool = False,
    company: str | None = None,
    asset_type: str | None = None,
    year: int | None = None,
    context: int = 180,
    max_results: int | None = None,
) -> list[dict]:
    """Search filing text after applying metadata filters."""
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
        # Support both index formats: clean-text filenames and source filenames.
        source_path = clean_dir / f"{Path(row['filename']).stem}_clean.txt"
        if not source_path.exists():
            source_path = clean_dir / str(row["filename"])
        if not source_path.exists():
            continue

        text = source_path.read_text(encoding="utf-8", errors="replace")
        matches = _matches(text, query, use_regex)
        if query and not matches:
            continue
        # Store only the first three snippets while retaining the total count.
        results.append(
            {
                "company": row["company"],
                "deal_name": row.get("deal_name", ""),
                "asset_type": row["asset_type"],
                "filing_date": row["filing_date"],
                "filename": row["filename"],
                "source_path": str(source_path),
                "match_count": len(matches),
                "snippets": [_snippet(text, m.start(), m.end(), context) for m in matches[:3]],
            }
        )

    # Rank filings with more evidence first, then use stable date/name ordering.
    results.sort(key=lambda result: (-result["match_count"], result["filing_date"], result["filename"]))
    return results[:max_results] if max_results else results


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search ABS filings and filter by metadata.")
    parser.add_argument("--query", help="Keyword or regular expression to search for.")
    parser.add_argument("--regex", action="store_true", help="Interpret --query as a regular expression.")
    parser.add_argument("--company", help="Company label, such as TOYOTA or BMW.")
    parser.add_argument("--asset-type", help="Asset type, such as auto_loans or cmbs.")
    parser.add_argument("--year", type=int, help="Filing year, such as 2025.")
    parser.add_argument("--max-results", type=int, default=10)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--clean-dir", type=Path, default=DEFAULT_CLEAN_DIR)
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print machine-readable JSON.")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    # A completely unfiltered full-corpus scan is usually accidental.
    if args.query is None and not any((args.company, args.asset_type, args.year)):
        raise SystemExit("Provide --query or at least one metadata filter.")
    results = search_filings(
        args.query,
        index=load_index(args.index),
        clean_dir=args.clean_dir,
        use_regex=args.regex,
        company=args.company,
        asset_type=args.asset_type,
        year=args.year,
        max_results=args.max_results,
    )
    if args.as_json:
        print(json.dumps(results, indent=2))
        return
    # Human-readable output is useful for exploratory work in a terminal.
    print(f"Results: {len(results)}")
    for result in results:
        print(f"\n{result['company']} | {result['filing_date']} | {result['asset_type']} | matches={result['match_count']}")
        print(f"Deal: {result['deal_name']}")
        print(f"Source: {result['source_path']}")
        for snippet in result["snippets"]:
            print(f"  ...{snippet}...")


if __name__ == "__main__":
    main()