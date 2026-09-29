import re 
import pandas as pd


def classify_table(df, min_cols=3, max_nan_ratio=0.6):
    """
    classifies a single dataframe (from pd.read_html) as likely real data 
    or likely junk/layout 
    based on structural heuristics 

    returns a dict with the classification and the signals used to reach it 
    so borderline cases can be manually reviewed later.
    """
    n_rows, n_cols = df.shape

    #NaN ratio across the whole table 
    total_cells = n_rows * n_cols
    nan_cells = df.isna().sum().sum()
    nan_ratio = nan_cells / total_cells if total_cells > 0 else 1.0 

    #check for numeric/data-like content anywhere in the table 
    #numerical data such as amounts, percentages, or plain numbers
    numeric_pattern = re.compile(r"\$?\d[\d,]*\.?\d*%?")
    has_numeric_content = False

    for col in df.columns:
        col_as_str = df[col].astype(str)
        if col_as_str.str.contains(numeric_pattern).any():
            has_numeric_content = True
            break
    
    """
    Marker pattern check (generalized): a footnote/bullet row typically has
    an early cell containing ONLY a short marker token - a parenthesized
    number "(1)", a bullet "·"/"•", a dash "-", an asterisk "*", etc.
    Kept short (1-4 chars) so it doesn't accidentally match real short
    data values like class names ("A-1") or dollar signs.
    """  

    footnote_pattern = re.compile(r"^([\(\)\d]{1,4}|[·•\-\*\u2022]{1,2})$")
    is_footnote = False

    for col in df.columns:
        col_as_str = df[col].astype(str).str.strip()
        if col_as_str.str.match(footnote_pattern).any():
            is_footnote = True 
            break
    
  
    # TOC pattern check: a table of contents typically has many rows and <= 6 columns"
    # section-name-like text and another column of small integers (page
    # numbers), across many rows.
    is_toc = False
    if n_rows >= 15 and n_cols <= 6:
        for col in df.columns:
            numeric_col = pd.to_numeric(df[col], errors="coerce")
            non_null = numeric_col.dropna()
            if len(non_null) == 0:
                continue
            # mostly small whole numbers in a plausible page-number range
            looks_like_pages = (
                (non_null % 1 == 0).mean() > 0.8
                and non_null.between(1, 999).mean() > 0.8
                and (non_null.notna().sum() / n_rows) > 0.7
            )
            if not looks_like_pages:
                continue

            uniqueness_ratio = non_null.nunique() / len(non_null)
            diffs = non_null.diff().dropna()
            monotonic_ratio = (diffs >= 0).mean() if len(diffs) > 0 else 0
 
            if uniqueness_ratio > 0.6 and monotonic_ratio > 0.7:
                is_toc = True
                break

    
    """
    Literal "Table of Contents" text check - a cheap, reliable override:
    if this phrase appears anywhere in the table's own cells, treat it
    as a TOC regardless of the row-count/page-number heuristic above.
    """        
    toc_text_pattern = re.compile(r"table\s+of\s+contents", re.IGNORECASE)
    has_toc_label = False
    for col in df.columns:
        if df[col].astype(str).str.contains(toc_text_pattern).any():
            has_toc_label = True
            is_toc = True
            break  

    if is_toc:
        classification = "likely_toc"
    elif (
        n_cols >= min_cols
        and nan_ratio <= max_nan_ratio
        and has_numeric_content
        and not is_footnote
    ):
        classification = "likely_data"
    else:
        classification = "likely_junk"
    
  
    return {
        "classification": classification,
        "n_rows": n_rows,
        "n_cols": n_cols,
        "nan_ratio": round(nan_ratio, 2),
        "has_numeric_content": has_numeric_content,
        "is_footnote": is_footnote,
        "is_toc": is_toc,
        "has_toc_label": has_toc_label
    }


def filter_tables(tables):
    """
    Applies classify_table to a full list of DataFrames.
    Returns three lists:
    1. likely_data_tables 
    2. likely_junk_tables
    3. likely_toc_tables
    each as (index, dataframe, classification_info) tuples so you can trace back to the original table number for manual review 
    """

    likel_data_tables = []
    likel_junk_tables = []
    likely_toc_tables = []

    for i, df in enumerate(tables):
        info = classify_table(df)
        entry = (i, df, info)

        if info["classification"] == "likely_data":
            likel_data_tables.append(entry)
        elif info["classification"] == "likely_toc":
            likely_toc_tables.append(entry)
        else:
            likel_junk_tables.append(entry)

    return likel_data_tables, likely_toc_tables, likel_junk_tables