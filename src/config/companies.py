"""
Shared company registry: maps a short label to the filename prefix used
to identify that company's filings in data/. Used by extraction and
discovery scripts so both stay in sync with the same company list.
"""

COMPANIES = {
    "FORD_CREDIT": "FORD_CREDIT_AUTO_RECEIVABLES_TWO_LLC",
    "WORLD_OMNI": "WORLD_OMNI_AUTO_RECEIVABLES_LLC",
    "AMERICAN_HONDA": "AMERICAN_HONDA_RECEIVABLES_LLC",
    "Ally_Auto": "Ally_Auto_Assets_LLC",
    "AMERICAN_EXPRESS": "AMERICAN_EXPRESS_CREDIT_ACCOUNT_MASTER_TRUST",
    "BMW": "BMW_AUTO_LEASING_LLC",
    "SANTANDER": "SANTANDER_DRIVE_AUTO_RECEIVABLES_LLC",
    "VERIZON": "Verizon_ABS_II_LLC",
    "WELLS_FARGO": "WELLS_FARGO_COMMERCIAL_MORTGAGE_SECURITIES_INC",
    "TOYOTA": "TOYOTA_AUTO_FINANCE_RECEIVABLES_LLC",
    "HYUNDAI": "HYUNDAI_ABS_FUNDING_LLC",
    "CARMAX": "CARMAX_AUTO_FUNDING_LLC",
    "HARLEY_DAVIDSON": "HARLEY-DAVIDSON_CUSTOMER_FUNDING_CORP_",
    "BRIDGECREST": "Bridgecrest_Auto_Funding_LLC",
    "AFS": "AFS_SENSUB_CORP",
}

ASSET_TYPES = {
    "FORD_CREDIT": "auto_loans",
    "WORLD_OMNI": "auto_loans",
    "AMERICAN_HONDA": "auto_loans",
    "Ally_Auto": "auto_loans",
    "AMERICAN_EXPRESS": "credit_card_revolving",
    "BMW": "auto_leases",
    "SANTANDER": "auto_loans_subprime",
    "VERIZON": "device_payment_revolving",
    "WELLS_FARGO": "cmbs",
    "TOYOTA": "auto_loans",
    "HYUNDAI": "auto_loans",
    "CARMAX": "auto_loans_subprime",
    "HARLEY_DAVIDSON": "motorcycle_loans",
    "BRIDGECREST": "auto_loans_subprime",
    "AFS": "auto_loans_subprime",
}