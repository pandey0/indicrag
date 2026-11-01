import json
import sys

sys.path.insert(0, "scripts")
from review_drafts import review  # noqa: E402


def setup(tmp_path):
    text = "Pension is paid monthly.\nApply at the block office."
    (tmp_path / "processed").mkdir(exist_ok=True)
    (tmp_path / "processed/d.txt").write_text(text, encoding="utf-8")
    import hashlib
    psha = hashlib.sha256(text.encode()).hexdigest()
    man = tmp_path / "manifest.csv"
    man.write_text("source_id,text_path,parsed_sha256,sha256\nd,processed/d.txt," + psha + ",raw1\n", encoding="utf-8")
    base = {"lang": "en", "question": "Where do I apply?", "qtype": "factoid", "difficulty": "easy", "answer": "At the block office.",
            "answerable": True, "dataset_version": "0.0-draft", "source_kind": "llm_drafted_validated", "review_status": "unreviewed",
            "notes": "DRAFT: LLM-written, not human validated; src",
            "evidence": [{"doc_id": "d", "doc_sha256": "raw1", "parsed_sha256": psha, "parser_version": "p/1", "char_start": 25, "char_end": 51,
                          "quote": "Apply at the block office."}]}
    items = [{**base, "id": f"q{i}"} for i in range(1, 5)]
    items[3]["lang"] = "kn"
    return items, man


def run(tmp_path, answers):
    items, man = setup(tmp_path)
    it = iter(answers)
    gold = tmp_path / "gold"
    stats = review(items, "tester", ask=lambda _: next(it), out=lambda *_: None, manifest=str(man), data_dir=str(tmp_path), gold_dir=gold)
    return stats, gold


def test_agree_edit_reject_and_kannada_skipped(tmp_path):
    stats, gold = run(tmp_path, ["a", "e", "Where should I apply?", "At the block office.", "r"])
    assert stats == {"agreed": 1, "revised": 1, "rejected": 1, "skipped": 1}
    dev = [json.loads(line) for line in open(gold / "dev.jsonl", encoding="utf-8")]
    assert [d["review_status"] for d in dev] == ["agreed", "revised"] and dev[1]["question"] == "Where should I apply?"
    assert all(d["reviewer"] == "tester" and "DRAFT" not in d["notes"] for d in dev)
    assert (gold / "rejected.jsonl").exists()


def test_resume_skips_done_and_quit_saves(tmp_path):
    stats, gold = run(tmp_path, ["a", "q"])
    assert stats["agreed"] == 1
    items, man = setup(tmp_path)
    again = review(items, "t", ask=lambda _: "a", out=lambda *_: None, manifest=str(man), data_dir=str(tmp_path), gold_dir=gold)
    assert again["agreed"] == 2          # q1 was already reviewed; q2, q3 agreed now; kn skipped
    assert len((gold / "dev.jsonl").read_text(encoding="utf-8").splitlines()) == 3


def test_invalid_edit_not_saved(tmp_path):
    stats, gold = run(tmp_path, ["e", "Q?", "Within 99 days.", "s", "s"])
    assert stats["revised"] == 0 and not (gold / "dev.jsonl").exists()      # answer number 99 not in quote -> validator blocks


def test_batch_decisions_non_interactive(tmp_path):
    from review_drafts import apply_decisions, parse_decisions
    items, man = setup(tmp_path)
    d = parse_decisions("q1=a, q2=e:Where should I apply?::At the block office., q3=r")
    assert d["q2"] == ("e", "Where should I apply?", "At the block office.")
    stats = apply_decisions(items, d, "t", out=lambda *_: None, manifest=str(man), data_dir=str(tmp_path), gold_dir=tmp_path / "g")
    assert stats["agreed"] == 1 and stats["revised"] == 1 and stats["rejected"] == 1
    try:
        apply_decisions(items, parse_decisions("q1=a"), "t", out=lambda *_: None, manifest=str(man), data_dir=str(tmp_path), gold_dir=tmp_path / "g")
        raise AssertionError("expected not-pending error")
    except ValueError as e:
        assert "not pending" in str(e)
