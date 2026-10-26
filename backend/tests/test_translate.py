"""The GPU -> CPU fallback in translate._open (ARCHITECTURE.md section 5), without loading a model."""
import pytest

from backend import translate


class FakeTranslator:
    def __init__(self, path, device, compute_type):
        if device == "cuda":
            raise RuntimeError("CUDA failed with error out of memory")
        self.device = device

    def translate_batch(self, batch, **kwargs):
        return []


class GpuFailsOnFirstUse(FakeTranslator):
    """What happened on 26 Oct: the model loads on the GPU, then cuBLAS is missing at first translation."""

    def __init__(self, path, device, compute_type):
        self.device = device

    def translate_batch(self, batch, **kwargs):
        if self.device == "cuda":
            raise RuntimeError("Library cublas64_12.dll is not found or cannot be loaded")
        return []


def test_falls_back_to_cpu_when_the_gpu_fails_to_load(monkeypatch):
    monkeypatch.setattr(translate.ctranslate2, "Translator", FakeTranslator)
    assert translate._open("cuda").device == "cpu"


def test_falls_back_to_cpu_when_the_gpu_fails_on_first_use(monkeypatch):
    monkeypatch.setattr(translate.ctranslate2, "Translator", GpuFailsOnFirstUse)
    assert translate._open("cuda").device == "cpu"


def test_forced_cpu_failure_is_not_swallowed(monkeypatch):
    def broken(path, device, compute_type):
        raise RuntimeError("model files missing")

    monkeypatch.setattr(translate.ctranslate2, "Translator", broken)
    with pytest.raises(RuntimeError, match="model files missing"):
        translate._open("cpu")


def test_empty_input_needs_no_model():
    assert translate.translate([]) == []
