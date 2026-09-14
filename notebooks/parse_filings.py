"""
Milestone 1 — HTML Filing Parser
Parses SEC 424H filings for Toyota, Hyundai, CarMax, and Harley-Davidson.
Extracts clean text and structured table content from semi-structured HTML.
"""

import re
import glob
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "clean_text"

COMPANIES = {
    "TOYOTA": "TOYOTA_AUTO_FINANCE_RECEIVABLES_LLC",
    "HYUNDAI": "HYUNDAI_ABS_FUNDING_LLC",
    "CARMAX": "CARMAX_AUTO_FUNDING_LLC",
    "HARLEY_DAVIDSON": "HARLEY-DAVIDSON_CUSTOMER_FUNDING_CORP_",
}


def get_filing_files(company_prefix: str) -> list[Path]:
    """Return all .htm files matching a company prefix."""
    return sorted(DATA_DIR.glob(f"{company_prefix}*_424H.htm"))


def strip_sec_wrapper(raw: str) -> str:
    """Remove the SEC SGML envelope (<DOCUMENT>...<TEXT>) leaving only HTML."""
    # The actual HTML starts after <TEXT> tag
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

    # Collapse excessive blank lines (3+ → 2)
    clean_text = re.sub(r"\n{3,}", "\n\n", raw_text)
    # Decode common HTML entities that BeautifulSoup may leave
    clean_text = clean_text.replace("\xa0", " ").strip()

    return {"clean_text": clean_text, "tables": tables_data}


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
    }


def process_company(label: str, prefix: str) -> pd.DataFrame:
    """Parse all filings for a company and return a summary DataFrame."""
    files = get_filing_files(prefix)
    if not files:
        print(f"  [WARN] No files found for {label} (prefix: {prefix})")
        return pd.DataFrame()

    records = []
    for f in files:
        print(f"  Parsing: {f.name}")
        result = parse_filing(f)
        records.append({
            "company": label,
            "filename": result["filename"],
            "filing_date": result["filing_date"],
            "text_length": result["text_length"],
            "num_tables": result["num_tables"],
        })

        # Save clean text to a .txt file alongside the source
        out_txt = OUTPUT_DIR / f.name.replace(".htm", "_clean.txt")
        out_txt.write_text(result["clean_text"], encoding="utf-8")

    return pd.DataFrame(records)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_dfs = []
    for label, prefix in COMPANIES.items():
        print(f"\nProcessing {label}...")
        df = process_company(label, prefix)
        all_dfs.append(df)

    summary = pd.concat(all_dfs, ignore_index=True)
    summary_path = OUTPUT_DIR / "parsed_filings_summary.csv"
    summary.to_csv(summary_path, index=False)

    print(f"\n{'='*60}")
    print(f"Parsing complete. Summary saved to: {summary_path}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
