"""
Phase 1 POC — step 3: query script. Takes a plain-text Amharic query,
embeds it, runs cosine similarity search against the ChromaDB collection
built by build_index.py, and prints the top-k chunks with source page.

Run:
    python query.py "<Amharic query text>" [--top-k 3]

No auth, no API framework — this is deliberately a bare function/CLI per
the POC scope. main() returns a plain list of dicts so it can be imported
and called directly (e.g. from a temporary FastAPI shim) without going
through subprocess or stdout parsing.
"""

import argparse
import sys

# Windows consoles default to cp1252, which can't encode Ethiopic script —
# printing an Amharic query/result without this raises UnicodeEncodeError.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import chromadb

from build_index import CHROMA_PATH, COLLECTION_NAME
from embedder import embed_query


def search(query_text: str, top_k: int = 3) -> list[dict]:
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception as e:
        raise RuntimeError(
            "Collection not found — run build_index.py first."
        ) from e

    vector = embed_query(query_text)
    result = collection.query(query_embeddings=[vector], n_results=top_k)

    hits = []
    for i in range(len(result["ids"][0])):
        distance = result["distances"][0][i]
        # Chroma returns cosine DISTANCE (0 = identical). We report
        # similarity (1 - distance) since "higher is better" is the
        # intuitive direction for a result list.
        hits.append({
            "chunk_id": result["ids"][0][i],
            "doc_id": result["metadatas"][0][i]["doc_id"],
            "page_number": result["metadatas"][0][i]["page_number"],
            "text": result["documents"][0][i],
            "similarity": round(1 - distance, 4),
        })
    return hits


def main():
    parser = argparse.ArgumentParser(description="Query the Amharic POC index")
    parser.add_argument("query", help="Amharic query text")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    hits = search(args.query, args.top_k)

    print(f"\nQuery: {args.query}\n")
    if not hits:
        print("No results.")
        return
    for rank, hit in enumerate(hits, 1):
        print(f"#{rank}  similarity={hit['similarity']}  "
              f"doc={hit['doc_id']}  page={hit['page_number']}")
        print(f"     {hit['text']}\n")


if __name__ == "__main__":
    sys.exit(main() or 0)
