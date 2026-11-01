"""End-to-end generation evaluation with deterministic scoring (no judge model), docs/05.

Modes: `rag` (retrieve -> answer_question with citation validation), `closed_book` (same model, no passages) and `long_doc`
(ORACLE: the whole parsed gold document is placed in context, so retrieval cannot fail; an upper bound on what better retrieval could
add, not a deployable system. The whole corpus (~1M tokens) does not fit in context, so a true long-context baseline is not run.
Unanswerable items have no gold document and are skipped in this mode).
Per answerable item: number_recall = share of the gold answer's numbers (Indic digits normalised) present in the model answer
(a weak but objective correctness proxy: items whose gold answer has no numbers are scored separately as n/a), cited_gold =
a cited chunk hits the gold span, refused. Per unanswerable item: abstained (rag only). A judge-based faithfulness/correctness
score is NOT computed here: the only judge available would be the same model family as the generator, which docs/05 forbids.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from src.generate.answer import answer_question, detect_lang
from src.generate.provider import LLMProvider

from .align import numbers
from .metrics import ChunkRef, relevance

CLOSED_SYSTEM = ("Answer the question about Indian government services briefly and concretely, in the language of the question. "
                 "If you are not sure, say you are not sure instead of guessing.")


LONG_SYSTEM = ("Answer the question using ONLY the document below, briefly and concretely, in the language of the question. "
               "If the document does not contain the answer, reply exactly NO_ANSWER.\n\nDOCUMENT:\n")
MAX_DOC_CHARS = 150_000


def gold_doc_text(it: dict, root: str = "data/processed") -> str | None:
    """Parsed text of the first gold evidence document (matched by parsed_sha256), capped; None if unavailable."""
    from pathlib import Path

    ev = (it.get("evidence") or [None])[0]
    if not ev:
        return None
    f = Path(root, ev["doc_id"], f"{ev['parsed_sha256']}.txt")
    return f.read_text(encoding="utf-8")[:MAX_DOC_CHARS] if f.exists() else None


@dataclass
class GenRow:
    id: str
    lang: str
    mode: str
    answerable: bool
    refused: bool
    number_recall: float | None     # None when the gold answer has no numbers (or unanswerable)
    cited_gold: bool | None         # rag only, answerable only
    in_tokens: int
    out_tokens: int


def run_generation(items: list[dict], retriever, chunks: dict[str, dict], provider: LLMProvider, mode: str = "rag", k: int = 5) -> list[GenRow]:
    rows = []
    for it in items:
        answerable = bool(it.get("evidence")) and it.get("answerable", True) is not False
        if mode == "rag":
            a = answer_question(it["question"], retriever, chunks, provider, k)
            text, refused = a.text, a.refused
            tin, tout = (a.completion.input_tokens, a.completion.output_tokens) if a.completion else (0, 0)
            cited_gold = None
            if answerable:
                by_cid = {s.cid: s.chunk_id for s in a.sources}
                ranked = [ChunkRef(by_cid[c], chunks[by_cid[c]]["doc_id"], chunks[by_cid[c]]["parsed_sha256"], chunks[by_cid[c]]["char_start"],
                                   chunks[by_cid[c]]["char_end"]) for c in a.cited if c in by_cid]
                cited_gold = any(relevance(ranked, it["evidence"])) if ranked else False
        elif mode == "long_doc":
            doc = gold_doc_text(it)
            if doc is None:
                continue
            comp = provider.complete(LONG_SYSTEM + doc, it["question"], 300)
            text, refused, tin, tout, cited_gold = comp.text, "NO_ANSWER" in comp.text, comp.input_tokens, comp.output_tokens, None
        else:
            comp = provider.complete(CLOSED_SYSTEM, it["question"], 300)
            text, refused, tin, tout, cited_gold = comp.text, False, comp.input_tokens, comp.output_tokens, None
        nr = None
        if answerable and not refused:
            gold = numbers(it["answer"])
            nr = len(gold & numbers(text)) / len(gold) if gold else None
        elif answerable and refused:
            nr = 0.0 if numbers(it["answer"]) else None
        rows.append(GenRow(it["id"], it["lang"], mode, answerable, refused, nr, cited_gold, tin, tout))
    return rows


def summarize(rows: list[GenRow]) -> dict:
    def mean(xs):
        xs = [x for x in xs if x is not None]
        return round(sum(xs) / len(xs), 3) if xs else None

    out = {}
    for lang in sorted({r.lang for r in rows}) + ["all"]:
        rs = [r for r in rows if lang == "all" or r.lang == lang]
        ans = [r for r in rs if r.answerable]
        un = [r for r in rs if not r.answerable]
        out[lang] = {"n_answerable": len(ans), "number_recall": mean([r.number_recall for r in ans]),
                     "n_with_numbers": sum(r.number_recall is not None for r in ans), "refusal_rate_answerable": mean([r.refused for r in ans]),
                     "cited_gold_rate": mean([r.cited_gold for r in ans]), "n_unanswerable": len(un),
                     "abstention_unanswerable": mean([r.refused for r in un]) if un and all(r.mode == "rag" for r in un) else None,  # closed-book has no refusal mechanism: n/a, not 0
                     "tokens_in": sum(r.in_tokens for r in rs), "tokens_out": sum(r.out_tokens for r in rs)}
    return out


def main() -> None:
    import argparse

    from src.evalrunner.run_retrieval import build_retriever, load_chunks
    from src.generate.provider import AnthropicProvider

    ap = argparse.ArgumentParser(description="Needs ANTHROPIC_API_KEY; spends API budget (one call per item per mode).")
    ap.add_argument("--gold", default="data/gold/dev.jsonl")
    ap.add_argument("--chunks", default="data/chunks/fixed_512_64.jsonl")
    ap.add_argument("--retriever", default="bm25")
    ap.add_argument("--model", default="intfloat/multilingual-e5-small")
    ap.add_argument("--modes", nargs="+", default=["rag", "closed_book"])
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    chunks = load_chunks(a.chunks)
    retr = build_retriever(a.retriever, chunks, a.model, a.chunks)
    items = [json.loads(line) for line in open(a.gold, encoding="utf-8") if line.strip()]
    prov = AnthropicProvider()
    res = {}
    for mode in a.modes:
        rows = run_generation(items, retr, chunks, prov, mode)
        res[mode] = {"summary": summarize(rows), "rows": [r.__dict__ for r in rows]}
        print(mode, json.dumps(res[mode]["summary"]["all"]))
    if a.out:
        json.dump(res, open(a.out, "w", encoding="utf-8"), ensure_ascii=False)
    _ = detect_lang


if __name__ == "__main__":
    main()
