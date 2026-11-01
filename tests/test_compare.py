import pytest

from src.evalrunner.compare import compare


def run(vals, lang="en"):
    return {f"i{n}": {"id": f"i{n}", "lang": lang, "recall@1": v} for n, v in enumerate(vals)}


def test_detects_clear_difference_and_null():
    a, b = run([1.0] * 30 + [0.0] * 10), run([0.0] * 30 + [0.0] * 10)
    r = compare(a, b)["all"]
    assert r["n"] == 40 and r["diff"] > 0.7 and r["ci_excludes_0"]
    same = compare(a, a)["all"]
    assert same["diff"] == 0 and not same["ci_excludes_0"]


def test_small_noisy_difference_is_not_a_finding():
    a = run([1, 0, 1, 0, 1, 0, 0, 1])
    b = run([1, 0, 0, 0, 1, 1, 0, 1])
    assert not compare(a, b)["all"]["ci_excludes_0"]


def test_mismatched_items_rejected():
    with pytest.raises(ValueError):
        compare(run([1, 0]), run([1, 0, 1]))
