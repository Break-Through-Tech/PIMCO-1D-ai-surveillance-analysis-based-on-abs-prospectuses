# ABS Prospectus Metadata Fields

Verified by inspecting clean text from all 15 companies (116 filings total) in `data/clean_text/`.
These fields form the basis for the index table in Milestone 1.

---

## Companies in the Dataset

| Company (filename prefix) | Trust Name Pattern | Asset Type | Filings |
|---|---|---|---|
| `AFS_SENSUB_CORP_` | AmeriCredit Automobile Receivables Trust | Auto loans (subprime) | 10 |
| `Ally_Auto_Assets_LLC_` | Ally Auto Receivables Trust | Auto loans | 4 |
| `AMERICAN_EXPRESS_CREDIT_ACCOUNT_MASTER_TRUST_` | American Express Credit Account Master Trust | Credit card receivables (revolving) | 5 |
| `AMERICAN_HONDA_RECEIVABLES_LLC_` | Honda Auto Receivables Owner Trust | Auto loans | 10 |
| `BMW_AUTO_LEASING_LLC_` | BMW Vehicle Lease Trust | Auto leases | 5 |
| `Bridgecrest_Auto_Funding_LLC_` | Bridgecrest Lending Auto Securitization Trust | Auto loans (subprime) | 10 |
| `CARMAX_AUTO_FUNDING_LLC_` | CarMax Select Receivables Trust | Auto loans (subprime) | 10 |
| `FORD_CREDIT_AUTO_RECEIVABLES_TWO_LLC_` | Ford Credit Auto Owner Trust | Auto loans | 9 |
| `HARLEY-DAVIDSON_CUSTOMER_FUNDING_CORP_` | Harley-Davidson Motorcycle Trust | Motorcycle loans | 3 |
| `HYUNDAI_ABS_FUNDING_LLC_` | Hyundai Auto Receivables Trust | Auto loans | 9 |
| `SANTANDER_DRIVE_AUTO_RECEIVABLES_LLC_` | Santander Drive Auto Receivables Trust | Auto loans (subprime) | 10 |
| `TOYOTA_AUTO_FINANCE_RECEIVABLES_LLC_` | Toyota Auto Receivables Owner Trust | Auto loans | 10 |
| `Verizon_ABS_II_LLC_` | Verizon Master Trust | Device payment plan agreements (revolving) | 6 |
| `WELLS_FARGO_COMMERCIAL_MORTGAGE_SECURITIES_INC_` | Wells Fargo Commercial Mortgage Trust | Commercial mortgage loans (CMBS) | 10 |
| `WORLD_OMNI_AUTO_RECEIVABLES_LLC_` | World Omni Auto Receivables Trust | Auto loans | 10 |

**Total: 116 filings**

---

## Group 1 — Auto / Motorcycle Loan ABS (11 companies, 95 filings)

Applies to: Toyota, Hyundai, CarMax, Harley-Davidson, AFS SenSub, Ally, American Honda, Bridgecrest, Ford, Santander, World Omni.

All fields confirmed present in clean text across all 11 companies.

### Deal / Identity

| Field | Description | Example |
|---|---|---|
| `deal_name` | Full name of the issuing trust | Toyota Auto Receivables 2024-B Owner Trust |
| `issuing_entity_cik` | SEC CIK number of the trust | 0002012786 |
| `depositor` | Legal name of the depositor entity | Toyota Auto Finance Receivables LLC |
| `sponsor_servicer` | Sponsor, seller, and/or servicer | Toyota Motor Credit Corporation |
| `registration_number` | SEC registration statement number | 333-259868 |
| `asset_type` | Type of underlying collateral | auto_loans / motorcycle_loans |
| `filing_date` | Date the 424H was filed (from filename) | 2024-04-18 |

### Pool / Collateral Characteristics

| Field | Description | Example | Notes |
|---|---|---|---|
| `cutoff_date` | Date the pool was frozen for statistics | February 29, 2024 | All 11 companies confirmed |
| `total_principal_balance` | Aggregate principal balance of the pool | $1,447,406,675.12 | All 11 confirmed |
| `number_of_receivables` | Count of contracts in the pool | 54,194 | All 11 confirmed |
| `avg_principal_balance` | Average principal balance per contract | $26,707.88 | All 11 confirmed |
| `wa_apr` | Weighted average annual percentage rate | 5.70% | All 11 confirmed; subprime issuers range 14–18% vs prime 5–10% |
| `wa_fico` | Weighted average FICO score of obligors | 767 | All 11 confirmed; subprime ~580–640, prime ~730–770 |
| `wa_original_term` | Weighted avg original scheduled payments (months) | 65.73 | All 11 confirmed |
| `wa_remaining_term` | Weighted avg remaining scheduled payments (months) | 54.53 | All 11 confirmed |

### Note Structure

| Field | Description | Example |
|---|---|---|
| `aggregate_principal_amount` | Total deal size (headline dollar amount) | $1,350,000,000 |
| `note_classes` | Classes of notes issued with principal amounts | A-1: $290M, A-2a: $478M, A-3: $478M, A-4: $70.2M, B: $33.8M |
| `first_payment_date` | Date of first scheduled payment to noteholders | May 15, 2024 |
| `credit_enhancement_types` | Credit enhancement mechanisms used | reserve account, overcollateralization, subordination, excess interest |

---

## Group 2 — BMW Auto Lease ABS (1 company, 5 filings)

Structurally similar to Group 1 but collateral is **closed-end retail leases**, not installment loans.

### Fields that apply unchanged
All deal/identity and note structure fields apply as-is.

### Fields that differ from Group 1

| Field | Description | Example |
|---|---|---|
| `cutoff_date` | Date the lease pool was frozen | confirmed present |
| `aggregate_securitization_value` | Aggregate securitization value of leases (replaces `total_principal_balance`) | $1,151,412,123.01 |
| `aggregate_residual_value` | Aggregate residual value of leased vehicles being financed | $596,136,269.46 (~51.77% of securitization value) |
| `wa_original_term` | Weighted avg original lease term (months) | 36 months |
| `wa_remaining_term` | Weighted avg remaining lease term (months) | 28 months |

### Fields NOT present in BMW leases
- `total_principal_balance` — replaced by `aggregate_securitization_value`
- `number_of_receivables` — not prominently disclosed in pool summary
- `avg_principal_balance` — not applicable
- `wa_apr` — leases do not carry an APR in the same sense
- `wa_fico` — not disclosed in BMW lease filings

---

## Group 3 — American Express Credit Card Master Trust (1 company, 5 filings)

**Revolving master trust** backed by credit card receivables. Structurally different from static-pool ABS.

### Fields that apply
- `deal_name`, `issuing_entity_cik`, `depositor`, `sponsor_servicer`, `registration_number`, `filing_date`
- `aggregate_principal_amount` (per series, e.g. $250,000,000 for Series 2024-2)
- `note_classes` (certificate classes A and B + collateral interest)
- `first_payment_date`

### Fields specific to AmEx (replacing pool characteristics)

| Field | Description | Example |
|---|---|---|
| `series_name` | Series identifier for this issuance | Series 2024-2 |
| `total_trust_receivables` | Total receivables in the master trust | $26,842,786,830 |
| `principal_receivables` | Principal receivables in the trust | $25,412,846,674 |
| `number_of_accounts` | Number of credit card accounts designated to the trust | 14,909,276 |
| `asset_type` | Fixed value | credit_card_revolving |

### Fields NOT present
- `cutoff_date`, `number_of_receivables`, `avg_principal_balance`, `wa_apr`, `wa_fico`, `wa_original_term`, `wa_remaining_term` — not applicable to revolving pools

---

## Group 4 — Verizon Master Trust (1 company, 6 filings)

**Revolving master trust** backed by device payment plan agreements (phone contracts). Structurally similar to AmEx.

### Fields that apply
- `deal_name`, `issuing_entity_cik`, `depositor`, `sponsor_servicer`, `registration_number`, `filing_date`
- `aggregate_principal_amount` (per series)
- `note_classes`, `first_payment_date`

### Fields specific to Verizon

| Field | Description | Example |
|---|---|---|
| `series_name` | Series identifier | Series 2024-6 |
| `asset_type` | Fixed value | device_payment_revolving |
| `anticipated_redemption_date` | Expected payoff date (distinct from final maturity) | August 20, 2027 |

### Fields NOT present
- All pool characteristic fields (`cutoff_date`, `wa_fico`, `wa_apr`, etc.) — not applicable to revolving pools

---

## Group 5 — Wells Fargo Commercial Mortgage Trust (1 company, 10 filings)

**CMBS** — completely different asset class. Collateral is commercial real estate mortgage loans, not consumer receivables.

### Fields that apply
- `deal_name`, `issuing_entity_cik`, `depositor`, `registration_number`, `filing_date`
- `aggregate_principal_amount` (initial pool balance)
- `note_classes` (certificate classes), `first_payment_date`

### Fields specific to CMBS (replacing pool characteristics)

| Field | Description | Example |
|---|---|---|
| `initial_pool_balance` | Aggregate cut-off date balance of mortgage loans | $622,662,516 |
| `number_of_loans` | Number of mortgage loans in the pool | 26 |
| `number_of_properties` | Number of mortgaged properties | 51 |
| `avg_loan_balance` | Average cut-off date balance per loan | $23,948,558 |
| `wa_interest_rate` | Weighted average mortgage interest rate | 6.4863% |
| `wa_ltv` | Weighted average loan-to-value ratio at cut-off | 56.4% |
| `wa_dscr` | Weighted average debt service coverage ratio (U/W NCF) | 1.64x |
| `wa_debt_yield` | Weighted average U/W NOI debt yield | 11.3% |
| `wa_original_term` | Weighted average original term to maturity (months) | 60 months |
| `wa_remaining_term` | Weighted average remaining term to maturity (months) | 58 months |
| `asset_type` | Fixed value | cmbs |

### Fields NOT present
- `wa_fico`, `wa_apr`, `number_of_receivables`, `avg_principal_balance` — not applicable to commercial mortgage loans

---

## Cross-Company Notes

- **Interest rates are blank** in all 424H filings across all 15 companies — pre-pricing, rates appear as `___%`. Only filled in the final 424B.
- **Dual pool scenarios** — most issuers present a base and upsize transaction. Use the base/smaller amount as the primary value.
- **Subprime vs prime** — WA FICO and WA APR differ significantly: subprime issuers (CarMax, Bridgecrest, Santander, AFS SenSub) show FICO ~580–640 and APR ~14–18%; prime issuers (Toyota, Honda, Ally) show FICO ~730–770 and APR ~5–10%.
- **Payment date** — most auto ABS pay on the 15th or 18th of each month; Harley-Davidson also uses the 15th.

---

## Proposed Index Table Schema

### Main table (Groups 1–2, auto/motorcycle/lease ABS)
```
company
deal_name
issuing_entity_cik
depositor
sponsor_servicer
filing_date
cutoff_date
registration_number
asset_type
aggregate_principal_amount
number_of_receivables
total_principal_balance
avg_principal_balance
wa_apr
wa_fico
wa_original_term
wa_remaining_term
note_classes
first_payment_date
credit_enhancement_types
filename
```

### Supplemental columns for BMW leases (Group 2)
```
aggregate_securitization_value
aggregate_residual_value
```

### Separate table or flagged rows for Groups 3–5
Groups 3 (AmEx), 4 (Verizon), and 5 (Wells Fargo) should either be stored in separate tables or included in the main table with `asset_type` as the discriminator and their unique fields stored in additional columns, with NaN for fields that don't apply.
