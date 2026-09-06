# Frontend — Lane D (Yassin)

React app: admin console (upload, job status, document manager), search UI,
and the document viewer with bounding-box highlight overlay.

See [`ARCHITECTURE.md`](../ARCHITECTURE.md):
- **§2.6 — the contract this lane consumes: `SearchRequest` / `SearchResponse`.**
  This is the only team boundary this lane has — it talks to Semir's API and
  nothing else, no direct dependency on any other lane's internals.
- §5 — auth boundary: which endpoints are public vs admin-only. Hiding admin
  UI from non-admins is a UX nicety here, not a security boundary — the API
  re-checks every protected call server-side regardless of what the frontend
  shows.

Highlight rendering note: `SearchHit` returns pixel bboxes plus
`page_width`/`page_height` as explicit denominators. Scale by
`rendered_width / page_width` — don't assume normalized 0–1 coordinates.

Nothing has been built here yet.
