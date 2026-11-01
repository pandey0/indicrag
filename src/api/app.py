"""FastAPI reference app (docs/15). Not a production service: no auth, no HA."""
from __future__ import annotations

import csv
import json
import logging
import uuid
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from src.generate.answer import Answer, answer_question, build_context, detect_lang
from src.security.pii import scrub

from .guards import Budget, RateLimiter, Settings, client_key

log = logging.getLogger("api")
DISCLAIMER = ("Information from public documents, may be out of date or incomplete. Not legal or financial advice. "
              "Verify on the official government website or office. Do not enter Aadhaar, phone, PAN or bank details.")


class AskRequest(BaseModel):
    question: str = Field(min_length=3)
    k: int = 5


class FeedbackRequest(BaseModel):
    question: str = ""
    rating: int = Field(ge=-1, le=1)
    reason: str = Field(default="", max_length=300)


def load_docs(manifest: str | Path) -> dict[str, dict]:
    with open(manifest, encoding="utf-8") as f:
        return {r["source_id"]: r for r in csv.DictReader(f) if r["parse_status"] in ("ok", "ocr_ok")}


def create_app(retriever, chunks: dict[str, dict], provider, docs: dict[str, dict], settings: Settings | None = None,
               valid_as_of: str | None = None, clock=None) -> FastAPI:
    st = settings or Settings.from_env()
    limiter = RateLimiter(st.per_minute, st.per_day, **({"clock": clock} if clock else {}))
    budget = Budget(st.daily_budget_usd)
    app = FastAPI(title="IndicRAG reference API", version="0.1.0")
    feedback_store: list[dict] = []
    app.state.feedback = feedback_store
    app.state.budget = budget

    def source_view(a: Answer) -> list[dict]:
        out = []
        for s in a.sources:
            d = docs.get(s.doc_id, {})
            item = {"id": s.cid, "doc_id": s.doc_id, "title": d.get("title", ""), "url": d.get("url", ""),
                    "fetched_at": d.get("fetched_at", ""), "cited": s.cid in a.cited}
            if d.get("redistribute") == "true":          # excerpts only where the licence verdict allows it
                item["excerpt"] = s.text[:300]
            out.append(item)
        return out

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    @app.get("/readyz")
    def readyz():
        ready = bool(chunks) and bool(docs)
        if not ready:
            raise HTTPException(503, "index not loaded")
        return {"ready": True, "chunks": len(chunks), "docs": len(docs)}

    @app.post("/ask")
    def ask(req: AskRequest, request: Request):
        rid = uuid.uuid4().hex[:12]
        if not st.enabled:
            raise HTTPException(503, "demo disabled")
        if len(req.question) > st.max_question_chars:
            raise HTTPException(422, f"question longer than {st.max_question_chars} characters")
        key = client_key(request.client.host if request.client else "unknown", st.salt)
        if not limiter.allow(key):
            raise HTTPException(429, "rate limit exceeded")
        k = max(1, min(req.k, st.max_k))
        clean_q, kinds = scrub(req.question)
        log.info(json.dumps({"rid": rid, "q": clean_q, "pii": kinds, "k": k}, ensure_ascii=False))   # scrubbed text only
        lang = detect_lang(req.question)
        base = {"request_id": rid, "valid_as_of": valid_as_of or date.today().isoformat(), "disclaimer": DISCLAIMER,
                "pii_detected": bool(kinds)}
        if kinds:
            return {**base, "answer": None, "refused": True, "reason": "pii_in_question", "lang": lang, "sources": [],
                    "note": "Your question seems to contain personal details; please remove them and ask again."}
        if budget.exhausted:     # degrade to retrieval-only: no LLM call
            hits = retriever.search(req.question, k)
            _, srcs = build_context([(h.chunk_id, chunks[h.chunk_id]["doc_id"], chunks[h.chunk_id]["text"]) for h in hits])
            view = source_view(Answer("", lang, True, "budget_exhausted", srcs))
            return {**base, "answer": None, "refused": True, "reason": "budget_exhausted", "lang": lang, "sources": view,
                    "note": "Generation is paused; showing the most relevant documents only."}
        a = answer_question(req.question, retriever, chunks, provider, k)
        if a.completion:
            budget.add(a.completion.input_tokens, a.completion.output_tokens)
        return {**base, "answer": a.text, "refused": a.refused, "reason": a.reason, "lang": a.lang, "cited": a.cited,
                "sources": source_view(a), "prompt_hash": a.prompt_hash}

    @app.post("/feedback")
    def feedback(fb: FeedbackRequest):
        q, kinds = scrub(fb.question)
        r, _ = scrub(fb.reason)
        feedback_store.append({"question": q, "rating": fb.rating, "reason": r, "pii_scrubbed": bool(kinds)})
        return {"stored": True}

    @app.get("/docs/{doc_id}")
    def get_doc(doc_id: str):
        d = docs.get(doc_id)
        if not d:
            raise HTTPException(404, "unknown document")
        return {"doc_id": doc_id, "title": d["title"], "url": d["url"], "lang": d["lang"], "publisher": d["publisher"],
                "fetched_at": d["fetched_at"], "licence_verdict": d["licence_verdict"], "redistribute": d["redistribute"] == "true"}

    return app
