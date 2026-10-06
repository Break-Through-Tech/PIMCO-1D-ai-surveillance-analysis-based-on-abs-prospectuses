"""
Page markers for the clean text.

Checking all 122 raw filings showed that every filing marks page boundaries in
exactly one of three ways:

    comment  <!-- Field: Page; Sequence: N -->       55 files (Honda, Ford, Hyundai,
                                                       Wells Fargo, World Omni, most Bridgecrest)
    before   style="page-break-before:always"         43 files
    after    style="page-break-after:always"          24 files

All three mark a boundary BETWEEN pages, so one rule covers them: a hit is on page
1 + (number of boundaries before it). A leading or trailing boundary (a break before
the first element or after the last) would create an empty page, so empty pages at
either end are dropped before numbering.

Use from clean_html():

    style = insert_page_boundaries(soup)       # BEFORE tables/img/style are removed
    ...
    text = soup.get_text(separator="\\n", strip=True)
    if style != "none":
        text, num_pages = number_pages(text)

Each page then starts with a line like
    [PAGE 23]                     physical page number (counted from the first page)
    [PAGE 23 | printed A-13]      plus the label printed on the page, when one is found

Check a few filings against their printed page labels:
    python page_markers.py data/AFS_SENSUB_CORP__2024-05-15_424H.htm
"""

import re
import sys
from collections import Counter
from pathlib import Path

from bs4 import Comment, NavigableString

_SENTINEL = "\x00PAGEBREAK\x00"
_COMMENT_MARKER = re.compile(r"^\s*Field:\s*Page\b", re.IGNORECASE)  # not "Field: /Page"
_BREAK_BEFORE = re.compile(r"page-break-before\s*:\s*always", re.IGNORECASE)
_BREAK_AFTER = re.compile(r"page-break-after\s*:\s*always", re.IGNORECASE)

# Matches the marker lines written by number_pages().
PAGE_MARKER = re.compile(r"^\[PAGE (\d+)(?: \| printed ([^\]]+))?\]$", re.MULTILINE)

_ROMAN = re.compile(r"(?=[ivx])x{0,2}(?:ix|iv|v?i{0,3})")


# ---------------------------------------------------------------------------
# Inserting boundaries into the parsed HTML
# ---------------------------------------------------------------------------
def _outer_table(node):
    """The outermost <table> containing node, or None. Boundaries inside a table
    are moved outside it, because tables are flattened to text later and anything
    inside would be lost (which would shift every later page number)."""
    outer = None
    parent = node.find_parent("table")
    while parent is not None:
        outer = parent
        parent = parent.find_parent("table")
    return outer


def insert_page_boundaries(soup) -> str:
    """
    Mark every page boundary in the soup with a sentinel string. Returns which
    style the filing uses: "comment", "before", "after", or "none".

    Call this BEFORE removing script/style/img tags and BEFORE flattening tables,
    since a boundary can sit on any of those elements.
    """
    comments = soup.find_all(
        string=lambda text: isinstance(text, Comment) and _COMMENT_MARKER.match(text)
    )
    if comments:
        for comment in comments:
            table = _outer_table(comment)
            if table is None:
                comment.replace_with(NavigableString(_SENTINEL))
            else:
                table.insert_after(NavigableString(_SENTINEL))
        return "comment"

    for pattern, style, place in (
        (_BREAK_BEFORE, "before", "insert_before"),
        (_BREAK_AFTER, "after", "insert_after"),
    ):
        tags = soup.find_all(style=pattern)
        if not tags:
            continue
        for tag in tags:
            anchor = _outer_table(tag) or tag
            getattr(anchor, place)(NavigableString(_SENTINEL))
        return style

    return "none"


# ---------------------------------------------------------------------------
# Numbering pages in the extracted text
# ---------------------------------------------------------------------------
def printed_label(page_text: str):
    """
    The page label printed at the foot of a page: '148', 'A-13', or 'ii'.
    Filings sometimes split 'A-24' across two lines ('A-' then '24'), so the
    last two lines are checked together. Returns None when nothing matches.
    """
    lines = [line.strip() for line in page_text.splitlines() if line.strip()]
    if not lines:
        return None
    last = lines[-1]

    if re.fullmatch(r"\d{1,3}", last):
        if len(lines) > 1 and re.fullmatch(r"[A-Z]\s*[-\u2013]", lines[-2]):
            return f"{lines[-2][0]}-{last}"
        return last
    annex = re.fullmatch(r"([A-Z])\s*[-\u2013]\s*(\d{1,3})", last)
    if annex:
        return f"{annex.group(1)}-{annex.group(2)}"
    if _ROMAN.fullmatch(last):
        return last
    return None


def number_pages(text: str):
    """
    Split text at the sentinels and write a [PAGE n] marker at the start of each
    page. Returns (numbered_text, number_of_pages).
    """
    segments = text.split(_SENTINEL)

    # A boundary before the first text or after the last would make an empty page.
    while segments and not segments[0].strip():
        segments.pop(0)
    while segments and not segments[-1].strip():
        segments.pop()

    blocks = []
    for number, segment in enumerate(segments, start=1):
        body = segment.strip()
        label = printed_label(body)
        marker = f"[PAGE {number}]" if label is None else f"[PAGE {number} | printed {label}]"
        blocks.append(f"{marker}\n{body}" if body else marker)

    return "\n\n".join(blocks), len(segments)


def strip_page_markers(text: str) -> str:
    """Remove the marker lines, e.g. before running the metadata regexes."""
    return re.sub(r"^\[PAGE \d+(?: \| printed [^\]]+)?\]\n?", "", text, flags=re.MULTILINE)


# ---------------------------------------------------------------------------
# Checking physical pages against printed labels
# ---------------------------------------------------------------------------
def alignment_report(paged_text: str) -> dict:
    """
    Compare each page's physical number with the label printed on it.

    'offsets' counts (physical - printed) for pages with a plain numeric label.
    Aligned body pages show one dominant offset (often 0 or 1). A second offset,
    or a drifting one, means pages were added or dropped, e.g. an extra break.
    """
    pages = PAGE_MARKER.findall(paged_text)
    numeric = [(int(n), int(label)) for n, label in pages if label.isdigit()]
    return {
        "pages": len(pages),
        "numeric_labels": len(numeric),
        "annex_or_roman_labels": sum(1 for _, label in pages if label and not label.isdigit()),
        "no_label": sum(1 for _, label in pages if not label),
        "offsets": Counter(n - label for n, label in numeric).most_common(5),
    }


def _report(path: Path) -> None:
    from html_parser import clean_html, strip_sec_wrapper

    raw = path.read_text(encoding="utf-8", errors="replace")
    result = clean_html(strip_sec_wrapper(raw))
    report = alignment_report(result["clean_text"])

    print(f"{path.name}")
    print(f"  boundary style : {result['page_style']}")
    print(f"  pages          : {report['pages']}")
    print(f"  numeric labels : {report['numeric_labels']}   annex/roman labels: "
          f"{report['annex_or_roman_labels']}   no label found: {report['no_label']}")
    if report["offsets"]:
        shown = ", ".join(f"{offset:+d}: {count} pages" for offset, count in report["offsets"])
        print(f"  physical minus printed  ->  {shown}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python page_markers.py FILE.htm [FILE.htm ...]")
    for name in sys.argv[1:]:
        _report(Path(name))