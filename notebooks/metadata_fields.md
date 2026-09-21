# ABS Prospectus Metadata Fields

Discovered by inspecting clean text from all 4 companies (Toyota, Hyundai, CarMax, Harley-Davidson).
These fields are consistently present across filings and are the basis for the index table in Milestone 1.

---

## Field Reference

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

These come from the pool summary table near the front of each prospectus, as of the cutoff date.

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
| `credit_enhancement_types` | Credit enhancement mechanisms used | reserve account, overcollateralization, subordination, excess interest, yield supplement OC amount |

---

## Notes on Data Availability

- **Interest rates are blank** in all 424H filings — these are pre-pricing filings, so rates appear as `___%` placeholders. They are filled in only in the final 424B prospectus.
- **Underwriting discounts and proceeds** are similarly blank for the same reason.
- **Some filings have two pool scenarios** (e.g. $1.35B and $1.75B aggregate principal) — the smaller/base case should be used as the primary value.
- **Harley-Davidson** filings use "motorcycle contracts" instead of "retail installment sales contracts" — `asset_type` captures this distinction.
- **CarMax** filings include lower credit quality obligors (subprime) — this is reflected in lower WA FICO scores compared to Toyota/Hyundai.

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
