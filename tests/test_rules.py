from src.agent.rules import evaluate_criterion, evaluate_rules

AGE = {"attr": "age", "op": "between", "value": [18, 50]}


def test_basic_ops_and_normalisation():
    assert evaluate_criterion(AGE, {"age": 30}).status == "met"
    assert evaluate_criterion(AGE, {"age": 51}).status == "not_met"
    assert evaluate_criterion({"attr": "state", "op": "in", "value": ["Karnataka", "Kerala"]}, {"state": " karnataka "}).status == "met"
    assert evaluate_criterion({"attr": "income", "op": "<=", "value": 100000}, {"income": 100000}).status == "met"
    assert evaluate_criterion({"attr": "owns_land", "op": "==", "value": True}, {"owns_land": False}).status == "not_met"


def test_missing_and_incomparable_are_unknown_not_guessed():
    r = evaluate_criterion(AGE, {})
    assert r.status == "unknown" and "not provided" in r.reason
    assert evaluate_criterion({"attr": "age", "op": ">=", "value": 18}, {"age": "thirty"}).status == "unknown"
    assert evaluate_criterion({"attr": "age", "op": "~", "value": 1}, {"age": 5}).status == "unknown"
    assert evaluate_criterion({"attr": "s", "op": "in", "value": "KA"}, {"s": "KA"}).status == "unknown"


def test_overall_decision_logic():
    crit = [AGE, {"attr": "income", "op": "<=", "value": 100000}]
    assert evaluate_rules(crit, {"age": 30, "income": 5})["decision"] == "eligible"
    assert evaluate_rules(crit, {"age": 60, "income": 5})["decision"] == "not_eligible"
    r = evaluate_rules(crit, {"age": 30})
    assert r["decision"] == "unknown" and r["missing_attributes"] == ["income"]
    assert evaluate_rules(crit, {"age": 60})["decision"] == "not_eligible"      # one failure decides even with unknowns
    assert evaluate_rules([], {"age": 3})["decision"] == "unknown"
