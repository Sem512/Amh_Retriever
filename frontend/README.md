# Amharic Document Search — Frontend (Task 10 / Task 9 integration)

React 18 + Vite + Tailwind. Owner: Yassin Bedru.

> **The project scope changed (Oct 2026):** it is now an image translator. The API is a single
> `POST /translate` (photo + mode → image + Amharic/English segments with `bboxes`), specified in
> [`../ARCHITECTURE.md`](../ARCHITECTURE.md) section 4. The table below is the old search API this app
> was built against. Report chapter, annexes, defense deck, UAT kit and design figures are in
> [`docs/`](docs/).

## Run
```bash
npm install
npm run dev        # http://localhost:5173  (demo mode, no backend needed)
npm test           # unit tests (vitest)
npm run build      # production build -> dist/ (deploy to Vercel)
```
Demo mode uses an in-browser mock backend (admin / admin123). To use the real
FastAPI backend: `cp .env.example .env` and set `VITE_API_URL=http://localhost:8000`.

## Features
- Amharic natural-language search with ranked results and match score
- Page viewer showing the **preprocessed page image** (the deskewed, cleaned image the OCR read) with a **bounding-box highlight overlay** (one box per line or block of the passage), zoom, page and result navigation
- Role-based access: public searchers vs. administrator (JWT). An expired or invalid token (HTTP 401/403) clears the session and redirects to the login page
- Admin: multi-file upload with progress (rows are keyed by a unique id, so same-named files do not collide), status polling (queued/processing/indexed/failed), delete; upload, delete and list failures show the backend's error message
- Amharic / English interface toggle; responsive (mobile viewer is full-screen)
- Accessibility: labelled controls, keyboard focus, aria-live status, reduced-motion support

## API contract (agree with Semir — Task 9)
| Method | Path | Body / Query | Response |
|---|---|---|---|
| POST | `/auth/login` | `{username, password}` | `{access_token, token_type, role: "admin"\|"searcher", username}` |
| GET | `/search` | `?q=<text>&k=10` | `{query, took_ms, results:[{chunk_id, doc_id, title, page, pages_total, score(0-1), snippet, bboxes:[{x,y,w,h}, ...]}]}` (a single `bbox:{x,y,w,h}` is still accepted as a fallback) |
| GET | `/documents` | admin | `[{id, title, pages, status, uploaded_at}]` |
| POST | `/documents` | multipart `file` (admin) | `{id, status}` |
| DELETE | `/documents/{id}` | admin | `204` |
| GET | `/documents/{id}/pages/{n}/image` | — | `image/png`: the preprocessed page image the OCR boxes refer to |

`bboxes` is an array of boxes, each **normalized 0–1** relative to the page image the viewer
shows, origin top-left. The backend divides Tesseract's pixel boxes by that image's width and
height (see `pixelsToBBox` in `src/lib/bbox.js`). The image served by `/pages/{n}/image` must be
the **same preprocessed image the OCR ran on** (same size and orientation, after deskewing),
otherwise the highlights are misplaced. The frontend draws every box in `bboxes`; if the array is
missing or empty it draws the single `bbox`.

Errors: send FastAPI-style `{"detail": "message"}` (a string, or a list of `{msg}` objects).
The frontend shows `detail` for failed uploads, deletes and document-list loads. Return **401** for a
missing, expired or invalid token and **403** for a valid token without admin rights; on either
the frontend clears the token and redirects to the login page. A wrong password on `/auth/login`
should also be 401 (the login form shows an inline error and does not redirect).

Enable CORS for the frontend origin in FastAPI.

## Structure
```
src/lib/      api.js (real client, 401/403 guard) · errors.js · mockApi.js · auth.jsx · i18n.jsx · bbox.js
src/components/  DocumentViewer · ResultList · UploadDropzone · Header
src/pages/    SearchPage · LoginPage · AdminPage
tests/        frontend.test.js (unit) · e2e/run_e2e.py (31 Playwright scenarios)
```

## Tests
```bash
npm test                                   # 18 unit tests
npm run build && npx vite preview --port 4173 &
python3 tests/e2e/run_e2e.py               # 31 end-to-end scenarios (needs Playwright + Chromium)
```
The e2e suite runs against the mock backend. To check the integration with the real FastAPI
service, rebuild with `VITE_API_URL` set; failures then point to contract mismatches.
