"""uvicorn src.api.main:app  (env: RETRIEVER=bm25|hybrid, CHUNKS, ANTHROPIC_API_KEY, ANTHROPIC_MODEL, DEMO_* limits).

Without ANTHROPIC_API_KEY the app runs retrieval-only (budget treated as exhausted): no model is called.
"""
from __future__ import annotations

import os

from src.evalrunner.run_retrieval import build_retriever, load_chunks

from .app import create_app, load_docs
from .guards import Settings


def build():
    chunks_path = os.environ.get("CHUNKS", "data/chunks/fixed_512_64.jsonl")
    chunks = load_chunks(chunks_path)
    retriever = build_retriever(os.environ.get("RETRIEVER", "bm25"), chunks, os.environ.get("EMBED_MODEL", "intfloat/multilingual-e5-small"), chunks_path)
    docs = load_docs(os.environ.get("MANIFEST", "data/corpus_manifest.csv"))
    st = Settings.from_env()
    if os.environ.get("ANTHROPIC_API_KEY"):
        from src.generate.provider import AnthropicProvider
        provider = AnthropicProvider()
    else:
        st.daily_budget_usd = 0.0     # retrieval-only mode
        from src.generate.provider import EchoProvider
        provider = EchoProvider(lambda s, u: "NO_ANSWER")
    return create_app(retriever, chunks, provider, docs, st)


app = build()
