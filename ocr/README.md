# OCR and normalization (Ferid)

Delivers `read_page(image)`, `read_line(line_image)`, `normalize(text)` and `fold_homophones(text)`.
The contract is in [`ARCHITECTURE.md`](../ARCHITECTURE.md) section 3, the engine choice is in section 5, and
the model download and test commands are in section 9.

- `reader.py`: Tesseract 5 through `tesserocr`, loaded once. `read_page` returns Tesseract's own text lines
  (normalized, with `(left, top, width, height)` pixel boxes, in reading order); `read_line` reads one
  cropped sign line. `OCR_LANG` picks `amh` (default) or `Ethiopic`.
- `normalize.py`: fixes OCR mistakes only and never re-spells a correctly read word. `fold_homophones` is
  separate and is not part of the pipeline; only the scoring experiment uses it.
- `tests/`: normalizer tables, plus the real engine on a generated Ebrima page (line count, box overlap,
  character error rate).

Still to do: choose `amh` or `Ethiopic` and a confidence threshold on the real printed photos, and
grow `normalize` as real OCR mistakes turn up (each new rule with a test). Handwriting uses the same
`read_page` path as an experimental baseline.

Run the tests from the repo root: `python -m pytest ocr`.
