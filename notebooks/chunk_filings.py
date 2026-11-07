"""
Milestone 2 — Page-based chunker
=================================
For every clean text file in data/clean_text/ (written by parse_filings.py):
  1. Read the text; every page already starts with a [PAGE N | printed X] header.
  2. Split at those markers → one raw chunk per physical page.
  3. Classify each chunk:
       "toc"      – the page(s) that contain the TABLE OF CONTENTS heading
       "divider"  – near-empty pages (≤ DIVIDER_TOKEN_LIMIT tokens); kept for
                    traceability but excluded from the embed set
       "body"     – everything else
  4. Tag body chunks with the TOC section they fall under (parsed from the TOC
     table: "SECTION TITLE | printed-page-number").
  5. Measure token counts with tiktoken (cl100k_base, same encoder used by
     OpenAI's text-embedding-3-* models, limit 8 191 tokens).
  6. Split oversized body chunks:
       a. First try splitting at [TABLE_N] / [/TABLE_N] boundaries.
       b. Within a text segment, split at paragraph (\\n\\n) then sentence (. )
          boundaries.  Every sub-chunk keeps the original page_num + printed_label
          and gets a chunk_part counter.
       c. Oversized tables are split by row groups; the header row is repeated on
          every piece.
  7. Strip page-marker lines from embed_text (they add noise to embeddings).
  8. Join filing-level metadata from data/filings_index.csv.
  9. Write one JSONL file per filing to data/chunks/ and a summary manifest to
     data/chunks_manifest.csv.

Usage
-----
    python notebooks/chunk_filings.py                  # all filings
    python notebooks/chunk_filings.py --filing TOYOTA_AUTO_FINANCE_RECEIVABLES_LLC_2024-04-18_424H_clean.txt
    python notebooks/chunk_filings.py --limit 5        # first N filings (smoke test)
"""

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd
import tiktoken

# ---------------------------------------------------------------------------
# Path setup — notebooks/ lives one level below the project root
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
CLEAN_DIR = DATA_DIR / "clean_text"
CHUNKS_DIR = DATA_DIR / "chunks"
INDEX_PATH = DATA_DIR / "filings_index.csv"

sys.path.insert(0, str(Path(__file__).parent))
from page_markers import PAGE_MARKER                      # compiled regex


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ENCODER = tiktoken.get_encoding("cl100k_base")
TOKEN_LIMIT = 8_191          # OpenAI text-embedding-3-* hard limit
DIVIDER_TOKEN_LIMIT = 30     # pages with ≤ this many tokens are dividers

_TOC_HEADING = re.compile(r"TABLE\s+OF\s+CONTENTS", re.IGNORECASE)
# A real TOC row: "SECTION TITLE | 42"  or multi-cell "SECTION |  |  | 42 |"
# We match any pipe-delimited row whose first non-empty cell is a title and
# whose last non-empty cell is a page label (digit, roman, or annex like A-3).
_PAGE_LABEL = re.compile(r"^[A-Za-z0-9][\w\-]*$")
# A page is the real TOC page only if it has the heading AND at least this
# many TOC rows (section | page_number).  Running headers say "Table of
# Contents" on every page but don't have the actual section list.
_TOC_MIN_ROWS = 5
# Page-marker line written by number_pages()
_PAGE_MARKER_LINE = re.compile(r"^\[PAGE \d+(?: \| printed [^\]]+)?\]\n?", re.MULTILINE)
# Table block boundaries
_TABLE_OPEN = re.compile(r"\[TABLE_(\d+)\]")
_TABLE_CLOSE = re.compile(r"\[/TABLE_(\d+)\]")


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------
def count_tokens(text: str) -> int:
    return len(ENCODER.encode(text))


def strip_marker_lines(text: str) -> str:
    """Remove [PAGE N] / [PAGE N | printed X] lines from text before embedding."""
    return _PAGE_MARKER_LINE.sub("", text).strip()


# ---------------------------------------------------------------------------
# TOC parsing
# ---------------------------------------------------------------------------
def _parse_toc_row(line: str) -> tuple[str, str] | None:
    """
    Extract (title, page_label) from a pipe-delimited TOC row.
    Handles both 2-cell rows  "SECTION | 42"
    and multi-cell rows       "SECTION |  |  | 42 |"
    Returns None if the line doesn't look like a TOC entry.
    """
    cells = [c.strip() for c in line.split("|")]
    non_empty = [c for c in cells if c]
    if len(non_empty) < 2:
        return None
    title = non_empty[0]
    label = non_empty[-1]
    # Label must be a page reference: digits, roman numerals, or annex (A-3)
    if not _PAGE_LABEL.match(label):
        return None
    # Title must be at least 3 chars and not itself a page label
    if len(title) < 3 or _PAGE_LABEL.match(title):
        return None
    return title, label


def parse_toc(paged_text: str) -> dict[str, str]:
    """
    Return a mapping  printed_label -> section_title  built from the TOC table.

    The TOC is rendered as pipe-delimited rows by parse_filings.py:
        SUMMARY OF TERMS | 8
        RISK FACTORS | 28
    We collect every row where the right cell is a page label (digit, roman, or
    annex like A-3) and the left cell is a non-empty title.
    """
    toc_map: dict[str, str] = {}
    in_toc = False
    for line in paged_text.splitlines():
        if _TOC_HEADING.search(line):
            in_toc = True
            continue
        if not in_toc:
            continue
        parsed = _parse_toc_row(line)
        if parsed:
            title, label = parsed
            toc_map[label] = title
    return toc_map


def resolve_section(printed_label: str | None, toc_map: dict[str, str]) -> str | None:
    """
    Find the TOC section that owns this page.

    The TOC maps the *first* printed page of each section.  We walk backwards
    through the sorted TOC keys to find the section whose start page is ≤ the
    current page's printed label.
    """
    if not toc_map or printed_label is None:
        return None

    def label_sort_key(lbl: str):
        """Convert a printed label to a sortable integer for comparison."""
        if lbl.isdigit():
            return int(lbl)
        m = re.match(r"([A-Z])-(\d+)", lbl)
        if m:
            return 10_000 + ord(m.group(1)) * 1000 + int(m.group(2))
        # Roman numerals — treat as negative so they sort before page 1
        roman = {"i": -9, "ii": -8, "iii": -7, "iv": -6, "v": -5,
                 "vi": -4, "vii": -3, "viii": -2, "ix": -1}
        return roman.get(lbl.lower(), -99)

    current_key = label_sort_key(printed_label)
    best_title = None
    best_key = -10_000
    for lbl, title in toc_map.items():
        k = label_sort_key(lbl)
        if k <= current_key and k > best_key:
            best_key = k
            best_title = title
    return best_title


# ---------------------------------------------------------------------------
# Oversized-chunk splitting
# ---------------------------------------------------------------------------
def _split_table_rows(table_text: str, header_rows: int = 1) -> list[str]:
    """
    Split a [TABLE_N]...[/TABLE_N] block into row-group pieces that each fit
    within TOKEN_LIMIT.  The header rows are repeated on every piece.
    """
    # Extract the inner content between the tags
    inner_match = re.search(r"\[TABLE_\d+\](.*?)\[/TABLE_\d+\]", table_text, re.DOTALL)
    if not inner_match:
        return [table_text]

    tag_open = re.match(r"(\[TABLE_\d+\])", table_text).group(1)
    tag_close = re.search(r"(\[/TABLE_\d+\])", table_text).group(1)
    inner = inner_match.group(1)
    rows = [r for r in inner.splitlines() if r.strip()]

    if not rows:
        return [table_text]

    header = rows[:header_rows]
    body_rows = rows[header_rows:]
    header_text = "\n".join(header)

    pieces = []
    current_rows: list[str] = []
    current_tokens = count_tokens(f"{tag_open}\n{header_text}\n{tag_close}")

    for row in body_rows:
        row_tokens = count_tokens(row + "\n")
        if current_tokens + row_tokens > TOKEN_LIMIT and current_rows:
            block = f"{tag_open}\n{header_text}\n" + "\n".join(current_rows) + f"\n{tag_close}"
            pieces.append(block)
            current_rows = []
            current_tokens = count_tokens(f"{tag_open}\n{header_text}\n{tag_close}")
        current_rows.append(row)
        current_tokens += row_tokens

    if current_rows:
        block = f"{tag_open}\n{header_text}\n" + "\n".join(current_rows) + f"\n{tag_close}"
        pieces.append(block)

    return pieces if pieces else [table_text]


def _split_text_segment(text: str) -> list[str]:
    """
    Split a plain-text segment (no table tags) at paragraph then sentence
    boundaries so each piece fits within TOKEN_LIMIT.
    """
    if count_tokens(text) <= TOKEN_LIMIT:
        return [text]

    pieces: list[str] = []
    current = ""
    for para in re.split(r"\n\n+", text):
        if count_tokens(current + "\n\n" + para) > TOKEN_LIMIT and current:
            pieces.append(current.strip())
            current = para
        else:
            current = (current + "\n\n" + para).strip() if current else para

    # If a single paragraph is still too large, split at sentence boundaries
    if current:
        if count_tokens(current) <= TOKEN_LIMIT:
            pieces.append(current)
        else:
            sentence_buf = ""
            for sentence in re.split(r"(?<=[.!?])\s+", current):
                if count_tokens(sentence_buf + " " + sentence) > TOKEN_LIMIT and sentence_buf:
                    pieces.append(sentence_buf.strip())
                    sentence_buf = sentence
                else:
                    sentence_buf = (sentence_buf + " " + sentence).strip()
            if sentence_buf:
                pieces.append(sentence_buf)

    return [p for p in pieces if p.strip()]


def split_oversized(text: str) -> list[str]:
    """
    Split text that exceeds TOKEN_LIMIT.

    Strategy:
      1. Segment the text into alternating table-blocks and plain-text runs.
      2. Split each table block by rows (repeating the header).
      3. Split each plain-text run at paragraph / sentence boundaries.
      4. Merge consecutive small pieces back together where possible.
    """
    if count_tokens(text) <= TOKEN_LIMIT:
        return [text]

    # Tokenise into segments: ("text", content) or ("table", content)
    segments: list[tuple[str, str]] = []
    last = 0
    for m in re.finditer(r"\[TABLE_\d+\].*?\[/TABLE_\d+\]", text, re.DOTALL):
        if m.start() > last:
            segments.append(("text", text[last:m.start()]))
        segments.append(("table", m.group()))
        last = m.end()
    if last < len(text):
        segments.append(("text", text[last:]))

    raw_pieces: list[str] = []
    for kind, content in segments:
        if kind == "table":
            if count_tokens(content) > TOKEN_LIMIT:
                raw_pieces.extend(_split_table_rows(content))
            else:
                raw_pieces.append(content)
        else:
            raw_pieces.extend(_split_text_segment(content))

    # Merge consecutive small pieces
    merged: list[str] = []
    buf = ""
    for piece in raw_pieces:
        candidate = (buf + "\n\n" + piece).strip() if buf else piece
        if count_tokens(candidate) <= TOKEN_LIMIT:
            buf = candidate
        else:
            if buf:
                merged.append(buf)
            buf = piece
    if buf:
        merged.append(buf)

    return merged if merged else [text]


# ---------------------------------------------------------------------------
# Core chunker
# ---------------------------------------------------------------------------
def filing_stem_of(clean_path: Path) -> str:
    """Filing name without the _clean suffix, so chunk IDs match the source filing."""
    return clean_path.stem.removesuffix("_clean")


def chunk_filing(clean_path: Path) -> list[dict]:
    """
    Read one clean text filing and return a list of chunk dicts.
    Each dict has:
        chunk_id, filing_stem, page_num, printed_label, chunk_part,
        chunk_type, toc_section, token_count, embed (bool),
        raw_text, embed_text
    """
    paged_text = clean_path.read_text(encoding="utf-8", errors="replace")

    # ---- Build TOC map ------------------------------------------------
    toc_map = parse_toc(paged_text)

    # ---- Split into pages ---------------------------------------------
    # PAGE_MARKER has two capturing groups so re.split() produces:
    #   [pre_text, page_num, printed_label_or_None, body, page_num, ...]
    # Groups of 3 after the leading pre_text.
    split_parts = PAGE_MARKER.split(paged_text)

    # If no page markers exist, treat the whole
    # document as a single page.
    if len(split_parts) == 1:
        pages = [("1", None, paged_text.strip())]
    else:
        pages: list[tuple[str, str | None, str]] = []
        pre = split_parts[0]
        if pre.strip():
            pages.append(("0", None, pre.strip()))  # pre-marker cover text
        # Remaining items come in triples: (page_num, printed_label, body)
        it = iter(split_parts[1:])
        for page_num_str, printed_raw, body in zip(it, it, it):
            printed = printed_raw.strip() if printed_raw else None
            pages.append((page_num_str, printed, body.strip()))

    # ---- Classify pages and detect TOC pages --------------------------
    # A page is the real TOC only if it has the heading AND >= _TOC_MIN_ROWS
    # pipe-delimited rows (section | page_number).  Running headers that say
    # "Table of Contents" on every page won't have the actual section list.
    toc_page_nums: set[str] = set()
    for page_num_str, _, body in pages:
        if _TOC_HEADING.search(body):
            row_count = sum(1 for line in body.splitlines() if _parse_toc_row(line) is not None)
            if row_count >= _TOC_MIN_ROWS:
                toc_page_nums.add(page_num_str)

    # ---- Emit chunks --------------------------------------------------
    filing_stem = filing_stem_of(clean_path)
    chunks: list[dict] = []
    chunk_seq = 0  # global sequence within this filing

    for page_num_str, printed_label, body in pages:
        if not body:
            continue  # drop truly empty pages

        token_count = count_tokens(body)

        # Classify
        if page_num_str in toc_page_nums:
            chunk_type = "toc"
        elif token_count <= DIVIDER_TOKEN_LIMIT:
            chunk_type = "divider"
        else:
            chunk_type = "body"

        should_embed = chunk_type == "body"
        toc_section = resolve_section(printed_label, toc_map) if chunk_type == "body" else None

        # Split oversized body chunks
        if chunk_type == "body" and token_count > TOKEN_LIMIT:
            sub_pieces = split_oversized(body)
        else:
            sub_pieces = [body]

        for part_idx, piece in enumerate(sub_pieces):
            embed_text = strip_marker_lines(piece)
            chunks.append({
                "chunk_id":      f"{filing_stem}__p{page_num_str}_pt{part_idx}",
                "filing_stem":   filing_stem,
                "page_num":      int(page_num_str),
                "printed_label": printed_label,
                "chunk_part":    part_idx,
                "chunk_type":    chunk_type,
                "toc_section":   toc_section,
                "token_count":   count_tokens(embed_text),
                "embed":         should_embed,
                "raw_text":      piece,
                "embed_text":    embed_text,
            })
            chunk_seq += 1

    return chunks


# ---------------------------------------------------------------------------
# Metadata join
# ---------------------------------------------------------------------------
def load_filing_metadata() -> dict[str, dict]:
    """Return a dict keyed by filing stem → metadata dict from filings_index.csv."""
    if not INDEX_PATH.exists():
        return {}
    df = pd.read_csv(INDEX_PATH, dtype=str)
    # filings_index uses clean .txt filenames; convert to the filing stem
    df["filing_stem"] = df["filename"].str.replace("_clean.txt", "", regex=False).str.replace(".txt", "", regex=False)
    meta = {}
    for _, row in df.iterrows():
        meta[row["filing_stem"]] = row.drop("filing_stem").to_dict()
    return meta


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Chunk SEC 424H filings by page.")
    parser.add_argument("--filing", help="Process a single clean text filename (basename only).")
    parser.add_argument("--limit", type=int, help="Process at most N filings (smoke test).")
    args = parser.parse_args()

    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    filing_meta = load_filing_metadata()

    if args.filing:
        clean_files = [CLEAN_DIR / args.filing]
    else:
        clean_files = sorted(CLEAN_DIR.glob("*_424H_clean.txt"))

    if args.limit:
        clean_files = clean_files[: args.limit]

    manifest_rows: list[dict] = []

    for clean_path in clean_files:
        if not clean_path.exists():
            print(f"  [WARN] Not found: {clean_path}")
            continue

        print(f"  Chunking: {clean_path.name}")
        try:
            chunks = chunk_filing(clean_path)
        except Exception as exc:
            print(f"    ERROR: {exc}")
            continue

        # Attach filing-level metadata to every chunk
        meta = filing_meta.get(filing_stem_of(clean_path), {})
        for chunk in chunks:
            chunk.update(meta)

        # Write JSONL
        out_path = CHUNKS_DIR / f"{filing_stem_of(clean_path)}_chunks.jsonl"
        with out_path.open("w", encoding="utf-8") as fh:
            for chunk in chunks:
                fh.write(json.dumps(chunk, ensure_ascii=False) + "\n")

        # Manifest row
        embed_chunks = [c for c in chunks if c["embed"]]
        oversized_before = sum(1 for c in chunks if c["chunk_type"] == "body" and c["chunk_part"] > 0)
        manifest_rows.append({
            "filing":          clean_path.name,
            "total_chunks":    len(chunks),
            "body_chunks":     sum(1 for c in chunks if c["chunk_type"] == "body"),
            "toc_chunks":      sum(1 for c in chunks if c["chunk_type"] == "toc"),
            "divider_chunks":  sum(1 for c in chunks if c["chunk_type"] == "divider"),
            "embed_chunks":    len(embed_chunks),
            "oversized_splits": oversized_before,
            "max_tokens":      max((c["token_count"] for c in embed_chunks), default=0),
            "mean_tokens":     round(sum(c["token_count"] for c in embed_chunks) / len(embed_chunks), 1) if embed_chunks else 0,
            "output_file":     out_path.name,
        })
        print(f"    -> {len(chunks)} chunks ({len(embed_chunks)} to embed), "
              f"max {manifest_rows[-1]['max_tokens']} tokens")

    manifest_df = pd.DataFrame(manifest_rows)
    manifest_path = CHUNKS_DIR / "chunks_manifest.csv"
    manifest_df.to_csv(manifest_path, index=False)
    print(f"\nDone. Manifest saved to {manifest_path}")
    if not manifest_df.empty:
        print(manifest_df[["filing", "embed_chunks", "max_tokens", "mean_tokens",
                            "oversized_splits"]].to_string(index=False))


if __name__ == "__main__":
    main()
