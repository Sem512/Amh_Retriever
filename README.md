# Amharic Image Translator

Senior project. A user uploads one photo of Amharic text (a document, a sign or handwriting); the app
reads the Amharic, translates it to English, and shows both side by side with each sentence's lines
highlighted on the image. Runs locally, free and open-source only. The full design, lane contracts,
API contract and schedule are in [`ARCHITECTURE.md`](ARCHITECTURE.md).

(The repo name is historical: the project was a semantic-retrieval system until the scope changed in
October 2026.)

## Team and lanes

| Lane | Owner | Directory | Status |
|---|---|---|---|
| Image cleanup, finding text on signs | Kibreab | [`preprocessing/`](preprocessing/) | not started |
| OCR (Tesseract) | Ferid | [`ocr/`](ocr/) | not started |
| Sentences, translation, API | Semir | [`backend/`](backend/) | API skeleton with contract tests; NLLB set up |
| Frontend, user tests | Yassin | [`frontend/`](frontend/) | built for the old search API; needs the upload + side-by-side rework |

Each lane builds against the function contracts in `ARCHITECTURE.md` section 3; those are the whole
coordination surface between lanes.
