"""Compare the two OCR models on the ground-truthed printed blocks.

Run from the repo root:  python -m ocr.compare_models <private test-photos folder>
The folder holds ground_truth_printed.json and the block images (they never go in the repo).
Both the OCR text and the answer key go through normalize() before scoring.
"""
import importlib
import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np

import ocr.reader as reader
from ocr.normalize import normalize
from ocr.scoring import cer

MODELS = ("amh", "Ethiopic", "amh+Ethiopic")  # the last runs both models together


def read_all(folder, blocks, model):
    os.environ["OCR_LANG"] = model
    importlib.reload(reader)  # the reader loads its model once, so reload to switch
    out = {}
    for b in blocks:
        image = cv2.imdecode(np.fromfile(folder / b["file"], np.uint8), cv2.IMREAD_COLOR)
        out[b["id"]] = " ".join(line["text"] for line in reader.read_page(image))
    return out


def main(folder):
    folder = Path(folder)
    blocks = json.loads((folder / "ground_truth_printed.json").read_text(encoding="utf-8"))
    truth = {b["id"]: normalize(" ".join(b["amharic"].splitlines())) for b in blocks}
    reads = {m: read_all(folder, blocks, m) for m in MODELS}
    scores = {m: {i: cer(truth[i], reads[m][i]) for i in truth} for m in MODELS}

    print(f"{'block':18} {'chars':>6} " + " ".join(f"{m + ' CER':>17}" for m in MODELS))
    for i in truth:
        print(f"{i:18} {len(truth[i]):>6} " + " ".join(f"{scores[m][i]:>17.1%}" for m in MODELS))
    print(f"{'MEAN':18} {'':>6} " + " ".join(f"{sum(scores[m].values()) / len(truth):>17.1%}" for m in MODELS))
    wins = {m: sum(scores[m][i] < min(scores[o][i] for o in MODELS if o != m) for i in truth) for m in MODELS}
    print(f"\n{len(truth)} blocks. Blocks won outright (lowest CER): " + ", ".join(f"{m} {wins[m]}" for m in MODELS))


if __name__ == "__main__":
    main(sys.argv[1])
