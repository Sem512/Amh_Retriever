"""Does merging same-sound letters before translation improve the English?

Run from the repo root:  python -m backend.letter_merging_experiment <private test-photos folder>
Each answer-key block that has an English reference is read, translated as read and after fold_homophones, and scored
with chrF against the reference. The pipeline never calls fold_homophones; it joins the pipeline only if the merged
score is at least 1 chrF point higher (ARCHITECTURE.md section 3).
"""
import json
import re
import sys
from pathlib import Path

import cv2
import numpy as np

from backend.translate import translate
from ocr.normalize import fold_homophones, normalize
from ocr.reader import read_page
from ocr.scoring import chrf

ADOPT_MARGIN = 1.0


def sentences(text):
    """Stands in for to_sentences(): drop list bullets, split after ። ፧ ? !"""
    return [s.strip() for s in re.split(r"(?<=[።፧?!])", text.replace("•", " ")) if s.strip()]


def english(amharic):
    return " ".join(translate(sentences(amharic)))


def main(folder):
    folder = Path(folder)
    blocks = [b for b in json.loads((folder / "ground_truth_printed.json").read_text(encoding="utf-8")) if b["english"]]
    refs = [b["english"] for b in blocks]
    read = []
    for b in blocks:
        img = cv2.imdecode(np.fromfile(folder / b["file"], np.uint8), cv2.IMREAD_COLOR)
        read.append(" ".join(line["text"] for line in read_page(img)))
    variants = {
        "as read": [english(t) for t in read],
        "letters merged": [english(fold_homophones(t)) for t in read],
        "answer key (upper bound)": [english(normalize(" ".join(b["amharic"].splitlines()))) for b in blocks],
    }
    print(f"{'block':12} " + " ".join(f"{name:>25}" for name in variants))
    for i, b in enumerate(blocks):
        print(f"{b['id']:12} " + " ".join(f"{chrf([hyps[i]], [refs[i]]):>25.1f}" for hyps in variants.values()))
    scores = {name: chrf(hyps, refs) for name, hyps in variants.items()}
    print(f"{'ALL ' + str(len(blocks)):12} " + " ".join(f"{s:>25.1f}" for s in scores.values()))
    gain = scores["letters merged"] - scores["as read"]
    print(f"\nmerging changes chrF by {gain:+.1f} points on {len(blocks)} blocks: " + ("ADOPT" if gain >= ADOPT_MARGIN else "keep it out of the pipeline"))


if __name__ == "__main__":
    main(sys.argv[1])
