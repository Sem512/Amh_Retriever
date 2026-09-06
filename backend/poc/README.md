# Phase 1 POC — semantic retrieval over Amharic text chunks

Proves one thing: Amharic text chunks embedded with a multilingual model and
searched by cosine similarity return a *semantically* relevant chunk that a
plain keyword search would miss. No auth, no API framework, no OCR — this
starts from already-normalized text chunks (Ferid's output) and ends at a
queryable in-process function.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# CPU-only torch first — installing sentence-transformers alone can pull a
# CUDA build you don't need and don't have the GPU for.
pip install --index-url https://download.pytorch.org/whl/cpu torch
pip install -r requirements.txt
```

## Run

```bash
cd poc
python build_index.py                    # embeds sample_chunks.json, builds the Chroma collection
python query.py "የቡና ንግድ በኢትዮጵያ ምጣኔ ሀብት ላይ ያለው ተጽእኖ"
```

To index Ferid's real chunks instead of the placeholder sample set:

```bash
python build_index.py path/to/real_chunks.json
```

Input format — a JSON list of objects, one per chunk:

```json
{"chunk_id": "doc1:p0001:c000", "doc_id": "doc1", "page_number": 1, "text": "..."}
```

This is a deliberately narrower shape than the full `Chunk` contract in
[`ARCHITECTURE.md`](../../ARCHITECTURE.md) (§2.4) — no bboxes, no
confidence, no versions yet. Phase 2 (Task 7) extends it to the full
contract once the relational DB and OCR handoff exist.

## Demo data

`sample_chunks.json` is **placeholder text I wrote**, not real OCR output —
5 short chunks across 3 pages, on Ethiopian coffee, education, and language.
It exists so the pipeline is runnable before Ferid's real chunks arrive.
Delete it once real data is available.

The demo query is deliberately a *paraphrase*: it asks about coffee's
economic impact using different words (ምጣኔ ሀብት, "national economy") than
the matching chunk uses (ኢኮኖሚ, "economy" — a loanword). A keyword/BM25
search would score this low or miss it since there's no shared token; a
semantic search should still rank that chunk first because the *meaning*
overlaps. That contrast is the actual deliverable — screenshot or paste the
`query.py` output showing it for the demo.

## On the embedding model — read this before assuming bge-m3 is wired in

**The default model in `embedder.py` is `intfloat/multilingual-e5-base`, not
bge-m3.** This is a deliberate, flagged substitution, not a placeholder I
forgot to swap back:

- `BAAI/bge-m3` is a ~2.2GB download and a heavier model to run on CPU. On a
  4-day budget, a slow or interrupted first download (model weights come
  from Hugging Face's CDN, and connection speed on a given machine is the
  real wildcard here) can eat a meaningful chunk of the time meant for
  actually building and testing the retrieval logic.
- `multilingual-e5-base` (~1.1GB, 768-dim) trades a bit of ceiling quality
  for a faster, more predictable setup, and it's well-documented for
  multilingual retrieval. For a POC whose only job is proving the
  *mechanism* — not squeezing out maximum recall — that trade is right.
- Swap back with zero code changes: `set AMH_EMBED_MODEL=BAAI/bge-m3` (or
  `export` on macOS/Linux) before running either script. Do this once
  there's headroom in the schedule — bge-m3 has an edge specifically on
  low-resource languages, so it's worth revisiting for Phase 2, not
  abandoning.
- If e5 is still too slow to download in your environment, the next
  fallback is `intfloat/multilingual-e5-small` (~470MB, 384-dim) — same
  prefix convention, just edit `DEFAULT_MODEL` in `embedder.py`.

**Why `embedder.py` is a separate file, not inlined into both scripts:**
`multilingual-e5-*` models require a `"query: "` / `"passage: "` text
prefix baked in at training time — skip it and the model still runs, still
returns *something*, and quietly returns worse rankings with no error to
tell you why. bge-m3 needs no prefix at all. Centralizing this means
`build_index.py` and `query.py` can never disagree about it, and switching
models later is a one-line env var instead of a two-file edit that's easy
to get half-done.

## Known limitations (by design, for a 4-day scope)

- Cosine similarity search only — no BM25, no hybrid fusion yet (that's
  Task 9, Phase 2, and it needs its own explanation of RRF; see
  `ARCHITECTURE.md` §4).
- No bounding boxes — chunks map to a page number, not a page region.
- No persistence contract with a relational DB yet — Chroma is the only
  store. Task 7 adds PostgreSQL and the chunk-ID sync strategy described in
  `ARCHITECTURE.md` §3.2 (same deterministic-ID approach applies here).
- `build_index.py` always rebuilds the collection from scratch rather than
  upserting — correct for a POC re-run, not what Phase 2 wants once
  incremental document upload exists.
