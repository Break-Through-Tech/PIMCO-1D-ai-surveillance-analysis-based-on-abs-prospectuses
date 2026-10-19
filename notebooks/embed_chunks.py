"""Create a local vector index from chunk JSONL files.

The API key is read from OPENAI_API_KEY. Generated files are intentionally
kept under data/, which is excluded by this repository's gitignore rules.

Examples:
    python notebooks/chunk_filings.py --limit 2
    python notebooks/embed_chunks.py --limit 2
    python notebooks/embed_chunks.py
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from openai import OpenAI


ROOT = Path(__file__).parent.parent
CHUNKS_DIR = ROOT / "data" / "chunks"
EMBEDDINGS_DIR = ROOT / "data" / "embeddings"
DEFAULT_MODEL = "text-embedding-3-small"


def load_chunks(limit: int | None = None) -> list[dict]:
    """Load embeddable chunks in stable filename/line order."""
    paths = sorted(CHUNKS_DIR.glob("*_chunks.jsonl"))
    if limit is not None:
        paths = paths[:limit]

    chunks = []
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"Invalid JSON in {path}:{line_number}") from error
                if chunk.get("embed") and chunk.get("embed_text", "").strip():
                    chunks.append(chunk)
    return chunks


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def create_embeddings(
    chunks: list[dict],
    *,
    model: str,
    batch_size: int,
    client: OpenAI,
) -> np.ndarray:
    """Embed chunks in batches and preserve the input order."""
    vectors: list[list[float]] = []
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        response = client.embeddings.create(
            model=model,
            input=[chunk["embed_text"] for chunk in batch],
        )
        returned = sorted(response.data, key=lambda item: item.index)
        if len(returned) != len(batch):
            raise RuntimeError(
                f"Embedding API returned {len(returned)} vectors for "
                f"{len(batch)} inputs."
            )
        vectors.extend(item.embedding for item in returned)
        print(f"  Embedded {min(start + batch_size, len(chunks))}/{len(chunks)} chunks")
    return np.asarray(vectors, dtype=np.float32)


def write_index(chunks: list[dict], vectors: np.ndarray, model: str) -> None:
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    np.save(EMBEDDINGS_DIR / "vectors.npy", vectors)

    metadata_path = EMBEDDINGS_DIR / "metadata.jsonl"
    with metadata_path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            record = {key: value for key, value in chunk.items() if key not in {"raw_text", "embedding"}}
            record["text_sha256"] = text_hash(chunk["embed_text"])
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    manifest = {
        "model": model,
        "dimensions": int(vectors.shape[1]) if vectors.ndim == 2 else 0,
        "chunk_count": len(chunks),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (EMBEDDINGS_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Embed chunk text into a local NumPy vector index.")
    parser.add_argument("--limit", type=int, help="Process at most N chunk files.")
    parser.add_argument("--batch-size", type=int, default=64, help="Texts per API request.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Embedding model name.")
    args = parser.parse_args()

    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set; refusing to make an unauthenticated request.")
    if not CHUNKS_DIR.exists():
        raise SystemExit(f"Chunk directory not found: {CHUNKS_DIR}. Run chunk_filings.py first.")

    chunks = load_chunks(args.limit)
    if not chunks:
        raise SystemExit("No embeddable chunks found. Run chunk_filings.py first.")

    print(f"Embedding {len(chunks)} chunks with {args.model}...")
    vectors = create_embeddings(
        chunks,
        model=args.model,
        batch_size=args.batch_size,
        client=OpenAI(),
    )
    write_index(chunks, vectors, args.model)
    print(f"Saved {len(chunks)} vectors to {EMBEDDINGS_DIR}")


if __name__ == "__main__":
    main()
