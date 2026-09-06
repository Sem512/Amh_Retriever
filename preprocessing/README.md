# Preprocessing — Lane A (Kibreab)

PDF-to-page-image splitting and OpenCV cleanup: deskew, denoise, binarize, crop.
Owns the first stage of the ingestion pipeline, ahead of OCR.

See [`ARCHITECTURE.md`](../ARCHITECTURE.md):
- §1 — component diagram, ingestion path
- **§2.1 — the contract this lane must produce: `PreprocessedPage`.** This is
  the team boundary with OCR (Lane B / Ferid) — freeze this shape before
  building against it.

Key decision already made in the architecture doc, worth reading before
writing code: the viewer renders the *preprocessed* image, not the original
PDF page, specifically so OCR bounding boxes never need an inverse-transform
back to original coordinates. That means this lane's output geometry is
what OCR, chunking, and the frontend highlight overlay all inherit — get the
image dimensions and `deskew_angle_deg` fields right and everything
downstream stays simple.

Nothing has been built here yet.
