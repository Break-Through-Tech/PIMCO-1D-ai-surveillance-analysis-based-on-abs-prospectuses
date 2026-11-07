# AI Surveillance Analysis Based on ABS Prospectuses

Milestone 1 for the Break Through Tech AI Studio project with PIMCO.

## Project Goal

Build a searchable index of SEC ABS prospectuses so users can find relevant deals and inspect supporting source text. This milestone provides deterministic HTML parsing, structured metadata extraction, keyword or regular-expression search, and filtering by filing year, company, and asset type.

The current dataset contains 116 publicly available SEC `424H` HTML filings from 15 issuers. The challenge overview describes a future `424B`/PDF workflow; this repository currently uses the downloaded `424H` HTML files because they preserve table structure and are available locally.

## Current Deliverables

- Clean text and table extraction from SEC filing HTML.
- Metadata index at `data/filings_index.csv`.
- Parsed-file summary at `data/clean_text/parsed_filings_summary.csv`.
- Search results with deal metadata, source paths, match counts, and supporting snippets.
- Asset-family metadata coverage for auto loans, motorcycle loans, auto leases, revolving receivables, device-payment receivables, and CMBS.

## Setup

Use Python 3.10 or newer, then install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Reproduce the Index

Run the parser first if clean text has not been generated:

```powershell
python notebooks/parse_filings.py
python notebooks/extract_metadata.py
```

The parser writes cleaned filing text to `data/clean_text/`. The metadata extractor writes `data/filings_index.csv` and includes `quality_flags` for missing or inconsistent fields.

## Search and Filter

Search all filings for a keyword:

```powershell
python notebooks/search_filings.py --query custody
```

Search with metadata filters:

```powershell
python notebooks/search_filings.py --query "weighted average" --year 2025 --asset-type auto_loans
python notebooks/search_filings.py --query "physical\s+custody" --regex --company TOYOTA
python notebooks/search_filings.py --asset-type cmbs --max-results 5
```

Use `--json` when passing results to another program:

```powershell
python notebooks/search_filings.py --query "reserve account" --json
```

Each result includes the deal name, issuer label, asset type, filing date, source clean-text path, match count, and up to three supporting snippets.

## Data Organization

| Path | Purpose |
|---|---|
| `data/*.htm` | Downloaded SEC filing documents |
| `data/clean_text/*_clean.txt` | Parsed searchable text |
| `data/filings_index.csv` | Structured metadata index |
| `data/_manifest.csv` | SEC source and download manifest |
| `notebooks/parse_filings.py` | HTML and table parser |
| `notebooks/extract_metadata.py` | Metadata extraction and quality checks |
| `notebooks/search_filings.py` | Keyword, regex, and metadata-filter search |
| `notebooks/chunk_filings.py` | Page-aware, token-limited chunk generator |
| `notebooks/embed_chunks.py` | Batched embedding index builder |
| `notebooks/search_embeddings.py` | Natural-language vector similarity search |
| `notebooks/answer_questions.py` | Evidence-grounded answers with citations |

## Validation

Run the search smoke tests:

```powershell
python -m unittest notebooks/test_search_filings.py
```

The Milestone 1 search layer is intentionally deterministic. Milestone 2
implementation is complete: the project now supports vector indexing,
semantic retrieval, and evidence-grounded answers with citations. Retrieval
evaluation against the team's held-out question set remains as follow-up work.

## Milestone 2 semantic Q&A

Set `OPENAI_API_KEY` in the terminal, generate chunks, and build the local
embedding index:

```powershell
$env:OPENAI_API_KEY = "your-team-api-key"
python notebooks/chunk_filings.py --limit 2
python notebooks/embed_chunks.py
```

Ask a natural-language question. The query is embedded, the closest chunks
are retrieved by cosine similarity, and only those chunks are sent to the
completion model:

```powershell
python notebooks/answer_questions.py `
    --query "Which deals use physical custody?" `
    --top-k 5
```

The default completion model is `gpt-6-luna`; use `--model gpt-5.6-luna` if
needed. Answers are instructed to use only retrieved evidence and cite the
filing, page, section, and chunk identifiers supplied in the prompt.

## Limitations and Next Steps

- The current corpus is `424H` HTML rather than `424B` PDF.
- Metadata extraction is issuer-family aware but still produces quality flags for fields requiring manual review.
- Lexical search may miss semantically equivalent language; use Milestone 2
  semantic search for natural-language questions.
- Milestone 2 implementation is complete. Remaining work is to evaluate
  retrieval quality and answer support against the team's held-out questions.

## References

- [SEC EDGAR search](https://www.sec.gov/edgar/search/)
- [PIMCO ABS surveillance challenge overview](Challenge-Project-Overview.md)

## Acknowledgements

This project is part of the Break Through Tech AI Studio program and is developed for the PIMCO challenge.
