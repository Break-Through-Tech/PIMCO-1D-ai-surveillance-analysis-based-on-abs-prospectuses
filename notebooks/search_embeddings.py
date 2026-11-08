"""Search the local embedding index with a natural-language question.

The search itself lives in src/qa/search.py; this script is its command line.

Examples:
    python notebooks/search_embeddings.py --query "physical custody" --top-k 5
"""

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from src.qa.search import QAError, retrieve


def main() -> None:
    parser = argparse.ArgumentParser(description="Search a local semantic embedding index.")
    parser.add_argument("--query", required=True, help="Natural-language question or search phrase.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to return.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be positive")

    try:
        results = retrieve(args.query, top_k=args.top_k)
    except QAError as error:
        raise SystemExit(str(error))
    if args.as_json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return
    for number, result in enumerate(results, start=1):
        label = result.get("deal_name") or result.get("company") or result["filing_stem"]
        print(f"\n[{number}] similarity={result['similarity']:.4f} | {label}")
        print(
            f"    filing={result['filing_stem']} | page={result['page_num']} "
            f"| printed={result.get('printed_label') or 'n/a'} "
            f"| section={result.get('toc_section') or 'n/a'}"
        )
        print(f"    chunk={result['chunk_id']}")
        print(f"    {result['embed_text']}")


if __name__ == "__main__":
    main()
