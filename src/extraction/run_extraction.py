import os
import sys
import json 
import traceback
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from html_parser import extract_filing, DATA_DIR, PROJECT_ROOT

DATA_DIR_PATH = Path(DATA_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
TEXT_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "text")
TABLES_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "tables")
LOG_PATH = os.path.join(OUTPUT_DIR, "extraction_log.json")

COMPANIES = {
    "FORD_CREDIT": "FORD_CREDIT_AUTO_RECEIVABLES_TWO_LLC",
    "WORLD_OMNI": "WORLD_OMNI_AUTO_RECEIVABLES_LLC",
    "AMERICAN_HONDA": "AMERICAN_HONDA_RECEIVABLES_LLC",
    "Ally_Auto": "Ally_Auto_Assets_LLC",
}

def get_filing_files(company_prefix):
    #Return all .htm files matching a company prefix
    return sorted(DATA_DIR_PATH.glob(f"{company_prefix}*_424H.htm"))

def process_filing(filepath):
    """
    Runs the full pipeline on a single filing: text + table extraction with position-preserving placeholder, table classification, 
    and saves output to disk.
    Returns a summary dict for logging - never raises, so one bad file doesn't stop the whole batch 
    """

    filename = os.path.basename(filepath)
    summary = {"filename": filename, "status": "ok", "error": None}
 
    try:
        result = extract_filing(filepath)
        paragraph_text = result["paragraph_text"]
        data_tables = result["data_tables"]
        toc_tables = result["toc_tables"]
        classifications = result["table_classifications"]
 
        # --- Save paragraph text (with [TABLE:id] / [TOC_TABLE:id] placeholders) ---
        text_out_path = os.path.join(
            TEXT_OUTPUT_DIR, filename.replace(".htm", ".txt").replace(".html", ".txt")
        )
        with open(text_out_path, "w", encoding="utf-8") as f:
            f.write(paragraph_text)
 
        # --- Save likely_data tables as individual CSVs, named by their
        # placeholder id so they can be looked up from the text later ---
        base_name = os.path.splitext(filename)[0]
        for table_id, df in data_tables.items():
            table_out_path = os.path.join(
                TABLES_OUTPUT_DIR, f"{base_name}__table{table_id}.csv"
            )
            df.to_csv(table_out_path, index=False)
 
        # TOC tables are kept too, in a separate subfolder, since Phase 3
        # will use these for section-boundary detection
        toc_out_dir = os.path.join(TABLES_OUTPUT_DIR, "toc")
        os.makedirs(toc_out_dir, exist_ok=True)
        for table_id, df in toc_tables.items():
            toc_out_path = os.path.join(toc_out_dir, f"{base_name}__toc{table_id}.csv")
            df.to_csv(toc_out_path, index=False)
 
        junk_count = sum(
            1 for c in classifications if c["classification"] == "likely_junk"
        )
 
        summary.update({
            "total_tables": len(classifications),
            "likely_data_count": len(data_tables),
            "likely_toc_count": len(toc_tables),
            "likely_junk_count": junk_count,
            "paragraph_text_chars": len(paragraph_text),
            "text_output": text_out_path,
        })
 
    except Exception as e:
        summary["status"] = "error"
        summary["error"] = f"{type(e).__name__}: {e}"
        summary["traceback"] = traceback.format_exc()
 
    return summary

def run_extraction(data_dir=DATA_DIR):
    """
    Walks data_dir for .htm/.html filings, processes each one, and
    writes a JSON log summarizing the results across the whole batch.
    """
    os.makedirs(TEXT_OUTPUT_DIR, exist_ok=True)
    os.makedirs(TABLES_OUTPUT_DIR, exist_ok=True)
 
    filepaths = []
    for root, _dirs, files in os.walk(data_dir):
        for fname in files:
            if fname.lower().endswith((".htm", ".html")):
                filepaths.append(os.path.join(root, fname))
 
    print(f"Found {len(filepaths)} filings under {data_dir}")
 
    results = []
    for i, filepath in enumerate(filepaths, start=1):
        print(f"[{i}/{len(filepaths)}] Processing {os.path.basename(filepath)} ...")
        summary = process_filing(filepath)
        results.append(summary)
 
        if summary["status"] == "ok":
            print(
                f"    ok - {summary['likely_data_count']} data tables, "
                f"{summary['likely_toc_count']} toc tables, "
                f"{summary['likely_junk_count']} junk tables discarded, "
                f"{summary['paragraph_text_chars']} chars of text"
            )
        else:
            print(f"    ERROR: {summary['error']}")
 
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
 
    n_ok = sum(1 for r in results if r["status"] == "ok")
    n_err = len(results) - n_ok
    print(f"\nDone. {n_ok} succeeded, {n_err} failed. Log written to {LOG_PATH}")
 
    return results

def process_company(label, prefix):
    """
    Processes every filing matching a company's filename prefix.
    Returns a list of per-file summary dicts, each tagged with the
    company label so results can be grouped/filtered later.
    """
    files = get_filing_files(prefix)
 
    if not files:
        print(f"  [WARN] No files found for {label} (prefix: {prefix})")
        return []
 
    company_results = []
    for filepath in files:
        print(f"  Parsing: {filepath.name}")
        summary = process_filing(str(filepath))
        summary["company"] = label
        company_results.append(summary)
 
        if summary["status"] == "ok":
            print(
                f"    ok - {summary['likely_data_count']} data tables, "
                f"{summary['likely_toc_count']} toc tables, "
                f"{summary['likely_junk_count']} junk tables discarded, "
                f"{summary['paragraph_text_chars']} chars of text"
            )
        else:
            print(f"    ERROR: {summary['error']}")
 
    return company_results
 
 
def run_extraction_by_company(companies=COMPANIES):
    """
    Processes every filing for every company in the COMPANIES dict,
    writes a combined JSON log, and prints a per-company summary count.
    """
    os.makedirs(TEXT_OUTPUT_DIR, exist_ok=True)
    os.makedirs(TABLES_OUTPUT_DIR, exist_ok=True)
 
    all_results = []
    for label, prefix in companies.items():
        print(f"\nProcessing {label}...")
        company_results = process_company(label, prefix)
        all_results.extend(company_results)
 
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
 
    n_ok = sum(1 for r in all_results if r["status"] == "ok")
    n_err = len(all_results) - n_ok
    print(f"\n{'=' * 60}")
    print(f"Done. {n_ok} succeeded, {n_err} failed. Log written to {LOG_PATH}")
 
    # Per-company breakdown
    for label in companies:
        company_count = sum(1 for r in all_results if r.get("company") == label)
        print(f"  {label}: {company_count} filings processed")
 
    return all_results
 

if __name__ == "__main__":
    run_extraction_by_company()