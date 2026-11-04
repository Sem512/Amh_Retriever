"""normalize() and fold_homophones(): input -> expected output tables, no OCR engine needed.

Run from the repo root: python -m pytest ocr
"""
import pytest

from ocr.normalize import fold_homophones, normalize


@pytest.mark.parametrize("raw, expected", [
    ("ሰላም፡፡", "ሰላም።"),                  # amh model writes the full stop as two ፡
    ("ሰላም::", "ሰላም።"),
    ("ሰላም፡ነው", "ሰላም ነው"),              # word separator between letters
    ("ሰላም : ነው", "ሰላም ነው"),
    ("ሰላም  ነው ", "ሰላም ነው"),            # extra spaces
    ("ሰላም።", "ሰላም።"),                  # already correct: untouched
    ("ሰዓት 2:30", "ሰዓት 2:30"),            # a colon in a time is not a separator
    ("é", "é"),                  # NFC
    ("   ", ""),
    ("", ""),
])
def test_normalize(raw, expected):
    assert normalize(raw) == expected


def test_normalize_is_idempotent():
    for raw in ("ሰላም፡፡", "ሰላም፡ነው ::", "አማርኛ"):
        assert normalize(normalize(raw)) == normalize(raw)


@pytest.mark.parametrize("raw, expected", [
    ("ሐሑ", "ሀሁ"), ("ኀኁ", "ሀሁ"),           # ሐ ኀ -> ሀ, all vowel orders line up
    ("ሠሡ", "ሰሱ"),
    ("ዐዓ", "አኣ"),
    ("ፀፁ", "ጸጹ"),
    ("ሰላም አማርኛ", "ሰላም አማርኛ"),         # already canonical
])
def test_fold_homophones(raw, expected):
    assert fold_homophones(raw) == expected
