import re
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup

# Define base directory structure
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "clean_text"

# Exact SEC issuing entity naming prefixes
COMPANIES = {
    "AMERICAN_EXPRESS": "AMERICAN_EXPRESS_CREDIT_ACCOUNT_MASTER_TRUST",
    "BMW": "BMW_AUTO_LEASING_LLC",
    "SANTANDER": "SANTANDER_DRIVE_AUTO_RECEIVABLES_LLC",
    "VERIZON": "Verizon_ABS_II_LLC",
    "WELLS_FARGO": "WELLS_FARGO_COMMERCIAL_MORTGAGE_SECURITIES_INC",
}

def strip_sec_wrapper(raw: str) -> str:
    """Remove SEC SGML header envelope (<DOCUMENT>...<TEXT>) keeping pure HTML."""
    match = re.search(r"<TEXT>(.*)", raw, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else raw

def parse_table(table_tag) -> list[list[str]]:
    """Convert a <table> element into a list of row values."""
    rows = []
    for tr in table_tag.find_all("tr"):
        cells = [td.get_text(separator=" ", strip=True) for td in tr.find_all(["td", "th"])]
        if any(c for c in cells):
            rows.append(cells)
    return rows

def table_to_text(rows: list[list[str]]) -> str:
    """Render table rows as pipe-delimited text."""
    return "\n".join(" | ".join(row) for row in rows)

def clean_html(html: str) -> dict:
    """Parse HTML content, strip unnecessary tags, and extract structured text/tables."""
    soup = BeautifulSoup(html, "lxml")

    # Decompose script, style, and image tags
    for tag in soup.find_all(["script", "style", "img"]):
        tag.decompose()

    tables_data = []
    table_index = 0

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

    body = soup.find("body") or soup
    raw_text = body.get_text(separator="\n", strip=True)

    # Normalize spacing and HTML entity remnants
    clean_text = re.sub(r"\n{3,}", "\n\n", raw_text)
    clean_text = clean_text.replace("\xa0", " ").strip()

    return {"clean_text": clean_text, "tables": tables_data}

def parse_filing(filepath: Path) -> dict:
    """Parse a single local file and return structured clean text and metrics."""
    raw_content = filepath.read_text(encoding="utf-8", errors="replace")
    html = strip_sec_wrapper(raw_content)
    parsed = clean_html(html)

    # Derive date from filename (matches standard SEC formatting YYYY-MM-DD)
    parts = filepath.stem.split("_")
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
    """Find and process all matching local files for a single company."""
    # Matches files starting with the specific exact prefix
    matching_files = [
        f for f in DATA_DIR.glob("*")
        if f.name.lower().startswith(prefix.lower())
        and f.suffix.lower() in [".htm", ".html"]
    ]

    if not matching_files:
        print(f"  [WARN] No matching files found in '{DATA_DIR}' for {label} (prefix: {prefix})")
        return pd.DataFrame()

    records = []
    for filepath in sorted(matching_files):
        print(f"  Parsing: {filepath.name}")
        result = parse_filing(filepath)

        records.append({
            "company": label,
            "filename": result["filename"],
            "filing_date": result["filing_date"],
            "text_length": result["text_length"],
            "num_tables": result["num_tables"],
        })

        # Save clean text output
        out_txt = OUTPUT_DIR / filepath.name.replace(".htm", "_clean.txt").replace(".html", "_clean.txt")
        out_txt.write_text(result["clean_text"], encoding="utf-8")

    return pd.DataFrame(records)

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_dfs = []

    for label, prefix in COMPANIES.items():
        print(f"\nProcessing {label}...")
        df = process_company(label, prefix)
        if not df.empty:
            all_dfs.append(df)

    if all_dfs:
        summary = pd.concat(all_dfs, ignore_index=True)
        summary_path = OUTPUT_DIR / "parsed_filings_summary.csv"
        summary.to_csv(summary_path, index=False)

        print(f"\n{'='*60}")
        print(f"Parsing complete. Summary saved to: {summary_path}")
        print(summary.to_string(index=False))
    else:
        print("\nNo matching filing files were parsed. Place your .htm files in the data directory.")

if __name__ == "__main__":
    main()