import copy
import hashlib
import json
from pathlib import Path

from src.evalrunner.validate_gold import validate_items


def make(tmp_path: Path):
    text = "Pension is paid monthly.\nApply at the block office."
    (tmp_path / "processed").mkdir()
    (tmp_path / "processed/d.txt").write_text(text, encoding="utf-8")
    psha = hashlib.sha256(text.encode()).hexdigest()
    manifest = {"d": {"source_id": "d", "text_path": "processed/d.txt", "parsed_sha256": psha, "sha256": "raw1"}}
    item = {"id": "q1", "lang": "en", "question": "Where do I apply?", "qtype": "factoid", "difficulty": "easy",
            "answer": "At the block office.", "answerable": True, "dataset_version": "0.0", "source_kind": "hand_written",
            "evidence": [{"doc_id": "d", "doc_sha256": "raw1", "parsed_sha256": psha, "parser_version": "p/1",
                          "char_start": 25, "char_end": 51, "quote": "Apply at the block office."}]}
    return item, manifest


def test_valid_item_passes(tmp_path):
    item, man = make(tmp_path)
    assert validate_items([item], man, tmp_path) == []


def test_quote_mismatch_and_range(tmp_path):
    item, man = make(tmp_path)
    bad = copy.deepcopy(item); bad["evidence"][0]["char_start"] = 24
    assert any("quote !=" in e for e in validate_items([bad], man, tmp_path))
    bad = copy.deepcopy(item); bad["evidence"][0]["char_end"] = 999
    assert any("out of range" in e for e in validate_items([bad], man, tmp_path))


def test_stale_pin_reports_reanchor(tmp_path):
    item, man = make(tmp_path)
    item["evidence"][0]["parsed_sha256"] = "old"
    errs = validate_items([item], man, tmp_path)
    assert any("stale evidence pin" in e and "found at 25" in e for e in errs)


def test_rules(tmp_path):
    item, man = make(tmp_path)
    dup = [item, copy.deepcopy(item)]
    assert any("duplicate id" in e for e in validate_items(dup, man, tmp_path))
    kn = copy.deepcopy(item); kn["id"] = "q2"; kn["lang"] = "kn"
    assert any("no authored-Kannada claim" in e for e in validate_items([kn], man, tmp_path))
    kn["source_kind"] = "aligned_parallel"
    assert any("needs aligned_with" in e for e in validate_items([kn], man, tmp_path))
    noev = copy.deepcopy(item); noev["id"] = "q3"; noev["evidence"] = []
    assert any("needs evidence" in e for e in validate_items([noev], man, tmp_path))
