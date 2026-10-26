# OCR (Ferid)

Delivers `read_page(image)` (whole page: one entry per text line, with its pixel box, in reading
order) and `read_line(line_image)` (one sign line). Exact inputs and outputs are in
[`ARCHITECTURE.md`](../ARCHITECTURE.md) section 3; engine choices are in section 5.

Engine: Tesseract 5 with `tessdata_best`. Compare `amh` with `script/Ethiopic` on the printed test
photos and keep the one with the lower character error rate. Handwriting goes through Tesseract as an
experimental baseline. Engine internals (models, page-segmentation modes, thresholds) are Ferid's call.

Spelling is never changed after OCR: no homophone folding, because the translation model learned
Amharic as people actually write it.

Nothing has been built here yet.
