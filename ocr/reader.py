"""Reads Amharic text from images with Tesseract (tesserocr). Contract: ARCHITECTURE.md section 3.

OCR_LANG picks the model in models/tessdata: "amh" (default) or "Ethiopic".
"""
import os
from pathlib import Path

import tesserocr
from PIL import Image

from ocr.normalize import normalize

TESSDATA = Path(__file__).resolve().parent.parent / "models" / "tessdata"
_api = None


def _engine(psm, image):
    global _api
    if _api is None:  # loading the model takes about a second, so do it once
        _api = tesserocr.PyTessBaseAPI(path=str(TESSDATA), lang=os.environ.get("OCR_LANG", "amh"))
    _api.SetPageSegMode(psm)
    _api.SetImage(Image.fromarray(image[..., ::-1] if image.ndim == 3 else image))  # BGR -> RGB
    return _api


def read_page(image):
    """Cleaned page -> [{"text": str, "box": (left, top, width, height)}], one per text line, in reading order."""
    api = _engine(tesserocr.PSM.AUTO, image)
    api.Recognize()
    lines = []
    for line in tesserocr.iterate_level(api.GetIterator(), tesserocr.RIL.TEXTLINE):
        try:
            text = normalize(line.GetUTF8Text(tesserocr.RIL.TEXTLINE))
        except RuntimeError:  # tesserocr raises "No text returned" for a line it found but could not read
            continue
        if text:
            left, top, right, bottom = line.BoundingBox(tesserocr.RIL.TEXTLINE)  # tesserocr gives right/bottom, not width/height
            lines.append({"text": text, "box": (left, top, right - left, bottom - top)})
    return lines


def read_line(line_image):
    """One cropped line (dark text on light) -> its text."""
    return normalize(_engine(tesserocr.PSM.SINGLE_LINE, line_image).GetUTF8Text())
