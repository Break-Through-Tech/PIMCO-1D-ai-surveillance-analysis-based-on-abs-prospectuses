"""
Milestone 1 — Metadata Extractor
Extracts structured metadata from clean text files and builds the index DataFrame.
"""

import re
import pandas as pd
from pathlib import Path

CLEAN_DIR = Path(__file__).parent.parent / "data" / "clean_text"
OUTPUT_DIR = Path(__file__).parent.parent / "data"

# ---------------------------------------------------------------------------
# Company config: label, filename prefix, asset_type group
# ---------------------------------------------------------------------------
COMPANIES = {
    "TOYOTA":           ("TOYOTA_AUTO_FINANCE_RECEIVABLES_LLC",          "auto_loans"),
    "HYUNDAI":          ("HYUNDAI_ABS_FUNDING_LLC",                       "auto_loans"),
    "CARMAX":           ("CARMAX_AUTO_FUNDING_LLC",                       "auto_loans_subprime"),
    "HARLEY_DAVIDSON":  ("HARLEY-DAVIDSON_CUSTOMER_FUNDING_CORP_",        "motorcycle_loans"),
    "AFS_SENSUB":       ("AFS_SENSUB_CORP_",                              "auto_loans_subprime"),
    "ALLY":             ("Ally_Auto_Assets_LLC",                          "auto_loans"),
    "AMERICAN_EXPRESS": ("AMERICAN_EXPRESS_CREDIT_ACCOUNT_MASTER_TRUST",  "credit_card_revolving"),
    "AMERICAN_HONDA":   ("AMERICAN_HONDA_RECEIVABLES_LLC",                "auto_loans"),
    "BMW":              ("BMW_AUTO_LEASING_LLC",                          "auto_leases"),
    "BRIDGECREST":      ("Bridgecrest_Auto_Funding_LLC",                  "auto_loans_subprime"),
    "FORD":             ("FORD_CREDIT_AUTO_RECEIVABLES_TWO_LLC",          "auto_loans"),
    "SANTANDER":        ("SANTANDER_DRIVE_AUTO_RECEIVABLES_LLC",          "auto_loans_subprime"),
    "VERIZON":          ("Verizon_ABS_II_LLC",                            "device_payment_revolving"),
    "WELLS_FARGO":      ("WELLS_FARGO_COMMERCIAL_MORTGAGE_SECURITIES_INC","cmbs"),
    "WORLD_OMNI":       ("WORLD_OMNI_AUTO_RECEIVABLES_LLC",               "auto_loans"),
}


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------
def first_match(patterns: list[str], text: str, flags=re.IGNORECASE) -> str | None:
    """Return the first captured group from the first matching pattern."""
    for pat in patterns:
        m = re.search(pat, text, flags)
        if m:
            return m.group(1).strip()
    return None


def clean_dollar(val: str | None) -> str | None:
    """Normalise a dollar string: remove commas, keep $ sign."""
    if val is None:
        return None
    return re.sub(r",", "", val.strip())


def clean_number(val: str | None) -> str | None:
    if val is None:
        return None
    return re.sub(r",", "", val.strip())


# ---------------------------------------------------------------------------
# Field extractors
# ---------------------------------------------------------------------------
def extract_deal_name(text: str) -> str | None:
    patterns = [
        # "Issuing Entity |  | <Name>, a Delaware..."
        r"Issuing Entity\s*\|[^|]*\|\s*([A-Z][^\n,|]{10,80}(?:Trust|LLC|Corp\.?))",
        # Name on its own line just before "Issuing Entity"
        r"((?:[A-Z][a-zA-Z0-9 \-]+\n){1,3}(?:Owner |Receivables |Automobile |Motorcycle |Vehicle |Auto |Lease )?Trust\s+\d{4}-[A-Z0-9]+)\s*\n\s*Issuing Entity",
        # Headline: "<Name>\nIssuing Entity"
        r"([A-Z][A-Za-z0-9 \-]+(?:Trust|LLC)\s+\d{4}-[A-Z0-9]+)\s*\n\s*Issuing Entity",
        # "AmeriCredit Automobile Receivables Trust\n2024-1\nIssuing Entity"
        r"([A-Z][A-Za-z ]+(?:Trust|LLC))\s*\n\s*(\d{4}-\d+)\s*\nIssuing Entity",
    ]
    # Try combined name+year pattern first
    m = re.search(
        r"([A-Z][A-Za-z0-9 \-]+(?:Trust|LLC))\s*\n\s*(\d{4}-[A-Z0-9]+)\s*\n\s*Issuing Entity",
        text, re.IGNORECASE
    )
    if m:
        return f"{m.group(1).strip()} {m.group(2).strip()}"

    m = re.search(
        r"([A-Z][A-Za-z0-9 \-]+(?:Trust|LLC)\s+\d{4}-[A-Z0-9]+)\s*\n\s*Issuing Entity",
        text, re.IGNORECASE
    )
    if m:
        return m.group(1).strip()

    # Table-style: "Issuing Entity |  | <Name>, a Delaware..."
    m = re.search(r"Issuing Entity\s*\|[^|]*\|\s*([^\n,|]{10,80}(?:Trust|LLC))", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    return None


def extract_cik(text: str) -> str | None:
    patterns = [
        r"Issuing Entity.*?CIK(?:\s*No\.?|:)\s*([\d]+)",
        r"CIK(?:\s*No\.?|:)\s*([\d]+)\s*\nIssuing Entity",
        r"\(CIK(?:\s*No\.?|:)\s*([\d]+)\)\s*\nIssuing Entity",
        r"Issuing Entity.*?\(CIK(?:\s*No\.?|:)\s*([\d]+)\)",
    ]
    return first_match(patterns, text, re.IGNORECASE | re.DOTALL)


def extract_registration_number(text: str) -> str | None:
    patterns = [
        r"Registration(?:\s+Statement)?\s+No[s]?\.?\s*([\d\-]+)",
        r"Registration\s+File\s+No\.?:?\s*([\d\-]+)",
    ]
    return first_match(patterns, text)


def extract_depositor(text: str) -> str | None:
    patterns = [
        r"Depositor\s*\(CIK[^)]*\)\s*\n([A-Z][A-Za-z ,\.]+(?:LLC|Corp\.?|Inc\.?))",
        r"([A-Z][A-Za-z ,\.]+(?:LLC|Corp\.?|Inc\.?))\s*\nDepositor",
        r"([A-Z][A-Za-z ,\.]+(?:LLC|Corp\.?|Inc\.?))[^\n]*Depositor",
        r"Depositor\s*\|[^|]*\|\s*([A-Z][A-Za-z ,\.]+(?:LLC|Corp\.?|Inc\.?))",
    ]
    return first_match(patterns, text)


def extract_sponsor(text: str) -> str | None:
    patterns = [
        r"Sponsor(?:,?[A-Za-z ,]*)?(?:and|&)[A-Za-z ,]*Servicer[^\n]*\n([A-Z][A-Za-z ,\.]+(?:LLC|Corp\.?|Inc\.?|Corporation))",
        r"([A-Z][A-Za-z ,\.]+(?:LLC|Corp\.?|Inc\.?|Corporation))[^\n]*\nSponsor(?:,? and Servicer)?",
        r"Sponsor(?:,?[A-Za-z ,]*)?Servicer\s*\(CIK[^)]*\)\s*\n([A-Z][A-Za-z ,\.]+)",
        r"Sponsor and Servicer\s*\|[^|]*\|\s*([A-Z][A-Za-z ,\.]+(?:LLC|Corp\.?|Inc\.?|Corporation))",
    ]
    return first_match(patterns, text)


def extract_cutoff_date(text: str) -> str | None:
    patterns = [
        # "Cutoff Date\nApril 14, 2024" (Toyota, AFS SenSub, World Omni)
        r"[Cc]utoff [Dd]ate\s*\n([A-Z][a-z]+ \d{1,2},? \d{4})",
        # "Cutoff Date ... close of business on February 29, 2024"
        r"[Cc]utoff [Dd]ate[^\n]*?(?:is|was|of|on)\s+(?:the\s+)?(?:close of business on\s+)?([A-Z][a-z]+ \d{1,2},? \d{4})",
        # "as of ... February 29, 2024 (the cutoff date)"
        r"as of (?:the )?(?:close of business on )?([A-Z][a-z]+ \d{1,2},? \d{4})(?:,? the cutoff date| \(the cutoff date\))",
        # "received after March 31, 2024, which we refer to as the cut-off date" (Bridgecrest, Santander, Ford)
        r"received after ([A-Z][a-z]+ \d{1,2},? \d{4}), which we refer to as the[^\n]*cut.off date",
        # "after the close of business on February 5, 2024, which we refer to herein as the cut-off date" (Hyundai)
        r"after the close of business on ([A-Z][a-z]+ \d{1,2},? \d{4})[^\n]*cut.off date",
        # "automobile loan contracts as of April 14, 2024, or the cutoff date" (AFS SenSub)
        r"(?:automobile loan contracts|receivables|contracts) as of ([A-Z][a-z]+ \d{1,2},? \d{4}),? or the cutoff date",
        # CMBS: "cut-off date" near a date
        r"[Cc]ut-off [Dd]ate[^\n]*?(?:is|was|of)\s+([A-Z][a-z]+ \d{1,2},? \d{4})",
    ]
    return first_match(patterns, text)


def extract_total_balance(text: str) -> str | None:
    patterns = [
        r"Total Principal Balance\s*\|[^|]*\|\s*(\$[\d,\.]+)",
        r"Aggregate(?:\s+Starting|\s+Amount Financed|\s+Outstanding)?\s+Principal Balance\s*\|[^|]*\|\s*(\$[\d,\.]+)",
        r"an aggregate (?:outstanding |principal )?balance of (\$[\d,\.]+)",
        r"an aggregate principal balance of (\$[\d,\.]+)",
        r"initial (?:aggregate )?(?:receivables )?principal balance[^\$]*(\$[\d,\.]+)",
        r"initial pool balance\s*\n[^\$]*(\$[\d,\.]+)",
        r"pool balance[^\$\n]*(\$[\d,\.]+)",
    ]
    val = first_match(patterns, text)
    return clean_dollar(val)


def extract_num_receivables(text: str) -> str | None:
    patterns = [
        r"Number of (?:Receivables|Contracts(?: in Pool)?|Loans?)\s*\|[^|]*\|\s*([\d,]+)",
        r"Number\s*\n\s*of receivables\s*\|\s*([\d,]+)",
        r"\|\s*Number of (?:Receivables|Contracts)\s*\|\s*([\d,]+)",
        r"Number of Contracts\s*\|\s*\?\s*\|\s*\?\s*\|\s*([\d,]+)",
        # Ford: "Number of receivables | 38,854" (no extra pipes)
        r"^Number of receivables\s*\|\s*([\d,]+)",
    ]
    val = first_match(patterns, text, re.IGNORECASE | re.MULTILINE)
    return clean_number(val)


def extract_avg_balance(text: str) -> str | None:
    patterns = [
        r"Average Principal Balance\s*\|[^|]*\|\s*(\$[\d,\.]+)",
        r"Average Amount Financed\s*\|[^|]*\|\s*(\$[\d,\.]+)",
        r"Average\s*\n\s*principal balance\s*\|\s*(\$[\d,\.]+)",
        r"Average Principal Balance\s*\|\s*\?\s*\|\s*\?\s*\|\s*(\$[\d,\.]+)",
    ]
    val = first_match(patterns, text)
    return clean_dollar(val)


def extract_wa_apr(text: str) -> str | None:
    patterns = [
        r"Weighted Average APR[^\|]*\|[^|]*\|\s*([\d\.]+)\s*%",
        r"Weighted Average APR of all Receivables[^\|]*\|[^|]*\|\s*([\d\.]+)",
        r"weighted average annual percentage rate[^\d]*([\d\.]+)%",
        r"Weighted\s*\n\s*average annual percentage rate[^\|]*\|\s*([\d\.]+)%",
        r"weighted average contract (?:interest )?rate[^\d]*([\d\.]+)%",
        r"Weighted Average Contract(?:\s+Interest)? Rate[^\|]*\|[^|]*\|\s*([\d\.]+)\s*%",
        r"Weighted Average Contract Interest Rate\s*\|\s*\?\s*\|\s*\?\s*\|\s*([\d\.]+)%",
        # Ford: "Weighted average APR | 4.80%"
        r"^Weighted average APR\s*\|\s*([\d\.]+)%",
        # CMBS: "Weighted average Interest Rate | 6.4863%"
        r"Weighted average Interest Rate\s*\|\s*([\d\.]+)%",
    ]
    return first_match(patterns, text, re.IGNORECASE | re.MULTILINE)


def extract_wa_fico(text: str) -> str | None:
    patterns = [
        r"Weighted Average FICO[^\|]*\|[^|]*\|\s*([\d\.]+)",
        r"weighted average (?:custom score of \d+ and a )?weighted average credit bureau score of ([\d\.]+)",
        r"weighted average FICO[^\d]*([\d\.]+)",
        r"non-zero weighted average FICO[^\d]*([\d\.]+)",
        r"weighted average FICO\S* score at origination of approximately ([\d\.]+)",
        # Ford: "Weighted average FICO r score at origination | 756"
        r"^Weighted average FICO[^\n\|]*\|\s*([\d\.]+)",
    ]
    return first_match(patterns, text, re.IGNORECASE | re.MULTILINE)


def extract_wa_original_term(text: str) -> str | None:
    patterns = [
        r"Weighted Average Original(?:\s+Number of Scheduled Payments|\s+Term(?:\s+to Maturity)?)[^\|]*\|[^|]*\|\s*([\d\.]+)",
        r"Weighted Average Original Term \(In Months\)[^\|]*\|[^|]*\|\s*([\d\.]+)",
        r"Weighted\s*\n\s*average original\s*\n\s*term to maturity[^\|]*\|\s*([\d\.]+)",
        r"weighted average original term(?:\s+to maturity)? of approximately ([\d\.]+) months",
        r"weighted average original term to maturity[^\d]*([\d\.]+) months",
        r"Weighted Average Original Term to Maturity[^\|]*\|[^|]*\|\s*([\d\.]+)",
        # Ford: "Weighted average original term | 63.7 months"
        r"^Weighted average original term\s*\|\s*([\d\.]+)",
        # CMBS
        r"Weighted average original term to maturity\s*\|\s*(\d+) months",
    ]
    return first_match(patterns, text, re.IGNORECASE | re.MULTILINE)


def extract_wa_remaining_term(text: str) -> str | None:
    patterns = [
        r"Weighted Average Remaining(?:\s+Number of Scheduled Payments|\s+Term(?:\s+to Maturity)?)[^\|]*\|[^|]*\|\s*([\d\.]+)",
        r"Weighted Average Remaining Term \(In Months\)[^\|]*\|[^|]*\|\s*([\d\.]+)",
        r"Weighted\s*\n\s*average remaining\s*\n\s*term to maturity[^\|]*\|\s*([\d\.]+)",
        r"weighted average remaining term(?:\s+to maturity)? of approximately ([\d\.]+) months",
        r"weighted average remaining term to maturity[^\d]*([\d\.]+) months",
        r"Weighted Average Remaining Term to Maturity[^\|]*\|[^|]*\|\s*([\d\.]+)",
        # Ford: "Weighted average remaining term | 55.8 months"
        r"^Weighted average remaining term\s*\|\s*([\d\.]+)",
        # CMBS
        r"Weighted average remaining term to maturity\s*\|\s*(\d+) months",
    ]
    return first_match(patterns, text, re.IGNORECASE | re.MULTILINE)


def extract_aggregate_principal(text: str) -> str | None:
    """Extract the headline deal size (base/smaller scenario)."""
    patterns = [
        r"^\$?([\d,]+(?:\.\d+)?)\s*\(1\)\s*\n",
        r"aggregate initial principal amount of (?:the notes(?: is)?|notes will be) \$?([\d,]+(?:\.\d+)?)\b",
        r"^\$([\d,]+,000)\s*\n.*?(?:Asset.Backed Notes|Automobile Receivables|Motorcycle Contract)",
    ]
    # Prefer the first dollar amount on the cover page (within first 3000 chars)
    cover = text[:3000]
    m = re.search(r"\$([\d,]+,000)(?:\s*\(1\))?", cover)
    if m:
        return clean_dollar("$" + m.group(1))
    return None


def extract_first_payment_date(text: str) -> str | None:
    patterns = [
        r"[Ff]irst payment date (?:will be|is) ([A-Z][a-z]+ \d{1,2},? \d{4})",
        r"[Ff]irst payment date\s*\n([A-Z][a-z]+ \d{1,2},? \d{4})",
        r"beginning (?:on )?([A-Z][a-z]+ \d{1,2},? \d{4})",
        r"starting (?:on )?([A-Z][a-z]+ \d{1,2},? \d{4})",
        r"[Ff]irst [Pp]ayment [Dd]ate is ([A-Z][a-z]+ \d{1,2},? \d{4})",
    ]
    return first_match(patterns, text)


def extract_credit_enhancement(text: str) -> str | None:
    """Extract credit enhancement types as a comma-separated string."""
    enhancements = []
    checks = [
        (r"reserve (?:account|fund)", "reserve account"),
        (r"overcollaterali[sz]ation", "overcollateralization"),
        (r"subordination", "subordination"),
        (r"excess (?:interest|spread|cash\s*flow)", "excess interest/spread"),
        (r"yield supplement", "yield supplement OC"),
    ]
    for pattern, label in checks:
        if re.search(pattern, text[:5000], re.IGNORECASE):
            enhancements.append(label)
    return ", ".join(enhancements) if enhancements else None


# BMW-specific
def extract_securitization_value(text: str) -> str | None:
    m = re.search(r"aggregate securitization value[^\$]*(\$[\d,\.]+)", text, re.IGNORECASE)
    return clean_dollar(m.group(1)) if m else None


def extract_residual_value(text: str) -> str | None:
    m = re.search(r"aggregate residual value[^\$]*(\$[\d,\.]+)", text, re.IGNORECASE)
    return clean_dollar(m.group(1)) if m else None


# AmEx-specific
def extract_total_trust_receivables(text: str) -> str | None:
    # "Total receivables in the trust:\n$26,842,786,830"
    m = re.search(r"Total receivables in the trust[^\$\n]*\n\$?([\d,]+)", text, re.IGNORECASE)
    if m:
        return clean_dollar("$" + m.group(1))
    # inline: "Total receivables in the trust: $26,842,786,830"
    m = re.search(r"Total receivables in the trust[^\$]*\$([ \d,]+)", text, re.IGNORECASE)
    return clean_dollar("$" + m.group(1).strip()) if m else None


def extract_num_accounts(text: str) -> str | None:
    # "Accounts designated to the trust:\n14,909,276"
    m = re.search(r"Accounts designated to the trust[^\d\n]*\n([\d,]+)", text, re.IGNORECASE)
    if m:
        return clean_number(m.group(1))
    m = re.search(r"Accounts designated to the trust[^\d]*([\d,]{5,})", text, re.IGNORECASE)
    return clean_number(m.group(1)) if m else None


# CMBS-specific
def extract_num_loans(text: str) -> str | None:
    m = re.search(r"Number of mortgage loans\s*\|\s*([\d,]+)", text, re.IGNORECASE)
    return clean_number(m.group(1)) if m else None


def extract_num_properties(text: str) -> str | None:
    m = re.search(r"Number of mortgaged properties\s*\|\s*([\d,]+)", text, re.IGNORECASE)
    return clean_number(m.group(1)) if m else None


def extract_wa_ltv(text: str) -> str | None:
    patterns = [
        r"Weighted average Cut-off Date LTV Ratio[^\d]*([\d\.]+)%",
        r"^\s*\|\s*Weighted average Cut-off Date LTV Ratio[^\|]*\|\s*([\d\.]+)%",
    ]
    val = first_match(patterns, text, re.IGNORECASE | re.MULTILINE)
    return val + "%" if val else None


def extract_wa_dscr(text: str) -> str | None:
    patterns = [
        r"Weighted average U/W NCF DSCR[^\d]*([\d\.]+)x",
        r"^\s*\|\s*Weighted average U/W NCF DSCR[^\|]*\|\s*([\d\.]+)x",
    ]
    val = first_match(patterns, text, re.IGNORECASE | re.MULTILINE)
    return val + "x" if val else None


# ---------------------------------------------------------------------------
# Per-filing parser
# ---------------------------------------------------------------------------
def extract_metadata(filepath: Path, company: str, asset_type: str) -> dict:
    text = filepath.read_text(encoding="utf-8", errors="replace")

    parts = filepath.stem.split("_")
    filing_date = next((p for p in parts if re.match(r"\d{4}-\d{2}-\d{2}", p)), "unknown")

    record = {
        "company":                  company,
        "filename":                 filepath.name,
        "filing_date":              filing_date,
        "asset_type":               asset_type,
        "deal_name":                extract_deal_name(text),
        "issuing_entity_cik":       extract_cik(text),
        "registration_number":      extract_registration_number(text),
        "depositor":                extract_depositor(text),
        "sponsor_servicer":         extract_sponsor(text),
        "aggregate_principal_amount": extract_aggregate_principal(text),
        "first_payment_date":       extract_first_payment_date(text),
        "credit_enhancement_types": extract_credit_enhancement(text),
        # Pool fields — auto/motorcycle loans
        "cutoff_date":              None,
        "total_principal_balance":  None,
        "number_of_receivables":    None,
        "avg_principal_balance":    None,
        "wa_apr":                   None,
        "wa_fico":                  None,
        "wa_original_term":         None,
        "wa_remaining_term":        None,
        # BMW lease fields
        "aggregate_securitization_value": None,
        "aggregate_residual_value":       None,
        # AmEx fields
        "total_trust_receivables":  None,
        "number_of_accounts":       None,
        # CMBS fields
        "number_of_loans":          None,
        "number_of_properties":     None,
        "wa_ltv":                   None,
        "wa_dscr":                  None,
    }

    if asset_type in ("auto_loans", "auto_loans_subprime", "motorcycle_loans"):
        record["cutoff_date"]             = extract_cutoff_date(text)
        record["total_principal_balance"] = extract_total_balance(text)
        record["number_of_receivables"]   = extract_num_receivables(text)
        record["avg_principal_balance"]   = extract_avg_balance(text)
        record["wa_apr"]                  = extract_wa_apr(text)
        record["wa_fico"]                 = extract_wa_fico(text)
        record["wa_original_term"]        = extract_wa_original_term(text)
        record["wa_remaining_term"]       = extract_wa_remaining_term(text)

    elif asset_type == "auto_leases":
        record["cutoff_date"]                   = extract_cutoff_date(text)
        record["aggregate_securitization_value"] = extract_securitization_value(text)
        record["aggregate_residual_value"]       = extract_residual_value(text)
        record["wa_original_term"]               = extract_wa_original_term(text)
        record["wa_remaining_term"]              = extract_wa_remaining_term(text)

    elif asset_type == "credit_card_revolving":
        record["total_trust_receivables"] = extract_total_trust_receivables(text)
        record["number_of_accounts"]      = extract_num_accounts(text)

    elif asset_type == "cmbs":
        record["cutoff_date"]         = extract_cutoff_date(text)
        record["total_principal_balance"] = extract_total_balance(text)
        record["number_of_loans"]     = extract_num_loans(text)
        record["number_of_properties"] = extract_num_properties(text)
        record["wa_apr"]              = extract_wa_apr(text)
        record["wa_original_term"]    = extract_wa_original_term(text)
        record["wa_remaining_term"]   = extract_wa_remaining_term(text)
        record["wa_ltv"]              = extract_wa_ltv(text)
        record["wa_dscr"]             = extract_wa_dscr(text)

    return record


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    records = []
    for company, (prefix, asset_type) in COMPANIES.items():
        files = sorted(CLEAN_DIR.glob(f"{prefix}*_clean.txt"))
        if not files:
            print(f"  [WARN] No clean files found for {company}")
            continue
        print(f"\nProcessing {company} ({len(files)} files)...")
        for f in files:
            print(f"  {f.name}")
            records.append(extract_metadata(f, company, asset_type))

    df = pd.DataFrame(records)

    # Column order
    cols = [
        "company", "deal_name", "asset_type", "filing_date", "cutoff_date",
        "issuing_entity_cik", "registration_number", "depositor", "sponsor_servicer",
        "aggregate_principal_amount",
        "total_principal_balance", "number_of_receivables", "avg_principal_balance",
        "wa_apr", "wa_fico", "wa_original_term", "wa_remaining_term",
        "aggregate_securitization_value", "aggregate_residual_value",
        "total_trust_receivables", "number_of_accounts",
        "number_of_loans", "number_of_properties", "wa_ltv", "wa_dscr",
        "first_payment_date", "credit_enhancement_types", "filename",
    ]
    df = df[cols]

    out_path = OUTPUT_DIR / "filings_index.csv"
    df.to_csv(out_path, index=False)

    print(f"\n{'='*60}")
    print(f"Index table saved to: {out_path}")
    print(f"Total rows: {len(df)}")
    print(f"\nField coverage (non-null counts):")
    print(df.notna().sum().to_string())


if __name__ == "__main__":
    main()
