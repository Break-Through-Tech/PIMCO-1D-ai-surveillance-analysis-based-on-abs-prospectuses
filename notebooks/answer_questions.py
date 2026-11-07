"""Answer natural-language questions using retrieved filing chunks.

Retrieval and answer generation are deliberately separate: the completion
model receives only the top retrieved chunks, never the whole corpus.

Examples:
    python notebooks/answer_questions.py --query "Which deals use physical custody?"
    python notebooks/answer_questions.py --query "What are the replacement servicer provisions?" --top-k 8
"""

import argparse
import os

from openai import OpenAI

from search_embeddings import retrieve


DEFAULT_MODEL = "gpt-6-luna"


def source_label(number: int, result: dict) -> str:
    filing = result.get("filing_stem", "unknown filing")
    page = result.get("page_num", "unknown")
    printed = result.get("printed_label")
    section = result.get("toc_section")
    details = f"{filing}, physical page {page}"
    if printed:
        details += f", printed page {printed}"
    if section:
        details += f", section {section}"
    return f"[Source {number}: {details}; chunk {result['chunk_id']}]"


def build_prompt(query: str, results: list[dict]) -> str:
    evidence = []
    for number, result in enumerate(results, start=1):
        evidence.append(
            f"{source_label(number, result)}\n"
            f"Similarity score: {result['similarity']:.4f}\n"
            f"{result['embed_text']}"
        )
    return (
        "Answer the user's question using only the supplied evidence. "
        "Do not rely on outside knowledge and do not invent facts. "
        "If the evidence is insufficient or conflicting, say so clearly. "
        "Cite every substantive claim with one or more source labels exactly "
        "as written, such as [Source 1]. Keep the answer concise.\n\n"
        f"User question:\n{query}\n\n"
        "Retrieved evidence:\n"
        + "\n\n".join(evidence)
    )


def answer_question(
    query: str,
    *,
    top_k: int,
    model: str,
    client: OpenAI,
) -> str:
    results = retrieve(query, top_k=top_k, client=client)
    if not results:
        return "No evidence was retrieved for this question."

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful financial-document research assistant. "
                    "Use only the retrieved evidence and always cite claims."
                ),
            },
            {"role": "user", "content": build_prompt(query, results)},
        ],
    )
    answer = response.choices[0].message.content
    if not answer or not answer.strip():
        raise RuntimeError("The completion API returned an empty answer.")
    return answer.strip()


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
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set; refusing to make an unauthenticated request.")

    print(answer_question(
        args.query,
        top_k=args.top_k,
        model=args.model,
        client=OpenAI(),
    ))


if __name__ == "__main__":
    main()
