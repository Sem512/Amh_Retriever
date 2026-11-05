"""pipeline.run and POST /translate in document mode, with fake reader and translator (no models load)."""
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend import app as app_module
from backend import pipeline

LINES = [
    {"text": "ሰላም ነው።", "box": (20, 10, 100, 30)},
    {"text": "እንዴት ነህ?", "box": (20, 60, 120, 30)},
]


@pytest.fixture
def fakes(monkeypatch):
    seen = {"read": 0, "translated": None}

    def read_page(image):
        seen["read"] += 1
        return LINES

    def translate(texts):
        seen["translated"] = texts
        return [f"en:{t}" for t in texts]

    monkeypatch.setattr(pipeline, "read_page", read_page)
    monkeypatch.setattr(pipeline, "translate", translate)
    return seen


def photo(w=400, h=200):
    return np.full((h, w, 3), 255, np.uint8)


def test_document_mode_returns_one_segment_per_line(fakes):
    image, segments = pipeline.run(photo(), "document")
    assert image.shape[:2] == (200, 400)
    assert fakes["translated"] == ["ሰላም ነው።", "እንዴት ነህ?"]
    assert segments == [
        {"amharic": "ሰላም ነው።", "english": "en:ሰላም ነው።", "boxes": [(20, 10, 100, 30)]},
        {"amharic": "እንዴት ነህ?", "english": "en:እንዴት ነህ?", "boxes": [(20, 60, 120, 30)]},
    ]


def test_photo_without_text_gives_no_segments(monkeypatch):
    monkeypatch.setattr(pipeline, "read_page", lambda image: [])
    monkeypatch.setattr(pipeline, "translate", lambda texts: [])
    assert pipeline.run(photo(), "document")[1] == []


def test_sign_mode_keeps_the_placeholder_and_skips_the_reader(fakes):
    _, segments = pipeline.run(photo(), "sign")
    assert fakes["read"] == 0 and len(segments) == 1


def test_handwriting_mode_reads_the_page_like_document_mode(fakes):
    assert pipeline.run(photo(), "handwriting")[1] == pipeline.run(photo(), "document")[1]
    assert fakes["read"] == 2


def test_api_handwriting_mode_returns_the_standard_shape(fakes):
    png = cv2.imencode(".png", photo())[1].tobytes()
    r = TestClient(app_module.app).post("/translate", files={"file": ("p.png", png, "image/png")}, data={"mode": "handwriting"})
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "handwriting"
    assert [(s["amharic"], s["english"]) for s in body["segments"]] == [("ሰላም ነው።", "en:ሰላም ነው።"), ("እንዴት ነህ?", "en:እንዴት ነህ?")]
    assert body["segments"][0]["bboxes"] == [{"x": 0.05, "y": 0.05, "w": 0.25, "h": 0.15}]


def test_large_photo_is_resized_and_boxes_refer_to_the_resized_image(fakes):
    image, _ = pipeline.run(photo(w=5000, h=2500), "document")
    assert max(image.shape[:2]) == pipeline.MAX_SIDE


def test_warm_up_loads_both_engines(fakes):
    pipeline.warm_up()
    assert fakes["read"] == 1 and fakes["translated"] == ["ሰላም።"]


def test_server_start_warms_the_models(monkeypatch):
    called = []
    monkeypatch.setattr(pipeline, "warm_up", lambda: called.append(1))
    with TestClient(app_module.app):
        pass
    assert called == [1]


def test_failed_warm_up_does_not_stop_the_server(monkeypatch, fakes):
    def no_models():
        raise RuntimeError("no model files")

    monkeypatch.setattr(pipeline, "warm_up", no_models)
    png = cv2.imencode(".png", photo())[1].tobytes()
    with TestClient(app_module.app) as client:
        assert client.post("/translate", files={"file": ("p.png", png, "image/png")}).status_code == 200


def test_api_document_mode_end_to_end_with_fakes(fakes):
    png = cv2.imencode(".png", photo())[1].tobytes()
    r = TestClient(app_module.app).post("/translate", files={"file": ("p.png", png, "image/png")}, data={"mode": "document"})
    assert r.status_code == 200
    body = r.json()
    assert [s["amharic"] for s in body["segments"]] == ["ሰላም ነው።", "እንዴት ነህ?"]
    assert body["segments"][0]["bboxes"] == [{"x": 0.05, "y": 0.05, "w": 0.25, "h": 0.15}]
    assert body["image"]["width"] == 400 and body["image"]["height"] == 200
