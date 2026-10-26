"""HTTP layer: POST /translate. Validates the upload, runs the pipeline, shapes the response.

Contract: ARCHITECTURE.md section 4. Run from the repo root: uvicorn backend.app:app
"""
import base64
import time
from typing import Literal

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend import pipeline

MAX_BYTES = 10 * 1024 * 1024
JPEG_MAGIC, PNG_MAGIC = b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n"

app = FastAPI(title="Amharic image translator")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["POST"], allow_headers=["*"])


@app.post("/translate")
async def translate(
    file: UploadFile = File(...),
    mode: Literal["document", "sign", "handwriting"] = Form("document"),
):
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "The image is larger than 10 MB.")
    photo = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR) if data.startswith((JPEG_MAGIC, PNG_MAGIC)) else None
    if photo is None:
        raise HTTPException(400, "The file is not a readable JPG or PNG image.")

    started = time.perf_counter()
    try:
        image, segments = pipeline.run(photo, mode)
        ok, png = cv2.imencode(".png", image)
        if not ok:
            raise RuntimeError("could not encode the result image")
    except Exception as e:  # any engine failure becomes the contract's 500 {detail}
        raise HTTPException(500, f"Processing failed: {e}") from e

    h, w = image.shape[:2]
    return {
        "mode": mode,
        "took_ms": round((time.perf_counter() - started) * 1000),
        "image": {"data_url": "data:image/png;base64," + base64.b64encode(png).decode(), "width": w, "height": h},
        "segments": [
            {
                "id": i,
                "amharic": s["amharic"],
                "english": s["english"],
                "bboxes": [{"x": left / w, "y": top / h, "w": bw / w, "h": bh / h} for left, top, bw, bh in s["boxes"]],
            }
            for i, s in enumerate(segments)
        ],
    }
