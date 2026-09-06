# OCR + Normalization — Lane B (Ferid, output-structuring co-owned with Semir)

OCR engine (Tesseract `amh` / EasyOCR) over preprocessed page images, plus the
Amharic normalizer that folds homophone characters (ሀ/ሐ/ኀ, ሠ/ሰ, ዐ/አ, ጸ/ፀ) and
canonicalizes punctuation and digits.

See [`ARCHITECTURE.md`](../ARCHITECTURE.md):
- §2.1 — `PreprocessedPage`, the input this lane consumes from preprocessing
  (Lane A / Kibreab)
- §2.2 — `OCRWord`, word-level output with bounding boxes — line-level bboxes
  are not enough, highlighting depends on per-word boxes
- §2.3 — normalization rules, and why **both** `text` (raw OCR) and
  `norm_text` (normalized) must be kept permanently, never just one
- **§2.4 — the contract this lane must produce: `Chunk`.** This is the team
  boundary with backend/retrieval (Lane C / Semir) — freeze this shape
  before building against it. Semir's Phase 1 POC (`../backend/poc/`) is
  currently running against placeholder chunks in this exact shape; swap
  them for real output here as soon as it exists.

Split of ownership within this lane: Ferid owns OCR engine internals
(language data, confidence thresholds); Semir owns turning that output into
the structured `Chunk` format the database and embedding pipeline consume.
Don't assume engine-tuning work belongs to Semir — ask first.

Nothing has been built here yet.
