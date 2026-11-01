"""Deterministic eligibility rule evaluation. Never guesses a missing attribute."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

OPS = {">=", "<=", ">", "<", "==", "!=", "in", "not_in", "between"}


@dataclass
class CriterionResult:
    attr: str
    op: str
    value: Any
    status: str          # met | not_met | unknown
    reason: str
    text: str = ""


def _cmp(op: str, have: Any, want: Any) -> bool:
    if op == "between":
        lo, hi = want
        return lo <= have <= hi
    if op == "in":
        return have in want
    if op == "not_in":
        return have not in want
    return {">=": have >= want, "<=": have <= want, ">": have > want, "<": have < want, "==": have == want, "!=": have != want}[op]


def _norm(v: Any) -> Any:
    return v.strip().lower() if isinstance(v, str) else v


def evaluate_criterion(c: dict, attributes: dict) -> CriterionResult:
    attr, op, want = c.get("attr", ""), c.get("op", ""), c.get("value")
    base = dict(attr=attr, op=op, value=want, text=c.get("text", ""))
    if op not in OPS:
        return CriterionResult(**base, status="unknown", reason=f"unsupported operator {op!r}")
    if attr not in attributes or attributes[attr] is None:
        return CriterionResult(**base, status="unknown", reason=f"attribute {attr!r} not provided")
    have = _norm(attributes[attr])
    if isinstance(want, list):
        want = [_norm(x) for x in want]
    else:
        want = _norm(want)
    try:
        if op in {"in", "not_in"} and not isinstance(want, list):
            return CriterionResult(**base, status="unknown", reason=f"{op} needs a list value")
        if op == "between" and not (isinstance(want, list) and len(want) == 2):
            return CriterionResult(**base, status="unknown", reason="between needs [low, high]")
        ok = _cmp(op, have, want)
    except TypeError:
        return CriterionResult(**base, status="unknown", reason=f"cannot compare {type(have).__name__} with {type(want).__name__}")
    return CriterionResult(**base, status="met" if ok else "not_met", reason=f"{have!r} {op} {want!r} is {ok}")


def evaluate_rules(criteria: list[dict], attributes: dict) -> dict:
    results = [evaluate_criterion(c, attributes) for c in criteria]
    if not results:
        overall = "unknown"
    elif any(r.status == "not_met" for r in results):
        overall = "not_eligible"
    elif all(r.status == "met" for r in results):
        overall = "eligible"
    else:
        overall = "unknown"
    return {"decision": overall, "criteria": [r.__dict__ for r in results],
            "missing_attributes": sorted({r.attr for r in results if r.status == "unknown" and "not provided" in r.reason})}
