"""Interactive review of LLM-drafted items. Run in a terminal:  python3 scripts/review_drafts.py data/gold/drafts/*.jsonl --reviewer <name>

For each unreviewed item you see the source quote, question and answer. Keys:
  a = agree (answer is supported by the quote, question is natural)    r = reject
  e = edit question and/or answer, then agree (status 'revised')       s = skip for now      q = quit (progress is saved)
Agreed/revised items are appended to data/gold/dev.jsonl (validated first); rejected ones go to data/gold/rejected.jsonl.
Reviewed item ids are remembered in data/gold/.reviewed so re-runs resume where you stopped.
Hindi/English reviewers only for those languages; Kannada items need a native Kannada reviewer (native_verified stays false here).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from src.evalrunner.validate_gold import load_manifest, validate_items  # noqa: E402

GOLD = Path("data/gold")


def review(items: list[dict], reviewer: str, ask=input, out=print, manifest="data/corpus_manifest.csv", data_dir="data",
           gold_dir: Path = GOLD) -> dict:
    gold_dir.mkdir(parents=True, exist_ok=True)
    done_file = gold_dir / ".reviewed"
    done = set(done_file.read_text().split()) if done_file.exists() else set()
    man = load_manifest(Path(manifest))
    stats = {"agreed": 0, "revised": 0, "rejected": 0, "skipped": 0}
    todo = [i for i in items if i["id"] not in done and i.get("review_status") == "unreviewed"]
    for n, it in enumerate(todo, 1):
        if it["lang"] == "kn":
            out(f"skip {it['id']}: Kannada needs a native reviewer")
            stats["skipped"] += 1
            continue
        out(f"\n--- {n}/{len(todo)}  {it['id']}  [{it['lang']}, {it['qtype']}, {it['difficulty']}]")
        out("QUOTE:    " + (it["evidence"][0]["quote"][:900] if it["evidence"] else "(none: must be UNANSWERABLE from the corpus) " + it.get("notes", "")))
        out("QUESTION: " + it["question"])
        out("ANSWER:   " + it["answer"])
        while True:
            try:
                k = ask("[a]gree [r]eject [e]dit [s]kip [q]uit > ").strip().lower()
            except EOFError:
                out("no interactive input available (stdin closed): use --list / --decide for the non-interactive flow")
                k = "q"
            if k in {"a", "r", "e", "s", "q"}:
                break
        if k == "q":
            break
        if k == "s":
            stats["skipped"] += 1
            continue
        if k == "r":
            with open(gold_dir / "rejected.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({**it, "review_status": "rejected", "reviewer": reviewer}, ensure_ascii=False) + "\n")
            stats["rejected"] += 1
        else:
            new = dict(it)
            if k == "e":
                q = ask("new question (blank = keep) > ").strip()
                a = ask("new answer   (blank = keep) > ").strip()
                new["question"], new["answer"] = q or it["question"], a or it["answer"]
            new.update(review_status="revised" if k == "e" else "agreed", reviewer=reviewer, source_kind="llm_drafted_validated",
                       dataset_version="0.1-dev")
            new["notes"] = (new.get("notes", "").replace("DRAFT: LLM-written, not human validated; ", "")).strip()
            errs = validate_items([new], man, Path(data_dir), check_answer_numbers=True)
            if errs:
                out("NOT SAVED, validator says: " + "; ".join(errs))
                continue
            with open(gold_dir / "dev.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(new, ensure_ascii=False) + "\n")
            stats["revised" if k == "e" else "agreed"] += 1
        with open(done_file, "a") as f:
            f.write(it["id"] + "\n")
    out(f"\nsummary: {stats}")
    return stats


def pending(items: list[dict], gold_dir: Path = GOLD) -> list[dict]:
    done_file = gold_dir / ".reviewed"
    done = set(done_file.read_text().split()) if done_file.exists() else set()
    return [i for i in items if i["id"] not in done and i.get("review_status") == "unreviewed" and i["lang"] != "kn"]


def parse_decisions(spec: str) -> dict[str, tuple[str, str, str]]:
    """'id=a, id=r, id=s, id=e:new question::new answer' (comma/newline separated; edit text may not contain a comma-then-id)."""
    import re

    out = {}
    # split on newlines or on a comma that is followed by "<id>=" so edit text may itself contain commas
    for part in [p.strip() for p in re.split(r"\n|,\s*(?=[\w-]+=)", spec) if p.strip()]:
        iid, _, rest = part.partition("=")
        if rest[:1] == "e" and ":" in rest:
            q, _, a = rest[2:].partition("::")
            out[iid.strip()] = ("e", q.strip(), a.strip())
        elif rest[:1] in {"a", "r", "s"}:
            out[iid.strip()] = (rest[:1], "", "")
        else:
            raise ValueError(f"bad decision {part!r}")
    return out


def apply_decisions(items: list[dict], decisions: dict, reviewer: str, **kw) -> dict:
    """Run the same review() logic non-interactively: only items named in decisions are touched."""
    todo = [i for i in pending(items, kw.get("gold_dir", GOLD)) if i["id"] in decisions]
    unknown = set(decisions) - {i["id"] for i in todo}
    if unknown:
        raise ValueError(f"not pending/unknown ids: {sorted(unknown)}")
    script: list[str] = []
    for i in todo:
        k, q, a = decisions[i["id"]]
        script += [k] + ([q, a] if k == "e" else [])
    it = iter(script)
    return review(todo, reviewer, ask=lambda _: next(it), **kw)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--reviewer", default="")
    ap.add_argument("--list", type=int, metavar="N", help="print the next N pending items compactly and exit")
    ap.add_argument("--decide", help="decisions 'id=a,id=r,id=e:new q::new a,id=s' applied non-interactively")
    a = ap.parse_args()
    items = [json.loads(line) for f in a.files for line in open(f, encoding="utf-8") if line.strip()]
    if a.list:
        for i in pending(items)[: a.list]:
            print(f"{i['id']} [{i['lang']},{i['qtype']}]\n  QUOTE: {i['evidence'][0]['quote'][:420] if i['evidence'] else '(none: should be UNANSWERABLE) ' + i.get('notes', '')}\n  Q: {i['question']}\n  A: {i['answer']}\n")
        print(f"({len(pending(items))} pending)")
        return
    if not a.reviewer:
        ap.error("--reviewer is required")
    if a.decide:
        apply_decisions(items, parse_decisions(a.decide), a.reviewer)
        return
    review(items, a.reviewer)


if __name__ == "__main__":
    main()
