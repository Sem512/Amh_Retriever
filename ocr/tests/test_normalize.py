"""normalize() and fold_homophones(): input -> expected output tables, no OCR engine needed.

Run from the repo root: python -m pytest ocr
"""
import json
import os
import re
from pathlib import Path

import pytest

from ocr.normalize import fold_homophones, normalize


@pytest.mark.parametrize("raw, expected", [
    ("ሰላም፡፡", "ሰላም።"),                  # amh model writes the full stop as two ፡
    ("ሰላም::", "ሰላም።"),
    ("ሰላም፡ነው", "ሰላም ነው"),              # word separator between letters
    ("ሰላም : ነው", "ሰላም ነው"),
    ("ሰላም  ነው ", "ሰላም ነው"),            # extra spaces
    ("ሰላም።", "ሰላም።"),                  # already correct: untouched
    ("ድረስ ። በርሱ ፣ ነው", "ድረስ። በርሱ፣ ነው"),   # space before Amharic punctuation (old booklet, 3 on the real blocks)
    ("- የግድ በአካል", "• የግድ በአካል"),      # bullet read as - (10 on the real flyer)
    (". በበሽታው የተያዘ", "• በበሽታው የተያዘ"),  # bullet read as . (6 on the real flyer)
    ("• የግድ በአካል", "• የግድ በአካል"),      # a correct bullet is untouched
    ("ሰላም - ነው", "ሰላም - ነው"),            # a dash inside a line is not a bullet
    ("-5 ዲግሪ", "-5 ዲግሪ"),                # a minus sign is not a bullet
    ("ሰዓት 2:30", "ሰዓት 2:30"),            # a colon in a time is not a separator
    ("é", "é"),                  # NFC
    ("   ", ""),
    ("", ""),
])
def test_normalize(raw, expected):
    assert normalize(raw) == expected


def test_normalize_is_idempotent():
    for raw in ("ሰላም፡፡", "ሰላም፡ነው ::", "አማርኛ", "- የግድ ። በአካል"):
        assert normalize(normalize(raw)) == normalize(raw)


def test_normalize_does_not_respell_the_answer_key():
    """normalize() may only change spaces and word separators on correct text; a rule that edits any other character is wrong.

    The old-print separator ፡ and a spaced colon in the key are turned into spaces on purpose, so they are not compared.
    """
    folder = os.environ.get("AMH_TEST_PHOTOS")
    key = Path(folder or "") / "ground_truth_printed.json"
    if not folder or not key.exists():
        pytest.skip("set AMH_TEST_PHOTOS to the private test-photos folder (it holds ground_truth_printed.json)")
    lines = [line for block in json.loads(key.read_text(encoding="utf-8")) for line in block["amharic"].splitlines()]
    assert len(lines) > 50
    solid = lambda s: re.sub(r"[\s፡:]", "", s)
    assert [line for line in lines if solid(normalize(line)) != solid(line)] == []


@pytest.mark.parametrize("raw, expected", [
    ("ሐሑ", "ሀሁ"), ("ኀኁ", "ሀሁ"),           # ሐ ኀ -> ሀ, all vowel orders line up
    ("ሠሡ", "ሰሱ"),
    ("ዐዓ", "አኣ"),
    ("ፀፁ", "ጸጹ"),
    ("ሰላም አማርኛ", "ሰላም አማርኛ"),         # already canonical
])
def test_fold_homophones(raw, expected):
    assert fold_homophones(raw) == expected
