# OCR and normalization (Ferid)

Delivers `read_page(image)`, `read_line(line_image)`, `normalize(text)` and `fold_homophones(text)`.
The contract is in [`ARCHITECTURE.md`](../ARCHITECTURE.md) section 3, the engine choice is in section 5, and
the model download and test commands are in section 9.

- `reader.py`: Tesseract 5 through `tesserocr`, loaded once. `read_page` returns Tesseract's own text lines
  (normalized, with `(left, top, width, height)` pixel boxes, in reading order); `read_line` reads one
  cropped sign line. `OCR_LANG` picks `amh`, `Ethiopic` or `amh+Ethiopic` (default, both together).
- `compare_models.py`: `python -m ocr.compare_models <private photos folder>` prints the character error
  rate per block and the mean for each model setting. `scoring.py` holds the `cer` function it shares with the tests.
- `normalize.py`: fixes OCR mistakes only and never re-spells a correctly read word. It also turns a
  misread line-start bullet (`-`, `.`) into `•` and drops a space before `።` `፣` `፤` `፥`. The mistakes
  that were rejected as rules, and why, are in `ARCHITECTURE.md` section 10. `fold_homophones` is
  separate and is not part of the pipeline; only the scoring experiment uses it.
- `tests/`: normalizer tables, plus the real engine on a generated Ebrima page (line count, box overlap,
  character error rate).

No confidence cut-off is used (measured, see `ARCHITECTURE.md` section 10; `python -m ocr.confidence_cutoffs
<folder>` re-runs the measurement). Still to do: grow `normalize` as real OCR mistakes turn up (each new rule with a test). Handwriting uses the same
`read_page` path as an experimental baseline.

Run the tests from the repo root: `python -m pytest ocr`.
