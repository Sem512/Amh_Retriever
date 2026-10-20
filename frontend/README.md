# Amharic Document Search — Frontend (Task 10 / Task 9 integration)

React 18 + Vite + Tailwind. Owner: Yassin Bedru.

> The authoritative API contract lives in [`../ARCHITECTURE.md`](../ARCHITECTURE.md) §2.6 and §5; the
> table below is the version this app was built against, and §2.6 adopts it with a few extensions
> (`bboxes` list, preprocessed page image, `queued` status). Report chapter, annexes, defense deck, UAT
> kit and design figures are in [`docs/`](docs/).

## Run
```bash
npm install
npm run dev        # http://localhost:5173  (demo mode, no backend needed)
npm test           # unit tests
npm run build      # production build -> dist/ (deploy to Vercel)
```
Demo mode uses an in-browser mock backend (admin / admin123). To use the real
FastAPI backend: `cp .env.example .env` and set `VITE_API_URL=http://localhost:8000`.

## Features
- Amharic natural-language search with ranked results and match score
- Original page viewer with **bounding-box highlight overlay**, zoom, page and result navigation
- Role-based access: public searchers vs. administrator (JWT)
- Admin: multi-file upload with progress, status polling (queued/processing/indexed/failed), delete
- Amharic / English interface toggle; responsive (mobile viewer is full-screen)
- Accessibility: labelled controls, keyboard focus, aria-live status, reduced-motion support

## API contract (agree with Semir — Task 9)
| Method | Path | Body / Query | Response |
|---|---|---|---|
| POST | `/auth/login` | `{username, password}` | `{access_token, token_type, role: "admin"\|"searcher", username}` |
| GET | `/search` | `?q=<text>&k=10` | `{query, took_ms, results:[{chunk_id, doc_id, title, page, pages_total, score(0-1), snippet, bbox:{x,y,w,h}}]}` |
| GET | `/documents` | admin | `[{id, title, pages, status, uploaded_at}]` |
| POST | `/documents` | multipart `file` (admin) | `{id, status}` |
| DELETE | `/documents/{id}` | admin | `204` |
| GET | `/documents/{id}/pages/{n}/image` | — | `image/png` |

`bbox` is **normalized 0–1** relative to the page image, origin top-left. The backend
must divide Tesseract's pixel boxes by the page image width/height (see
`pixelsToBBox` in `src/lib/bbox.js`). Enable CORS for the frontend origin in FastAPI.

## Structure
```
src/lib/      api.js (real client) · mockApi.js · auth.jsx · i18n.jsx · bbox.js
src/components/  DocumentViewer · ResultList · UploadDropzone · Header
src/pages/    SearchPage · LoginPage · AdminPage
tests/        frontend.test.js
```
