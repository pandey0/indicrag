import csv
import json


def write_drafts(drafts: dict, sheet: str, out: str, prefix: str) -> None:
    """drafts: sheet_id -> (question, qtype, difficulty, answer). Items are UNREVIEWED LLM drafts."""
    rows = {r["id"]: r for r in csv.DictReader(open(sheet, encoding="utf-8"))}
    with open(out, "w", encoding="utf-8") as f:
        for iid, (q, qtype, diff, ans) in drafts.items():
            r = rows[iid]
            f.write(json.dumps({
                "id": f"{prefix}-{iid.replace('pilot-', '')}", "lang": r["lang"], "register": "formal", "question": q, "qtype": qtype,
                "difficulty": diff, "answer": ans, "answerable": True, "valid_as_of": "2026-11-01", "writer": "claude-draft",
                "review_status": "unreviewed", "dataset_version": "0.0-draft", "source_kind": "llm_drafted_validated",
                "notes": "DRAFT: LLM-written, not human validated; source is Wikipedia fallback corpus (CC BY-SA 4.0)",
                "evidence": [{"doc_id": r["doc_id"], "doc_sha256": r["doc_sha256"], "parsed_sha256": r["parsed_sha256"],
                              "parser_version": r["parser_version"], "char_start": int(r["char_start"]), "char_end": int(r["char_end"]),
                              "quote": r["quote"]}]}, ensure_ascii=False) + "\n")
    print(len(drafts), "drafts ->", out)
