"""A generated test page: known Amharic text drawn with Ebrima at known positions, so reader tests need no photos."""
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont

from ocr.reader import TESSDATA

FONT = Path(r"C:\Windows\Fonts\ebrima.ttf")
LINES = [
    "ማንኛውም ሰው ከስራ የሚያገኘው ገቢ በዚህ አዋጅ መሠረት የሥራ ግብር ይከፈልበታል።",
    "ግብር ከፋይ ዓመታዊ የገቢ መግለጫውን ከዓመቱ መጨረሻ በኋላ በአራት ወር ውስጥ ማቅረብ አለበት።",
    "ሠራተኛው ዓመታዊ የዕረፍት ፈቃድ የማግኘት መብት አለው።",
    "ሱቁ ከጠዋቱ ሁለት ሰዓት እስከ ማታ አሥራ ሁለት ሰዓት ክፍት ነው።",
]


@pytest.fixture(scope="session")
def page():
    if not FONT.exists() or not (TESSDATA / "amh.traineddata").exists():
        pytest.skip("needs the Ebrima font and models/tessdata/amh.traineddata (ARCHITECTURE.md section 9)")
    font = ImageFont.truetype(str(FONT), 34)
    img = Image.new("RGB", (1700, 90 + 80 * len(LINES)), "white")
    draw = ImageDraw.Draw(img)
    boxes = []
    for i, text in enumerate(LINES):
        xy = (60, 50 + 80 * i)
        draw.text(xy, text, font=font, fill="black")
        left, top, right, bottom = draw.textbbox(xy, text, font=font)
        boxes.append((left, top, right - left, bottom - top))
    return {"image": np.array(img)[..., ::-1], "lines": LINES, "boxes": boxes}  # BGR like OpenCV


def cer(expected, actual):
    """Character error rate: edit distance / length of the expected text."""
    row = list(range(len(actual) + 1))
    for i, a in enumerate(expected, 1):
        prev, row[0] = row[0], i
        for j, b in enumerate(actual, 1):
            prev, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, prev + (a != b))
    return row[-1] / len(expected)


def iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    w = min(ax + aw, bx + bw) - max(ax, bx)
    h = min(ay + ah, by + bh) - max(ay, by)
    inter = max(0, w) * max(0, h)
    return inter / (aw * ah + bw * bh - inter)
