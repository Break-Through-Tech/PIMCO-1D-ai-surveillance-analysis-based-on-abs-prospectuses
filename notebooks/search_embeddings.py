"""Search the local embedding index with a natural-language question.

Examples:
    python notebooks/search_embeddings.py --query "physical custody" --top-k 5
"""

import argparse
import json
import os
from pathlib import Path

import numpy as np
from openai import OpenAI


ROOT = Path(__file__).parent.parent
EMBEDDINGS_DIR = ROOT / "data" / "embeddings"


def normalize(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector, axis=-1, keepdims=True)
    return vector / np.maximum(norm, 1e-12)


def load_metadata() -> list[dict]:
    path = EMBEDDINGS_DIR / "metadata.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"Metadata index not found: {path}")
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def retrieve(query: str, *, top_k: int, client: OpenAI) -> list[dict]:
    vectors = np.load(EMBEDDINGS_DIR / "vectors.npy")
    metadata = load_metadata()
    if len(vectors) != len(metadata):
        raise ValueError("vectors.npy and metadata.jsonl contain different row counts.")
    if not metadata:
        return []

    manifest_path = EMBEDDINGS_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    response = client.embeddings.create(model=manifest["model"], input=[query])
    query_vector = np.asarray(response.data[0].embedding, dtype=np.float32)
    if vectors.shape[1] != query_vector.shape[0]:
        raise ValueError("Query vector dimensions do not match the stored index.")

    scores = normalize(vectors) @ normalize(query_vector.reshape(1, -1))[0]
    indices = np.argsort(scores)[::-1][:top_k]
    return [{**metadata[index], "similarity": float(scores[index])} for index in indices]


def main() -> None:
    parser = argparse.ArgumentParser(description="Search a local semantic embedding index.")
    parser.add_argument("--query", required=True, help="Natural-language question or search phrase.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to return.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be positive")
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set; refusing to make an unauthenticated request.")

    results = retrieve(args.query, top_k=args.top_k, client=OpenAI())
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
