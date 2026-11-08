"""Answer natural-language questions using retrieved filing chunks.

The answering itself lives in src/qa/answer.py; this script is its command
line. The completion model receives only the top retrieved chunks, never the
whole corpus.

Examples:
    python notebooks/answer_questions.py --query "Which deals use physical custody?"
    python notebooks/answer_questions.py --query "What are the replacement servicer provisions?" --top-k 8
"""

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from src.qa.answer import DEFAULT_MODEL, answer_question
from src.qa.search import QAError


def source_line(source: dict) -> str:
    label = source["deal_name"] or source["company"] or source["filing"]
    page = source["page_label"] or "n/a"
    return (
        f"[Source {source['number']}] {label} | {source['filing']} | "
        f"printed page {page} (page {source['page']}) | "
        f"section {source['section'] or 'n/a'} | chunk {source['chunk_id']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Answer a natural-language question from retrieved filing chunks."
    )
    parser.add_argument("--query", required=True, help="Natural-language question.")
    parser.add_argument("--top-k", type=int, default=5, help="Chunks to retrieve.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Completion model name.")
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be positive")

    try:
        result = answer_question(args.query, top_k=args.top_k, model=args.model)
    except QAError as error:
        raise SystemExit(str(error))
    print(result["answer"])
    if result["sources"]:
        print("\nSources:")
        for source in result["sources"]:
            print(source_line(source))


if __name__ == "__main__":
    main()
