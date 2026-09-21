import os
import re
import io
from bs4 import BeautifulSoup
import pandas as pd
 
from table_filter import classify_table
 
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
 
 
def strip_sec_wrapper(raw_content):
    """
    SEC full-submission files wrap the real HTML in non-HTML SGML-style
    tags (<DOCUMENT>, <TYPE>, <SEQUENCE>, <TEXT>, etc). This isolates just
    the <HTML>...</HTML> portion so BeautifulSoup/pandas parse cleanly.
    Falls back to the raw content if no <HTML> tag is found.
    """
    match = re.search(r"<HTML>.*?</HTML>", raw_content, re.DOTALL | re.IGNORECASE)
    return match.group(0) if match else raw_content
 
 
def extract_tables(raw_html):
    """
    Extracts all tables from the given HTML string, in document order.
    Wrapping in io.StringIO avoids an OSError some pandas/lxml versions
    raise when passed a raw HTML string directly.
    """
    try:
        return pd.read_html(io.StringIO(raw_html))
    except ValueError:
        # pandas raises this when it finds zero tables in the document
        return []

def df_to_markdown(df, table_id, label="TABLE"):
    """
    Renders a DataFrame as a Markdown table, warpped with an ID marker 
    so the source table stays traceable back to its saved CSV/DataFrame.
    uses pandas' to_markdown() 
    """ 
    header = f"\n\n[{label}:{table_id}]\n"
    footer = f"\n[{label}:{table_id}]\n\n"

    try:
        md = df.to_markdown(index=False)
    #fallback if tabulate not imported - manual 
    except ImportError:
        cols = [str(c) for c in df.columns]
        lines = ["| " + " | ".join(cols) + " |"]
        lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
        for _, row in df.iterrows():
            lines.append("| " + " | ".join(str(v) for v in row) + " |")
        md = "\n".join(lines)
    
    return header + md + footer 


 
def extract_filing(filepath):
    """
    Runs the full extraction pipeline on a single filing:
      1. Strip the SEC wrapper
      2. Extract all tables (in document order) and classify each one
         (likely_data / likely_toc / likely_junk)
      3. Walk the soup's <table> tags in the same document order:
           - likely_data / likely_toc tables are replaced with a short
             placeholder (e.g. "[TABLE:3]") so their POSITION in the
             narrative is preserved, while the real structured content
             is kept separately as a DataFrame
           - likely_junk tables (footnotes, layout tables, page nav)
             are removed entirely so they don't pollute the text
      4. Extract the remaining paragraph text (style/script also removed)
 
    Returns a dict with:
      - paragraph_text: text with [TABLE:id] / [TOC_TABLE:id] placeholders
      - data_tables: {id: DataFrame} for likely_data tables
      - toc_tables: {id: DataFrame} for likely_toc tables
      - table_classifications: full list of (id, classification_info)
        for every table found, including junk (useful for logging/QA)
    """
    with open(filepath, "r", encoding="utf-8") as f:
        raw_content = f.read()
 
    raw_html = strip_sec_wrapper(raw_content)
    tables = extract_tables(raw_html)
 
    soup = BeautifulSoup(raw_html, "lxml")
    table_tags = soup.find_all("table")
 
    data_tables = {}
    toc_tables = {}
    table_classifications = []
 
    if len(table_tags) != len(tables):
        # Mismatch between pandas' and BeautifulSoup's table counts (rare,
        # but possible on malformed HTML). Fall back to removing all
        # tables rather than risk misaligning content with the wrong tag.
        for table_tag in table_tags:
            table_tag.decompose()
        table_classifications = [
            {"id": i, "classification": "unclassified_mismatch"}
            for i in range(len(tables))
        ]
    else:
        for i, (table_tag, df) in enumerate(zip(table_tags, tables)):
            info = classify_table(df)
            info_with_id = {"id": i, **info}
            table_classifications.append(info_with_id)
 
            if info["classification"] == "likely_data":
                data_tables[i] = df
                placeholder = soup.new_tag("p")
                placeholder.string = df_to_markdown(df, i, label="TABLE")
                table_tag.replace_with(placeholder)
            elif info["classification"] == "likely_toc":
                toc_tables[i] = df
                placeholder = soup.new_tag("p")
                placeholder.string = df_to_markdown(df, i, label="TOC_TABLE")
                table_tag.replace_with(placeholder)
            else:
                table_tag.decompose()
 
    for tag in soup(["style", "script"]):
        tag.decompose()
 
    paragraph_text = soup.get_text(separator="\n", strip=True)
 
    return {
        "filepath": filepath,
        "paragraph_text": paragraph_text,
        "data_tables": data_tables,
        "toc_tables": toc_tables,
        "table_classifications": table_classifications,
    }
 
 
if __name__ == "__main__":
    test_filename = "FORD_CREDIT_AUTO_RECEIVABLES_TWO_LLC_2024-03-11_424H.htm"
    filepath = os.path.join(DATA_DIR, test_filename)
 
    result = extract_filing(filepath)
 
    print(f"Data tables kept: {len(result['data_tables'])}")
    print(f"TOC tables kept: {len(result['toc_tables'])}")
    print(f"Paragraph text length: {len(result['paragraph_text'])} chars")
    print(result["paragraph_text"][:800])