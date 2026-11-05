"""Runs one photo through the lanes: clean -> read -> to_sentences -> translate (ARCHITECTURE.md section 3).

run() returns (image, segments): `image` is the array every box refers to, and each segment is
{"amharic": str, "english": str, "boxes": [(left, top, width, height), ...]} in pixels of `image`.
"""
import cv2
import numpy as np

from backend.translate import translate
from ocr.reader import read_line, read_page

try:
    from preprocessing import crop_line, find_lines
except ImportError:  # shortcut: Kibreab's lane has not landed, so sign mode returns the placeholder; delete this guard when it does
    crop_line = find_lines = None

MAX_SIDE = 2500


def _resized(photo):
    scale = min(1.0, MAX_SIDE / max(photo.shape[:2]))
    return cv2.resize(photo, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else photo


def run(photo, mode):
    # shortcut: resize stands in for Kibreab's clean(); swap it in when his function lands
    image = _resized(photo)
    if mode == "sign":
        return image, _placeholder(image) if find_lines is None else _sign(image)
    lines = read_page(image)  # handwriting takes the same path as document; it is experimental (about 75% character errors, ARCHITECTURE.md section 10)
    # shortcut: one OCR line = one segment, so a sentence broken across lines is translated in halves; replace with to_sentences()
    english = translate([line["text"] for line in lines])
    return image, [{"amharic": line["text"], "english": en, "boxes": [line["box"]]} for line, en in zip(lines, english)]


def _sign(image):
    """Each line found on the sign is cropped and read on its own; its box is the upright rectangle around its four corners."""
    height, width = image.shape[:2]
    found = []
    for corners in find_lines(image):
        text = read_line(crop_line(image, corners))
        if text:  # clamped, because a tilted line's corner can fall just outside the image
            xs = [min(max(int(x), 0), width) for x, _ in corners]
            ys = [min(max(int(y), 0), height) for _, y in corners]
            found.append((text, (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))))
    english = translate([text for text, _ in found])
    return [{"amharic": text, "english": en, "boxes": [box]} for (text, box), en in zip(found, english)]


def warm_up():
    """Loads the OCR engine and the translation model now, so the first photo is not 20 s slower than the rest."""
    read_page(np.full((100, 300, 3), 255, np.uint8))
    translate(["ሰላም።"])


def _placeholder(image):
    h, w = image.shape[:2]
    return [{"amharic": "ይህ የሙከራ ውጤት ነው።", "english": "This is a test result.", "boxes": [(w // 10, h // 10, w * 8 // 10, h // 20)]}]
