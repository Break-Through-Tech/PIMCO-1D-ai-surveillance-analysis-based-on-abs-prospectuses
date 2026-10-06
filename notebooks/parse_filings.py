"""
Milestone 1 — HTML Filing Parser
Parses SEC 424H filings for all 15 companies in the dataset.
Extracts clean text and structured table content from semi-structured HTML.
"""

import re
import glob
import json
import traceback
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "clean_text"
LOG_PATH = OUTPUT_DIR / "parse_log.json"

from config.companies import COMPANIES
from page_markers import insert_page_boundaries, number_pages


def get_filing_files(company_prefix: str) -> list[Path]:
    """Return all .htm/.html files matching a company prefix."""
    htm_files = DATA_DIR.glob(f"{company_prefix}*_424H.htm")
    html_files = DATA_DIR.glob(f"{company_prefix}*_424H.html")
    return sorted(set(htm_files) | set(html_files))


def strip_sec_wrapper(raw: str) -> str:
    """
    Remove the SEC SGML envelope (<DOCUMENT>...<TEXT>...</TEXT>), leaving
    only the real HTML. Bounded to the FIRST <TEXT>...</TEXT> block, since
    a raw SEC full-submission file can bundle multiple <DOCUMENT> blocks
    (exhibits, graphics, other attachments) after the main filing - an
    unbounded match would pull all of that trailing content in too.
    """
    match = re.search(r"<TEXT>(.*?)</TEXT>", raw, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
 
    # Fallback: no closing </TEXT> found (shouldn't normally happen, but
    # don't silently return the whole raw submission unbounded either)
    match = re.search(r"<TEXT>(.*)", raw, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else raw


def parse_table(table_tag) -> list[list[str]]:
    """Convert a <table> element into a list of rows (each row is a list of cell strings)."""
    rows = []
    for tr in table_tag.find_all("tr"):
        cells = [td.get_text(separator=" ", strip=True) for td in tr.find_all(["td", "th"])]
        # Skip rows that are entirely whitespace/empty
        if any(c for c in cells):
            rows.append(cells)
    return rows


def table_to_text(rows: list[list[str]]) -> str:
    """Render table rows as pipe-delimited text for inclusion in clean text."""
    return "\n".join(" | ".join(row) for row in rows)


def clean_html(html: str) -> dict:
    """
    Parse HTML and return:
      - clean_text: plain text with tables rendered inline
      - tables: list of dicts with {index, rows}
    """
    soup = BeautifulSoup(html, "lxml")

    # Mark page boundaries first: a boundary can sit on a <table> or <img>,
    # which are removed or flattened below.
    page_style = insert_page_boundaries(soup)

    # Remove script/style/img tags — they add no textual value
    for tag in soup.find_all(["script", "style", "img"]):
        tag.decompose()

    tables_data = []
    table_index = 0

    # Replace each table with a plain-text placeholder so it stays in flow
    for table in soup.find_all("table"):
        rows = parse_table(table)
        if rows:
            tables_data.append({"index": table_index, "rows": rows})
            placeholder = soup.new_tag("p")
            placeholder.string = f"[TABLE_{table_index}]\n{table_to_text(rows)}\n[/TABLE_{table_index}]"
            table.replace_with(placeholder)
            table_index += 1
        else:
            table.decompose()

    # Extract text from the body
    body = soup.find("body") or soup
    raw_text = body.get_text(separator="\n", strip=True)

    num_pages = 0
    if page_style != "none":
        raw_text, num_pages = number_pages(raw_text)

    # Collapse excessive blank lines (3+ → 2)
    clean_text = re.sub(r"\n{3,}", "\n\n", raw_text)
    # Decode common HTML entities that BeautifulSoup may leave
    clean_text = clean_text.replace("\xa0", " ").strip()

    return {
        "clean_text": clean_text,
        "tables": tables_data,
        "num_pages": num_pages,
    }


def parse_filing(filepath: Path) -> dict:
    """Parse a single .htm filing and return structured data."""
    raw = filepath.read_text(encoding="utf-8", errors="replace")
    html = strip_sec_wrapper(raw)
    parsed = clean_html(html)

    # Derive metadata from filename: COMPANY_DATE_TYPE.htm
    parts = filepath.stem.split("_")
    # Date is the segment matching YYYY-MM-DD
    date_str = next((p for p in parts if re.match(r"\d{4}-\d{2}-\d{2}", p)), "unknown")

    return {
        "filename": filepath.name,
        "filing_date": date_str,
        "clean_text": parsed["clean_text"],
        "tables": parsed["tables"],
        "num_tables": len(parsed["tables"]),
        "text_length": len(parsed["clean_text"]),
        "page_style": parsed["page_style"],
        "num_pages": parsed["num_pages"],
    }


def process_company(label: str, prefix: str) -> tuple[pd.DataFrame, list[dict]]:
    """
    Parse all filings for a company and return a summary DataFrame,
    plus a list of per-file log entries (including any errors). A
    failure on one file is caught and logged rather than stopping
    the rest of the batch.
    """
    files = get_filing_files(prefix)
    if not files:
        print(f"  [WARN] No files found for {label} (prefix: {prefix})")
        return pd.DataFrame(), []
 
    records = []
    log_entries = []
 
    for f in files:
        print(f"  Parsing: {f.name}")
        try:
            result = parse_filing(f)
            records.append({
                "company": label,
                "filename": result["filename"],
                "filing_date": result["filing_date"],
                "text_length": result["text_length"],
                "num_tables": result["num_tables"],
                "page_style": result["page_style"],
                "num_pages": result["num_pages"],
            })
 
            # Save clean text to a .txt file alongside the source
            out_txt = OUTPUT_DIR / f.name.replace(".htm", "_clean.txt").replace(".html", "_clean.txt")
            out_txt.write_text(result["clean_text"], encoding="utf-8")
 
            log_entries.append({
                "company": label,
                "filename": f.name,
                "status": "ok",
                "text_length": result["text_length"],
                "num_tables": result["num_tables"],
                "page_style": result["page_style"],
                "num_pages": result["num_pages"],
            })
 
        except Exception as e:
            print(f"    ERROR parsing {f.name}: {type(e).__name__}: {e}")
            log_entries.append({
                "company": label,
                "filename": f.name,
                "status": "error",
                "error": f"{type(e).__name__}: {e}",
                "traceback": traceback.format_exc(),
            })
            # Continue to the next file rather than stopping the batch
 
    return pd.DataFrame(records), log_entries


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_dfs = []
    all_log_entries = []
 
    for label, prefix in COMPANIES.items():
        print(f"\nProcessing {label}...")
        df, log_entries = process_company(label, prefix)
        all_dfs.append(df)
        all_log_entries.extend(log_entries)
 
    summary = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
    summary_path = OUTPUT_DIR / "parsed_filings_summary.csv"
    summary.to_csv(summary_path, index=False)
 
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(all_log_entries, f, indent=2)
 
    n_ok = sum(1 for e in all_log_entries if e["status"] == "ok")
    n_err = sum(1 for e in all_log_entries if e["status"] == "error")
 
    print(f"\n{'='*60}")
    print(f"Parsing complete. {n_ok} succeeded, {n_err} failed.")
    print(f"Summary saved to: {summary_path}")
    print(f"Per-file log saved to: {LOG_PATH}")
    if not summary.empty:
        print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
