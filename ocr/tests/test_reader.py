"""read_page / read_line against a generated page, with the real Tesseract (about a second to load)."""
from ocr.reader import read_line, read_page
from ocr.tests.conftest import cer, iou


def test_cer_helper():
    assert cer("abcd", "abcd") == 0 and cer("abcd", "abxd") == 0.25 and cer("abcd", "") == 1


def test_read_page_finds_every_line_in_order(page):
    lines = read_page(page["image"])
    assert len(lines) == len(page["lines"])
    for read, expected, box in zip(lines, page["lines"], page["boxes"]):
        assert cer(expected, read["text"]) < 0.05
        assert iou(read["box"], box) > 0.5


def test_boxes_are_left_top_width_height_ints(page):
    for line in read_page(page["image"]):
        left, top, width, height = line["box"]
        assert all(isinstance(v, int) for v in line["box"]) and width > 0 and height > 0
        assert left + width <= page["image"].shape[1] and top + height <= page["image"].shape[0]


def test_read_page_returns_only_text_and_box_but_the_engine_confidence_is_visible(page):
    from ocr.reader import _read_lines

    assert all(set(line) == {"text", "box"} for line in read_page(page["image"]))
    inner = _read_lines(page["image"])
    assert len(inner) == len(page["lines"]) and all(0 <= line["confidence"] <= 100 for line in inner)


def test_text_is_normalized(page):
    text = "".join(line["text"] for line in read_page(page["image"]))
    assert "፡፡" not in text and "  " not in text


def test_blank_page_has_no_lines():
    import numpy as np

    assert read_page(np.full((200, 400, 3), 255, np.uint8)) == []


def test_read_line_on_a_cropped_line(page):
    left, top, width, height = page["boxes"][0]
    crop = page["image"][top - 12:top + height + 12, left - 12:left + width + 12]
    assert cer(page["lines"][0], read_line(crop)) < 0.05
