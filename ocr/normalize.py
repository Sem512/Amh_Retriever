"""Fixes OCR mistakes in Amharic text. Spelling of correctly read words is never changed.

normalize() runs inside the readers (ARCHITECTURE.md section 3). fold_homophones() is NOT part of the
pipeline: only the scoring experiment calls it, to test whether merging same-sound letters helps translation.
"""
import re
import unicodedata

_ETHIOPIC = "ሀ-፿"
_FULL_STOP = re.compile(r"፡፡|::")  # Tesseract's amh model writes the full stop as two word-separators
_BETWEEN_LETTERS = re.compile(rf"(?<=[{_ETHIOPIC}])\s*[፡:]\s*(?=[{_ETHIOPIC}])")  # an old-style word separator read as ፡ or :


def normalize(text):
    text = unicodedata.normalize("NFC", text)
    text = _FULL_STOP.sub("።", text)
    text = _BETWEEN_LETTERS.sub(" ", text)
    return " ".join(text.split())


# first syllable of each look-alike family -> the family it is folded into; the 7 vowel orders line up
_FOLD = {
    src + order: dst + order
    for src, dst in ((0x1210, 0x1200), (0x1280, 0x1200),  # ሐ ኀ -> ሀ
                     (0x1220, 0x1230),                    # ሠ -> ሰ
                     (0x12D0, 0x12A0),                    # ዐ -> አ
                     (0x1340, 0x1338))                    # ፀ -> ጸ
    for order in range(7)
}


def fold_homophones(text):
    return text.translate(_FOLD)
