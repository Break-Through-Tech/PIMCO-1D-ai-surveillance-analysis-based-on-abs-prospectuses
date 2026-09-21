# ABS Prospectus Metadata Fields

Discovered by inspecting raw HTML filings for all companies in `data/`.
These fields form the basis for the index table in Milestone 1.

---

## Companies in the Dataset

| Company (filename prefix) | Trust Name Pattern | Asset Type | Notes |
|---|---|---|---|
| `AFS_SENSUB_CORP_` | AmeriCredit Automobile Receivables Trust | Auto loans (subprime) | Sponsor: GM Financial |
| `Ally_Auto_Assets_LLC_` | Ally Auto Receivables Trust | Auto loans | Sponsor/Servicer: Ally Bank |
| `AMERICAN_EXPRESS_CREDIT_ACCOUNT_MASTER_TRUST_` | American Express Credit Account Master Trust | Credit card receivables | **Master trust / revolving — different structure** |
| `AMERICAN_HONDA_RECEIVABLES_LLC_` | Honda Auto Receivables Owner Trust | Auto loans | Sponsor: American Honda Finance Corp |
| `BMW_AUTO_LEASING_LLC_` | BMW Vehicle Lease Trust | **Auto leases** (not loans) | Collateral is lease payments + residual vehicle value |
| `Bridgecrest_Auto_Funding_LLC_` | Bridgecrest Lending Auto Securitization Trust | Auto loans (subprime) | Sponsor: Bridgecrest Acceptance Corp |
| `CARMAX_AUTO_FUNDING_LLC_` | CarMax Select Receivables Trust | Auto loans (subprime) | Sponsor: CarMax Business Services |
| `FORD_CREDIT_AUTO_RECEIVABLES_TWO_LLC_` | Ford Credit Auto Owner Trust | Auto loans | Sponsor: Ford Motor Credit Company |
| `HARLEY-DAVIDSON_CUSTOMER_FUNDING_CORP_` | Harley-Davidson Motorcycle Trust | **Motorcycle loans** | Sponsor: Harley-Davidson Credit Corp |
| `HYUNDAI_ABS_FUNDING_LLC_` | Hyundai Auto Receivables Trust | Auto loans | Sponsor: Hyundai Capital America |
| `SANTANDER_DRIVE_AUTO_RECEIVABLES_LLC_` | Santander Drive Auto Receivables Trust | Auto loans (subprime) | Sponsor: Santander Consumer USA |
| `TOYOTA_AUTO_FINANCE_RECEIVABLES_LLC_` | Toyota Auto Receivables Owner Trust | Auto loans | Sponsor: Toyota Motor Credit Corp |
| `Verizon_ABS_II_LLC_` | Verizon Master Trust | **Device payment plan agreements** | **Completely different asset class — revolving pool of phone contracts** |
| `WELLS_FARGO_COMMERCIAL_MORTGAGE_SECURITIES_INC_` | Wells Fargo Commercial Mortgage Trust | **Commercial mortgage loans** | **Completely different asset class — CMBS, not auto ABS** |
| `WORLD_OMNI_AUTO_RECEIVABLES_LLC_` | World Omni Auto Receivables Trust | Auto loans | Sponsor: Southeast Toyota Finance |

---

## Metadata Fields — Applicable to All Auto/Motorcycle Loan ABS (12 of 15 companies)

These fields are consistently present across Toyota, Hyundai, CarMax, Harley-Davidson, AFS SenSub, Ally, American Honda, Bridgecrest, Ford, Santander, and World Omni.

### Deal / Identity

| Field | Description | Example |
|---|---|---|
| `deal_name` | Full name of the issuing trust | Toyota Auto Receivables 2024-B Owner Trust |
| `issuing_entity_cik` | SEC CIK number of the trust | 0002012786 |
| `depositor` | Legal name of the depositor entity | Toyota Auto Finance Receivables LLC |
| `sponsor_servicer` | Sponsor, seller, and/or servicer | Toyota Motor Credit Corporation |
| `registration_number` | SEC registration statement number | 333-259868 |
| `asset_type` | Type of underlying collateral | auto loans / motorcycle loans |
| `filing_date` | Date the 424H was filed (from filename) | 2024-04-18 |

### Pool / Collateral Characteristics

From the pool summary table near the front of each prospectus, as of the cutoff date.

| Field | Description | Example |
|---|---|---|
| `cutoff_date` | Date the receivables pool was frozen for statistics | February 29, 2024 |
| `total_principal_balance` | Aggregate principal balance of the pool | $1,447,406,675.12 |
| `number_of_receivables` | Count of contracts in the pool | 54,194 |
| `avg_principal_balance` | Average principal balance per contract | $26,707.88 |
| `wa_apr` | Weighted average annual percentage rate | 5.70% |
| `wa_fico` | Weighted average FICO score of obligors | 767 |
| `wa_original_term` | Weighted avg original number of scheduled payments (months) | 65.73 |
| `wa_remaining_term` | Weighted avg remaining number of scheduled payments (months) | 54.53 |

### Note Structure

| Field | Description | Example |
|---|---|---|
| `aggregate_principal_amount` | Total deal size (headline dollar amount) | $1,350,000,000 |
| `note_classes` | Classes of notes issued with principal amounts | A-1: $290M, A-2a: $478M, A-3: $478M, A-4: $70.2M, B: $33.8M |
| `first_payment_date` | Date of first scheduled payment to noteholders | May 15, 2024 |
| `credit_enhancement_types` | Credit enhancement mechanisms used | reserve account, overcollateralization, subordination, excess interest |

---

## Field Variations by Asset Type

### BMW Auto Leasing — Auto Leases (not loans)
- All deal/identity and note structure fields apply as-is.
- Pool fields differ:
  - No `wa_fico` or `wa_apr` — leases don't carry an APR in the same sense.
  - Replace `total_principal_balance` / `number_of_receivables` with **number of leases** and **aggregate securitization value**.
  - Add `wa_residual_value` — weighted average residual value of leased vehicles (key risk driver for lease ABS).
  - Add `vehicle_make` — BMW passenger cars and light trucks only.

### American Express — Credit Card Master Trust (revolving)
- Structurally different: this is a **master trust** with a **revolving pool** of credit card receivables, not a static pool of installment contracts.
- `cutoff_date`, `number_of_receivables`, `wa_original_term`, `wa_remaining_term`, `wa_fico` do **not** apply in the same way.
- Relevant fields instead: **series name** (e.g. Series 2024-2), **certificate amount**, **seller's interest**, **portfolio yield**, **payment rate**.
- Recommend treating AmEx as a **separate asset class** in the index table with its own schema, or flagging it with `asset_type = credit_card_revolving`.

### Verizon — Device Payment Plan Agreements (revolving)
- Also a **master trust / revolving pool** structure — not a static pool.
- Collateral is Verizon phone payment plans, not vehicles.
- `wa_fico`, `wa_apr`, `wa_original_term`, `wa_remaining_term`, `cutoff_date` do **not** apply.
- Relevant fields instead: **series name**, **device payment plan balance**, **payment rate**, **anticipated redemption date**.
- Recommend flagging as `asset_type = device_payment_revolving` and treating separately.

### Wells Fargo — Commercial Mortgage (CMBS)
- Completely different asset class: **commercial real estate loans**, not consumer ABS.
- Pool fields are entirely different: loan count, property types, LTV ratios, DSCR, geographic distribution.
- Note structure uses **pass-through certificates** not notes.
- Recommend **excluding from the main index table** or maintaining a separate CMBS schema.

---

## Summary: Field Compatibility by Company

| Company | Core Fields Apply | Notes |
|---|---|---|
| Toyota | ✅ Full | — |
| Hyundai | ✅ Full | — |
| CarMax | ✅ Full | Subprime — lower WA FICO |
| Harley-Davidson | ✅ Full | `asset_type = motorcycle_loans` |
| AFS SenSub (AmeriCredit/GM Financial) | ✅ Full | Subprime — lower WA FICO |
| Ally | ✅ Full | — |
| American Honda | ✅ Full | — |
| Bridgecrest | ✅ Full | Subprime — lower WA FICO |
| Ford | ✅ Full | — |
| Santander | ✅ Full | Subprime — lower WA FICO |
| World Omni | ✅ Full | — |
| BMW | ⚠️ Partial | Lease ABS — no APR/FICO; add residual value fields |
| American Express | ❌ Different schema | Credit card revolving master trust |
| Verizon | ❌ Different schema | Device payment revolving master trust |
| Wells Fargo | ❌ Different schema | CMBS — commercial mortgage |

---

## Notes on Data Availability (all companies)

- **Interest rates are blank** in all 424H filings — pre-pricing, so rates appear as `___%`. Only filled in the final 424B.
- **Underwriting discounts and proceeds** are similarly blank.
- **Some filings have two pool scenarios** (base vs. upsize) — use the base/smaller amount as the primary value.
- **Subprime issuers** (CarMax, Bridgecrest, Santander, AFS SenSub) will have lower WA FICO scores and higher WA APRs than prime issuers (Toyota, Honda, Ally).

---

## Proposed Index Table Schema

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
