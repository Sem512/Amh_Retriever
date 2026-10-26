"""Contract tests for POST /translate (ARCHITECTURE.md section 4), with a fake pipeline: no models load.

Run from the repo root: python -m pytest backend
"""
import base64

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend import app as app_module

client = TestClient(app_module.app)


def png_bytes(w=200, h=100):
    return cv2.imencode(".png", np.full((h, w, 3), 255, np.uint8))[1].tobytes()


@pytest.fixture
def fake_pipeline(monkeypatch):
    calls = []

    def run(photo, mode):
        calls.append(mode)
        return photo, [{"amharic": "ሰላም።", "english": "Hello.", "boxes": [(20, 10, 100, 50)]}]

    monkeypatch.setattr(app_module.pipeline, "run", run)
    return calls


def post(data=None, mode=None):
    form = {"mode": mode} if mode else {}
    return client.post("/translate", files={"file": ("p.png", data or png_bytes(), "image/png")}, data=form)


def test_success_shape_and_normalized_boxes(fake_pipeline):
    r = post()
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "document" and fake_pipeline == ["document"]
    assert isinstance(body["took_ms"], int)
    assert body["image"]["width"] == 200 and body["image"]["height"] == 100
    assert body["image"]["data_url"].startswith("data:image/png;base64,")
    assert base64.b64decode(body["image"]["data_url"].split(",", 1)[1]).startswith(b"\x89PNG")
    assert body["segments"] == [
        {"id": 0, "amharic": "ሰላም።", "english": "Hello.", "bboxes": [{"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5}]}
    ]


def test_mode_is_passed_through(fake_pipeline):
    assert post(mode="sign").json()["mode"] == "sign"
    assert fake_pipeline == ["sign"]


def test_no_text_is_an_empty_list(monkeypatch):
    monkeypatch.setattr(app_module.pipeline, "run", lambda photo, mode: (photo, []))
    r = post()
    assert r.status_code == 200 and r.json()["segments"] == []


def test_not_an_image_is_400(fake_pipeline):
    r = post(data=b"%PDF-1.7 not an image")
    assert r.status_code == 400 and "JPG or PNG" in r.json()["detail"]


def test_corrupt_png_is_400(fake_pipeline):
    r = post(data=b"\x89PNG\r\n\x1a\n" + b"garbage")
    assert r.status_code == 400


def test_too_large_is_413(fake_pipeline):
    r = post(data=b"\x89PNG\r\n\x1a\n" + b"0" * app_module.MAX_BYTES)
    assert r.status_code == 413 and "10 MB" in r.json()["detail"]


def test_bad_mode_is_422(fake_pipeline):
    r = post(mode="poster")
    assert r.status_code == 422 and fake_pipeline == []


def test_engine_failure_is_500_with_detail(monkeypatch):
    def boom(photo, mode):
        raise RuntimeError("tesseract not found")

    monkeypatch.setattr(app_module.pipeline, "run", boom)
    r = post()
    assert r.status_code == 500 and "tesseract not found" in r.json()["detail"]


def test_cors_allows_the_frontend_dev_server():
    r = client.options(
        "/translate",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"
