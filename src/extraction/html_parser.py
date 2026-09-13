import os
import io
import re 
from bs4 import BeautifulSoup
import pandas as pd 


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

def strip_sec_wrapper(raw_content):
    #ignore SEC wrapper and extract only real html tags
    match = re.search(r"<HTML>.*?</HTML>", raw_content, re.DOTALL | re.IGNORECASE)
    if match:
        raw_html = match.group(0)
    #if no wrapper found 
    else:
        raw_html = raw_content 

    return raw_html


def extract_tables(raw_html):
#pull tables from the CLEANED HTML
    try:
        return pd.read_html(io.StringIO(raw_html))
    #pandas raises this when it finds zero tables in the document
    except ValueError:
        return []

def extract_paragraph_text(raw_html):
    #extract clean paragraph text from the given html string 
    soup = BeautifulSoup(raw_html, "lxml")

    #removes the tables from the soup 
    for table in soup.find_all("table"):
        table.decompose()

    #extract the clean text 
    return soup.get_text(separator="\n", strip=True)


def extract_filing(filepath):
    #runs the full extraction pipeline on a single filing
    with open(filepath, "r", encoding="utf-8") as f:
        raw_content = f.read()
        raw_html = strip_sec_wrapper(raw_content)
        tables = extract_tables(raw_html)
        paragraph_text = extract_paragraph_text(raw_html)

    return {
        "filepath": filepath,
        "paragraph_text": paragraph_text,
        "tables": tables,
    }

if __name__ == "__main__":
    test_filename = "FORD_CREDIT_AUTO_RECEIVABLES_TWO_LLC_2024-03-11_424H.htm"
    filepath = os.path.join(DATA_DIR, test_filename)
 
    result = extract_filing(filepath)
 
    print(f"Found {len(result['tables'])} tables")
    print(f"Paragraph text length: {len(result['paragraph_text'])} chars")
    print(result["paragraph_text"][:500])