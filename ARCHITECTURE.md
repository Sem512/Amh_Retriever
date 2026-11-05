# Amharic Image Translator: Architecture

**Status:** agreed plan, 26 Oct 2026. It replaces the earlier semantic-retrieval design (in git history
before this commit). The scope change was approved by the advisor.

## 1. What it does

One photo in, Amharic read, English out.

- **Input:** one JPG or PNG photo or scan, up to 10 MB. The user picks a **mode**: `document`
  (default), `sign` (signs, posters, menus) or `handwriting` (experimental).
- **Output:** each Amharic sentence next to its English translation. Selecting a sentence highlights
  its lines on the image.
- **Not built:** storage, accounts, search, editing the recognised text, other languages or
  directions, PDFs, live camera, online hosting, training our own models.
- **Priority:** printed documents must work; signs come second; handwriting is a stretch goal whose
  accuracy is reported honestly.
- **Runs** locally on one laptop, with free and open-source tools only.

## 2. Pipeline

```mermaid
flowchart TB
    P["Photo + mode"] --> C["clean<br/>Kibreab"]
    C -->|document, handwriting| R["read_page<br/>Ferid"]
    C -->|sign| F["find_lines + crop_line<br/>Kibreab"]
    F --> L["read_line, once per line<br/>Ferid"]
    R --> S["to_sentences<br/>Semir"]
    L --> S
    S --> T["translate<br/>Semir"]
    T --> A["POST /translate response"]
```

| Mode | `clean()` | Finding lines | Reading |
|---|---|---|---|
| `document` | straighten, crop, black and white | Tesseract's own layout analysis | Tesseract, page mode |
| `sign` | resize only (the whole photo is not straightened) | text-finder marks each line; each line is cut out, straightened, flipped to dark-on-light, padded ~10 px | Tesseract `--psm 7`, one line at a time |
| `handwriting` | as `document` | as `document` | Tesseract baseline (experimental). Surya-Fidel only if M1 and M2 are done by 15 Nov |

## 3. Lane contracts

These functions are the whole coordination surface between lanes. Each lane builds and tests against a
folder of sample photos, so nobody waits for anybody.

**Shared conventions**

- **Images** are numpy `uint8` arrays as OpenCV uses them: H×W×3 BGR for colour, H×W for grayscale.
- **Pixel boxes** are `(left, top, width, height)` integers, in the coordinate space of the image that
  `clean()` returned.
- **Line corners** (sign mode) are four `(x, y)` points, clockwise from top-left, in the same space.

| Owner | Function | Input → output |
|---|---|---|
| Kibreab | `clean(photo, mode)` | photo, mode → image, long side ≤ 2500 px. **This is the image the viewer shows; every box refers to it.** |
| Kibreab | `find_lines(image)` | → list of line corners |
| Kibreab | `crop_line(image, corners)` | → upright line image, dark text on light, ~10 px margin |
| Ferid | `read_page(image)` | → `[{"text": str, "box": (l, t, w, h)}, ...]`, one per text line, in reading order. Text is already normalized (below); lines that end up empty are dropped. |
| Ferid | `read_line(line_image)` | → `str`, normalized |
| Ferid | `normalize(text)` | Fixes OCR mistakes: Unicode NFC; `፡፡` and `::` → `።`; `፡` or a stray `:` between Amharic letters → a space; a space before `።` `፣` `፤` `፥` removed; a line-start `-` or `.` before an Amharic word → the bullet `•`; extra whitespace collapsed. **Never re-spells a correctly read word.** New rules are added only when real OCR output shows a mistake, each with a test. Runs inside both readers. |
| Ferid | `fold_homophones(text)` | Merges same-sound letters (ሐ ኀ → ሀ, ሠ → ሰ, ዐ → አ, ፀ → ጸ). **Not called by the pipeline.** Only the scoring experiment uses it, to test whether folding improves translation; it ships only if the scores say so. |
| Semir | `to_sentences(lines)` | `[{"text", "box"}]` → `[{"amharic": str, "boxes": [box, ...]}]`. Joins lines, splits after `።` `፧` `!`, rejoins words split across lines, **never changes spelling**. Character-level fixes (including `፡` → space) are already done by `normalize`. |
| Semir | `translate(sentences)` | `list[str]` Amharic → `list[str]` English, same order |
| Semir | `pipeline.run(photo, mode)` | Wires the above. A sign line's box is the upright rectangle enclosing its corners. **Today (5 Nov):** `document` and `handwriting` are real and take the same path. It resizes the photo, runs `read_page`, translates, and treats **each OCR line as one segment**. That is temporary: a sentence that runs across lines is translated in halves until `to_sentences` replaces it. `sign` still returns a fixed placeholder. |

## 4. API contract (backend → frontend)

**Request:** `POST /translate`, multipart form.

- `file`: JPG or PNG, up to 10 MB.
- `mode`: `document` (default), `sign` or `handwriting`.

The call is synchronous, with no job IDs and no polling. The target is about 10 s for a typical page.

**Response:**

```json
200 {
  "mode": "document",
  "took_ms": 8421,
  "image":    { "data_url": "data:image/png;base64,…", "width": 1654, "height": 2339 },
  "segments": [
    { "id": 0, "amharic": "…", "english": "…",
      "bboxes": [ {"x": 0.10, "y": 0.18, "w": 0.80, "h": 0.04} ] }
  ]
}
```

- `image` is the image the boxes refer to (the output of `clean()`). The viewer shows it directly.
- `bboxes` are 0–1 fractions of that image, one per line, origin top-left. This is the format the
  frontend's `getBoxes` already reads.
- If no text is found, the response is `200` with `segments: []`.

**Errors** come back as `{"detail": "…"}`:

| Status | When |
|---|---|
| `400` | the file is not a readable JPG or PNG |
| `413` | the file is over 10 MB |
| `422` | `mode` is not one of the three values |
| `500` | an engine failed |

CORS allows `http://localhost:5173`. Phone photos are turned upright using their EXIF orientation tag
when the API decodes them (OpenCV does this).

## 5. Engines, hardware, licenses

| Part | Choice | License |
|---|---|---|
| OCR | Tesseract 5, `tessdata_best` `amh` and `script/Ethiopic` run together (`amh+Ethiopic`), chosen by character error rate on the real printed blocks (section 10). | Apache 2.0 |
| Sign text-finder | PP-OCRv5 mobile detector via RapidOCR/onnxruntime. Fallback: OpenCV's DNN text detector. Unproven on Ethiopic; measured on our sign photos. | Apache 2.0 |
| Translation | `facebook/nllb-200-distilled-600M`, which we convert to CTranslate2 int8 ourselves | **CC-BY-NC 4.0 (non-commercial)**, disclosed in the report |
| Handwriting (stretch only) | `kiyam/surya-fidel-amharic` in its own Python ≤ 3.13 environment | CC-BY-NC-SA + Datalab terms |

**Translation device:**

- Translation runs on the GPU (GTX 1650; only about 1.3–1.5 GB of its 4 GB is free while the
  desktop runs).
- CUDA's cuBLAS library comes from the `nvidia-cublas-cu12` pip package, so no CUDA toolkit install
  is needed.
- If the GPU fails at load time, translation **falls back to the CPU automatically** and logs a
  warning. `TRANSLATE_DEVICE=cpu` forces the CPU.

**Environment:** one Python 3.14 venv for the main app. Every package it needs has Windows wheels
(checked 25 Oct). All models are downloaded ahead of time, so the demo runs offline.

## 6. Quality and testing

**Test set:** 25 photos.

| Group | Photos |
|---|---|
| Printed, short passages of 5–15 lines | 12 |
| Signs and posters | 8 |
| Handwritten | 5 |

Each photo gets its hand-typed Amharic and a reference English translation, about 6–7 photos per
person. They live in a **private shared folder, never this public repo**, with no real personal data in
any photo.

**Scores:**

- Character error rate (CER) for reading.
- chrF for translation.
- Translation is also scored on the hand-typed Amharic, which separates reading mistakes from
  translation mistakes.

**Code tests** (run from the repo root with `python -m pytest backend`):

- Fast tests with fake engines, covering the API contract, the box conversion, sentence splitting
  and the GPU fallback.
- One slow test with the real engines.
- The frontend's browser suite, pointed at the real API.

## 7. Schedule

| When | Milestone and tasks |
|---|---|
| 26 Oct – 1 Nov | **Setup.** Semir: this doc, API skeleton (fixed sample response) with contract tests, NLLB conversion and timing test. Ferid: Tesseract and `read_page`. Kibreab: `clean` for documents. Yassin: upload screen and mode picker against the skeleton. **Everyone: test photos in the shared folder by Tue 3 Nov.** |
| 2 – 8 Nov | **M1: printed text works end to end.** `to_sentences`, real pipeline, scoring script. Ferid picks `amh` or Ethiopic. Yassin's viewer runs on the real API. |
| 9 – 15 Nov | **M2: signs work and handwriting has a baseline.** `find_lines`, `crop_line`, `read_line`; all three modes wired and scored. **15 Nov: decide whether to attempt Surya.** |
| 16 – 17 Nov | Surya helper if M1 and M2 are done; otherwise fix the worst problems the scores showed. |
| **Wed 18 Nov** | **Feature freeze.** All models pre-downloaded; the demo runs offline. |
| 18 – 21 Nov | User tests with 5–8 people; bug fixes only; final scores go into the report. |
| 22 – 24 Nov | Rehearsal and fixes only. |
| **Wed 25 Nov** | Defense. |

## 8. Risks

1. **Sign and handwriting accuracy.** Reading Amharic signs is unproven. The best available
   handwriting model gets about 17% of characters wrong, even on clean scans.
2. **GPU memory** is shared with the display, so the translation model may land on the CPU, which is
   slower.
3. **The Surya window** is only 16–17 Nov, so handwriting will most likely ship as the Tesseract
   baseline.
4. **Ethiopian clock times** are mistranslated as Western times (section 10), which matters for signs
   showing opening hours. Report it as a limitation unless there is time to fix it.

## 9. Backend setup

```
python -m venv .venv
.venv\Scripts\pip install -r backend\requirements.txt
```

One-time model conversion. It also needs CPU torch and downloads about 2.5 GB.

```
.venv\Scripts\pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv\Scripts\ct2-transformers-converter --model facebook/nllb-200-distilled-600M --quantization int8 --output_dir models\nllb-200-distilled-600M-ct2-int8 --copy_files tokenizer.json sentencepiece.bpe.model tokenizer_config.json special_tokens_map.json
```

OCR model files (about 19 MB). `tesserocr` from `requirements.txt` already bundles Tesseract 5.5, so
nothing is installed system-wide:

```
mkdir models\tessdata
curl.exe -L -o models\tessdata\amh.traineddata https://github.com/tesseract-ocr/tessdata_best/raw/main/amh.traineddata
curl.exe -L -o models\tessdata\Ethiopic.traineddata https://github.com/tesseract-ocr/tessdata_best/raw/main/script/Ethiopic.traineddata
```

`OCR_LANG` picks the model: `amh`, `Ethiopic`, or `amh+Ethiopic` (the default, both together).
To re-run the model comparison on the private test photos:

```
.venv\Scripts\python -m ocr.compare_models <private test-photos folder>
```

Run the API and the tests, both from the repo root:

```
.venv\Scripts\uvicorn backend.app:app
.venv\Scripts\python -m pytest backend ocr
```

The OCR tests draw known Amharic text with the Ebrima font that ships with Windows, so they need no
photos. They skip themselves, with a reason, if the model files or the font are missing. One more test
checks `normalize` against the private answer key; set `AMH_TEST_PHOTOS` to the private test-photos folder to
run it, otherwise it skips.

## 10. Measurements

**26 Oct 2026, translation timing test.** 20 realistic Amharic sentences (about one page) on the demo
laptop (i5-10500H, GTX 1650):

| Device | Load at startup | 20 sentences, warm | Per sentence | GPU memory |
|---|---|---|---|---|
| GPU (CUDA via `nvidia-cublas-cu12`) | ~17 s | **0.51 s** | 0.025 s | +0.9 GB (1.8 → 2.7 of 4 GB) |
| CPU (fallback) | ~17 s | 4.2 s | 0.21 s | — |

- Translation leaves most of the 10-second budget for cleanup and OCR, even on the CPU fallback.
- Translations of the samples read correctly.
- **Ethiopian clock times** come out wrong: "ከጠዋቱ ሁለት ሰዓት" (8 a.m. in Ethiopian time) was
  translated as "2:00 a.m.".
- transformers warns about an "incorrect regex pattern" when the tokenizer loads. The warning is
  aimed at Mistral models: the tokens match the original SentencePiece model for whitespace-stripped
  text, which is what `translate()` sends.
- **OCR, 4 Nov 2026, generated page** (4 lines of Ebrima text, so clean input and an upper bound):

  | Model | Lines found | Character error rate |
  |---|---|---|
  | `amh` (`tessdata_best`) | 4 of 4, in order | **1.1%** (2 errors in 189 characters) |
  | `script/Ethiopic` | 4 of 4, in order | 6.3% (12 errors in 189 characters) |

  `amh` also wrote the full stop as `፡፡` on two lines, which is why `normalize` exists. This is one
  clean page: the choice between the models is made on the real printed photos (next item).
- **OCR model choice, 5 Nov 2026, 8 printed blocks** (`python -m ocr.compare_models`; both the OCR text
  and the answer key go through `normalize()` before scoring). Six blocks are from one CDC flyer scan,
  one is a 1930 booklet page, one is a clean typed page from the Fidel dataset:

  | Model | Mean character error rate | Blocks won outright |
  |---|---|---|
  | `amh` | 20.3% | 0 |
  | `script/Ethiopic` | 17.5% | 2 |
  | **`amh+Ethiopic`** (both together) | **16.6%** | **5** |

  `amh+Ethiopic` is lower than `amh` on all 8 blocks. Against `Ethiopic` alone it wins 5, loses 2 (the
  flyer's `c` and `e`) and ties 1. `amh` is ahead of `Ethiopic` only on clean text (Fidel page 4.9% vs
  7.4%, generated page 1.1% vs 6.3%); on the real scans `Ethiopic` is ahead, largely because `amh` cannot
  read Latin letters and digits: "የ COVID-19" came out as "የርዐሃሀ-19". Counting Ethiopic characters only,
  the order is the same (16.6%, 14.3%, 13.1%). **The default is now `amh+Ethiopic`.** The cost is time:
  a full 48-line flyer page reads in 2.6 s, against 1.9 s (`amh`) and 1.8 s (`Ethiopic`).

  The evidence is thin: 8 blocks from 3 sources, a first-pass answer key with one reader, and the margin
  over `Ethiopic` alone is 0.9 points. The choice stands unless the team's own phone photos say
  otherwise: re-run the command above on a larger set, or set `OCR_LANG` to switch. These numbers are
  from before the normalization rules below; with the rules the order is the same (`amh` 20.3 → 18.9%,
  `Ethiopic` 17.5 → 16.9%, `amh+Ethiopic` 16.6 → 15.5%).
- **Normalization rules from real mistakes, 5 Nov 2026** (same 8 blocks, `amh+Ethiopic`, 124 edit
  operations between the OCR text and the answer key). Mean character error rate **16.6% → 15.5%**.

  | Mistake | How often | Decision |
  |---|---|---|
  | A list bullet `•` read as `-` or `.` | 15 times | **Rule.** Line-start `-` or `.` before an Amharic word → `•`. Alone: 16.6% → 15.9%. A real dash at the start of a line is also turned into a bullet, which is harmless for translation. |
  | A space before `።` `፣` `፤` `፥` | 3 times, all in the 1930 booklet | **Rule.** Space removed. Alone: 16.6% → 16.2%. Thin evidence, but it can never change a letter. |
  | `እ` read as `አ` at the start of a word (`እና` → `አና`, `እስከ` → `አስከ`) | 18 times, the most common mistake | **Rejected.** `አ` also starts 24 correct words in the answer key (`አዲስ`, `አካላት`), so a rule would re-spell 22 correct lines. A fix for `አና` alone (6 times) is rejected too, because `አና` is a real name. |
  | `ህ` read as `ሀ`, `ው` as `ወ`, `ን` as `ገ`, `ኒ` as `ነ` and other look-alike letters | about 20 times | **Rejected.** Both letters are real, so only a spelling dictionary could decide. Handled by choosing the model (ticket 03) or, if it helps translation, the letter-merging experiment (ticket 08). |
  | Missing spaces between words (`ነክጉዳዮችን`) | 16 times | **Rejected.** Needs a word list to tell where to split. |
  | `COVID-19` read as Ethiopic letters (`ርዐህዐ-ገ9`) | 8 times | **Rejected.** Not recoverable from the text. |
  | A word separator read as `;` or `:` at the end of a word | 3 times, all in the 1930 booklet | **Rejected.** A real colon can end a modern word, so it cannot be told apart. |
  | Heading lines the engine did not return at all (flyer `a`, `c`, `f`) | 3 blocks | Not a text mistake: a line-finding question for ticket 05. |

  Two of the rejected rules were tried on the OCR output, and each would have changed correct answer-key
  text (word-initial `አ` → `እ` changes 22 lines, `ህ` → `ሀ` changes 10). The new test
  `test_normalize_does_not_respell_the_answer_key` runs when `AMH_TEST_PHOTOS` points at the private
  folder and skips with a reason otherwise. It lets `normalize` change only spaces and word separators
  on every answer-key line, so a future rule that edits a letter fails it. The old-print `፡` words in the
  booklet and one spaced colon in the Fidel page are turned into spaces on purpose by an earlier rule, so
  those 5 lines are not unchanged, only un-respelled.
- **Confidence cut-off, 5 Nov 2026: none needed.** The reader now reads each line's confidence (0 to
  100) internally; `read_page` still returns only `text` and `box`. `python -m ocr.confidence_cutoffs`
  drops the lines below each cut-off and counts what is lost (`amh+Ethiopic`; 75 lines on the answer-key
  blocks, 20 handwriting, 50 scene, 458 on the 10 printed scans):

  | Cut-off | Blocks CER | Block lines lost | Handwriting lost (of 20) | Scene lost (of 50) | Scan lines lost (of 458) |
  |---|---|---|---|---|---|
  | none | 15.5% | 0 | 0 | 0 | 0 |
  | 30 | 15.5% | 0 | 1 | 3 | 14 |
  | 40 | 15.5% | 0 | 10 | 13 | 33 |
  | 50 | 15.5% | 0 | 18 | 21 | 71 |
  | 60 | 18.9% | 2 | 20 | 24 | 141 |
  | 70 | 22.9% | 5 | 20 | 32 | 203 |
  | 80 | 39.4% | 19 | 20 | 37 | 285 |

  Why no cut-off: confidence does not separate good lines from bad. A line read with no mistakes scored
  71 and lines with 10 to 20% errors scored 90 or more, and all 75 block lines are real text (lowest 57).
  Handwriting sits at 11 to 54 and the sign photos at 0 to 97, which is exactly where a cut-off would
  bite, and real Amharic lines on the old scans also score 37 to 47 (`የንግድና የኢንደስትሪ ሚነክቴር`, 37). The
  only clear junk is below 30: 14 of 458 scan lines, by eye all specks or the gazette's English text read
  as Ethiopic letters (`ጊረ...`, `+ P`, `ont im this Misia`). That is 3% of lines on bilingual pages, and
  the better fix for those is spotting Latin text, not confidence. **If the team's own phone photos show
  junk rows, 30 is the highest cut-off that lost no real line here:** set it in one place in `reader.py`
  and re-run the command. Only phone photos can say whether it holds there; the scans are not phone
  photos.
- **Handwriting baseline, 5 Nov 2026 (experimental).** `handwriting` mode reads through `read_page`, like
  `document`. The 5 Fidel handwriting samples (4 lines each, nothing to copy or crop) were audited
  against their labels first, because the earlier printed sample had misaligned labels: every sample
  has the label line count of its image (4 and 4); the word count per line matches the image on 8 of 20
  lines and is within one on 6 more (the rest are lines where my blob count merged tight words); and on
  the 3 samples where the reader found 4 lines, all 12 lines are closest to their own label line, not
  another. So the labels are aligned line by line. This does **not** check letters: handwriting is
  read by eye only for order and word groups, and a person who reads Amharic should confirm the letters.

  | Setting | Mean character error rate on the 5 samples |
  |---|---|
  | `amh` | 77.1% |
  | `Ethiopic` | 75.2% |
  | **`amh+Ethiopic`** (default) | **75.2%** |

  About three characters in four are wrong, so the output is not usable as text; the mode is labelled
  experimental and exists as a baseline. The reader found 3 lines on one sample and 5 on another, so line
  finding also fails on loose handwriting. Surya-Fidel is the way past this (decide on 15 Nov).
- **Through the API, 4 Nov 2026, `document` mode with the real engines** (resize only for cleanup, one
  segment per OCR line):

  | Photo | Segments | Time |
  |---|---|---|
  | A real printed scan (6 lines), **first request after start** | 6 | **24.8 s**: it loads the translation model and the OCR engine |
  | The same scan, warm | 6 | 1.4 s |
  | A 48-line CDC flyer scan, warm | 48 | 2.4 s |
  | A blank photo | 0 | 7 ms |

  The first request after the server starts was far over the 10-second target, because the models load
  on demand. **Fixed the same day:** the server now loads both models at startup (17.6 s, once), and the
  first photo after start takes 1.3 s. If the warm-up fails, for example because model files are missing,
  it logs a warning and the server still starts, so the placeholder modes keep working; the models then
  load on the first request, as before.
- Found during the test: cuBLAS loads on first use, not at model load. `_open()` therefore runs one
  tiny translation at startup, so a broken GPU falls back to the CPU there rather than failing inside
  a user's request.
