"""What would a confidence cut-off do on the real photos?

Run from the repo root:  python -m ocr.confidence_cutoffs <private test-photos folder>
For each cut-off it drops the lines the engine is less sure of than that, then reports the character error rate on
the answer-key blocks and how many lines are lost on each kind of photo. Nothing here changes read_page.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

import ocr.reader as reader
from ocr.normalize import normalize
from ocr.scoring import cer

CUTOFFS = (0, 10, 20, 30, 40, 50, 60, 70, 80)


def lines_of(path):
    return reader._read_lines(cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR))


def main(folder):
    folder = Path(folder)
    blocks = json.loads((folder / "ground_truth_printed.json").read_text(encoding="utf-8"))
    truth = {b["id"]: normalize(" ".join(b["amharic"].splitlines())) for b in blocks}
    block_lines = {b["id"]: lines_of(folder / b["file"]) for b in blocks}
    others = {kind: [l["confidence"] for p in sorted((folder / kind).glob("*.*")) if p.suffix.lower() in (".png", ".jpg", ".jpeg") for l in lines_of(p)]
              for kind in ("handwritten", "scene", "printed_scan")}
    total_block_lines = sum(map(len, block_lines.values()))
    print(f"lines found: answer-key blocks {total_block_lines}, " + ", ".join(f"{k} {len(v)}" for k, v in others.items()))
    print(f"\n{'cut-off':>7} {'blocks CER':>11} {'blocks lost':>12} " + " ".join(f"{k + ' lost':>17}" for k in others))
    for cut in CUTOFFS:
        kept = {i: [l["text"] for l in ls if l["confidence"] >= cut] for i, ls in block_lines.items()}
        mean = sum(cer(truth[i], " ".join(kept[i])) for i in truth) / len(truth)
        lost = total_block_lines - sum(map(len, kept.values()))
        print(f"{cut:>7} {mean:>11.1%} {lost:>12} " + " ".join(f"{sum(c < cut for c in v):>17}" for v in others.values()))


if __name__ == "__main__":
    main(sys.argv[1])
