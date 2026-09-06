"""
Shared embedding-model loader for the POC.

Single source of truth for which model both build_index.py and query.py use —
if they load different models, the vectors are in different spaces and
similarity search silently returns garbage. Keeping this in one place also
means swapping the model later (see the fallback note below) is a one-line
change, not a two-file edit that's easy to let drift.
"""

import os

# Primary choice per the architecture doc: bge-m3, multilingual, strong
# reported performance on low-resource languages relative to its size.
# Override with AMH_EMBED_MODEL=BAAI/bge-m3 to force it back on if the
# fallback below was needed on this machine.
DEFAULT_MODEL = "intfloat/multilingual-e5-base"
BGE_M3_MODEL = "BAAI/bge-m3"

MODEL_NAME = os.environ.get("AMH_EMBED_MODEL", DEFAULT_MODEL)

# e5 models were trained with an instruction prefix baked into the training
# data. Skipping it doesn't error — it just quietly returns worse rankings,
# which is a nasty thing to debug. bge-m3 needs no prefix at all.
_E5_PREFIXES = {"intfloat/multilingual-e5-base", "intfloat/multilingual-e5-large",
                "intfloat/multilingual-e5-small"}


def uses_e5_prefix(model_name: str = MODEL_NAME) -> bool:
    return model_name in _E5_PREFIXES


_model = None


def get_model():
    """Load once, reuse — the model load itself is the slow part (seconds to
    tens of seconds on CPU), not the embedding calls after it."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print(f"[embedder] loading {MODEL_NAME} (first run downloads it, be patient)...")
        _model = SentenceTransformer(MODEL_NAME)
        print(f"[embedder] loaded. embedding dim = {_model.get_embedding_dimension()}")
    return _model


def embed_passages(texts: list[str]):
    """Embed chunk text — the corpus side of a search."""
    model = get_model()
    if uses_e5_prefix():
        texts = [f"passage: {t}" for t in texts]
    return model.encode(texts, normalize_embeddings=True).tolist()


def embed_query(text: str):
    """Embed a search query. Kept as a separate function from embed_passages,
    not just a convenience wrapper: e5 uses a DIFFERENT prefix for queries
    than for passages ("query: " vs "passage: "), so query and passage
    embedding are genuinely different operations for that model family, and
    collapsing them into one function is how that distinction gets lost."""
    model = get_model()
    if uses_e5_prefix():
        text = f"query: {text}"
    return model.encode([text], normalize_embeddings=True).tolist()[0]
