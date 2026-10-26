"""Amharic -> English with NLLB-200-distilled-600M (CTranslate2, int8).

Runs on the GPU when it can and falls back to the CPU at load time (ARCHITECTURE.md section 5).
TRANSLATE_DEVICE=cpu forces the CPU.
"""
import logging
import os
import sys
from pathlib import Path

if sys.platform == "win32":
    # cuBLAS comes from the nvidia-cublas-cu12 wheel; CTranslate2 loads it via the plain PATH search
    cublas = Path(sys.prefix) / "Lib" / "site-packages" / "nvidia" / "cublas" / "bin"
    if cublas.is_dir():
        os.environ["PATH"] = f"{cublas}{os.pathsep}{os.environ['PATH']}"

import ctranslate2
import transformers

MODEL_DIR = Path(__file__).resolve().parent.parent / "models" / "nllb-200-distilled-600M-ct2-int8"
_translator = _tokenizer = None


def _open(device):
    try:
        translator = ctranslate2.Translator(str(MODEL_DIR), device=device, compute_type="int8")
        # cuBLAS loads on first use, so test it now rather than failing inside a user's request
        translator.translate_batch([["▁"]], max_decoding_length=1)
        return translator
    except (RuntimeError, ValueError) as e:  # no CUDA libraries, no GPU, or not enough GPU memory
        if device == "cpu":
            raise
        logging.warning("GPU unavailable (%s); translating on the CPU instead", e)
        return ctranslate2.Translator(str(MODEL_DIR), device="cpu", compute_type="int8")


def translate(sentences):
    """Amharic sentences -> English sentences, same order."""
    global _translator, _tokenizer
    if not sentences:
        return []
    if _translator is None:
        _translator = _open(os.environ.get("TRANSLATE_DEVICE", "cuda"))
        # its "incorrect regex pattern" warning is Mistral-specific: tokens match SentencePiece for stripped text (checked 26 Oct)
        _tokenizer = transformers.AutoTokenizer.from_pretrained(str(MODEL_DIR), src_lang="amh_Ethi")
    batch = [_tokenizer.convert_ids_to_tokens(_tokenizer.encode(s.strip())) for s in sentences]
    results = _translator.translate_batch(batch, target_prefix=[["eng_Latn"]] * len(batch))
    # hypotheses[0][0] is the eng_Latn language tag the decoder was primed with
    return [_tokenizer.decode(_tokenizer.convert_tokens_to_ids(r.hypotheses[0][1:])) for r in results]
