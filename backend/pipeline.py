"""Runs one photo through the lanes: clean -> read -> to_sentences -> translate (ARCHITECTURE.md section 3).

run() returns (image, segments): `image` is the array every box refers to, and each segment is
{"amharic": str, "english": str, "boxes": [(left, top, width, height), ...]} in pixels of `image`.
"""
import cv2
import numpy as np

from backend.translate import translate
from ocr.reader import read_page

MAX_SIDE = 2500


def _resized(photo):
    scale = min(1.0, MAX_SIDE / max(photo.shape[:2]))
    return cv2.resize(photo, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else photo


def run(photo, mode):
    # shortcut: resize stands in for Kibreab's clean(); swap it in when his function lands
    image = _resized(photo)
    if mode != "document":
        return image, _placeholder(image)  # shortcut: sign and handwriting return a fixed sample until their tickets land
    lines = read_page(image)
    # shortcut: one OCR line = one segment, so a sentence broken across lines is translated in halves; replace with to_sentences()
    english = translate([line["text"] for line in lines])
    return image, [{"amharic": line["text"], "english": en, "boxes": [line["box"]]} for line, en in zip(lines, english)]


def warm_up():
    """Loads the OCR engine and the translation model now, so the first photo is not 20 s slower than the rest."""
    read_page(np.full((100, 300, 3), 255, np.uint8))
    translate(["ሰላም።"])


def _placeholder(image):
    h, w = image.shape[:2]
    return [{"amharic": "ይህ የሙከራ ውጤት ነው።", "english": "This is a test result.", "boxes": [(w // 10, h // 10, w * 8 // 10, h // 20)]}]
