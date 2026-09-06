"""
Phase 1 POC — step 1 & 2: set up a local ChromaDB collection and embed a
small set of Amharic text chunks into it.

Run:
    python build_index.py [path/to/chunks.json]

Input JSON is a list of objects: {chunk_id, doc_id, page_number, text}.
Defaults to sample_chunks.json (placeholder data) — swap in Ferid's real
chunks by pointing this at that file instead; the shape must match.

This does NOT do normalization or OCR — per the task split, Ferid's stage
hands off already-normalized text chunks. This script starts from there.
"""

import json
import sys
from pathlib import Path

import chromadb

from embedder import MODEL_NAME, embed_passages

CHROMA_PATH = Path(__file__).parent / "chroma_store"
COLLECTION_NAME = "amharic_poc_chunks"


def load_chunks(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        chunks = json.load(f)
    required = {"chunk_id", "doc_id", "page_number", "text"}
    for c in chunks:
        missing = required - c.keys()
        if missing:
            raise ValueError(f"chunk {c.get('chunk_id', '?')} missing fields: {missing}")
    return chunks


def main():
    chunks_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "sample_chunks.json"
    print(f"[build_index] loading chunks from {chunks_path}")
    chunks = load_chunks(chunks_path)
    print(f"[build_index] {len(chunks)} chunks loaded")

    print(f"[build_index] embedding with model: {MODEL_NAME}")
    vectors = embed_passages([c["text"] for c in chunks])

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    # Delete-and-recreate rather than upsert: for the POC we always want a
    # clean rebuild from the current chunk file, not leftover state from a
    # previous model or previous sample set silently mixed in.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        COLLECTION_NAME,
        metadata={"embedding_model": MODEL_NAME},
    )

    collection.add(
        ids=[c["chunk_id"] for c in chunks],
        embeddings=vectors,
        documents=[c["text"] for c in chunks],
        metadatas=[{"doc_id": c["doc_id"], "page_number": c["page_number"]} for c in chunks],
    )

    print(f"[build_index] indexed {collection.count()} chunks into "
          f"'{COLLECTION_NAME}' at {CHROMA_PATH}")
    print("[build_index] done. run: python query.py \"<your Amharic query>\"")


if __name__ == "__main__":
    main()
