from app.models.extraction import ValidationStatus
from app.processors.contract_validator import detect_inconsistent, resolve


def tx(invoice, contract, nit="900"):
    return {"invoice": invoice, "nit_provider": nit, "contract": contract}


def test_detects_only_units_outside_valid_contracts():
    observed = detect_inconsistent([tx("F1", "CNT-1"), tx("F2", "CNT-9")], ["cnt-1"])
    assert list(observed) == [("F2", "900")]


def test_corrects_when_fpr_has_exactly_one_valid_contract():
    obs = {("F2", "900"): {"CNT-9"}}
    res = resolve(obs, {("F2", "900"): {"CNT-1", "CNT-9"}}, ["CNT-1"])
    assert res[("F2", "900")].status is ValidationStatus.CORRECTED
    assert res[("F2", "900")].final_contract == "CNT-1"


def test_discards_when_missing_in_fpr_or_not_valid_or_ambiguous():
    obs = {("A", "9"): {"X"}, ("B", "9"): {"X"}, ("C", "9"): {"X"}}
    fpr = {("B", "9"): {"Z"}, ("C", "9"): {"CNT-1", "CNT-2"}}
    res = resolve(obs, fpr, ["CNT-1", "CNT-2"])
    assert all(r.status is ValidationStatus.DISCARDED and r.reason for r in res.values())