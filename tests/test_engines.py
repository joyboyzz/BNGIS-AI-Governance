"""
BNGIS — Engine test suite (pytest)
Run:  pip install -r requirements.txt -r requirements-dev.txt && pytest -v
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.engines import (blockchain, corruption, disaster, resources,
                         scheme_matcher, voice)

# ==========================================================================
# Module 3 — Scheme Matching Engine
# ==========================================================================
LAKSHMI = {
    "age": 34, "gender": "F", "state": "KA", "area_type": "rural",
    "income_annual": 96000, "occupation": "daily_wage", "caste": "sc",
    "land_hectares": 0.0, "house_status": "kutcha", "disability": "none",
    "bank_account": True, "has_girl_child": True, "is_family_head": True,
}


def test_match_lakshmi_eligibility():
    r = scheme_matcher.match_citizen(LAKSHMI)
    ids = [s["id"] for s in r["eligible"]]
    assert "pm-jay" in ids            # low income -> health cover
    assert "shakti" in ids            # KA woman -> free bus
    assert "gruha-lakshmi" in ids     # KA woman family head
    assert "mgnrega" in ids           # rural adult
    assert all(s["priority_score"] <= 100 for s in r["eligible"])


def test_match_farmer_gets_pm_kisan():
    farmer = dict(LAKSHMI, age=45, gender="M", occupation="farmer",
                  land_hectares=1.2, is_family_head=True, has_girl_child=False)
    ids = [s["id"] for s in scheme_matcher.match_citizen(farmer)["eligible"]]
    assert "pm-kisan" in ids and "pmfby" in ids and "kcc" in ids


def test_match_income_blocks_pmjay():
    rich = dict(LAKSHMI, income_annual=900000)
    ids = [s["id"] for s in scheme_matcher.match_citizen(rich)["eligible"]]
    assert "pm-jay" not in ids


def test_portfolio_conflict_rule():
    biz = dict(LAKSHMI, age=28, gender="M", occupation="self_employed",
               caste="obc", wants_business=True, house_status="own_pucca",
               income_annual=240000, has_girl_child=False, is_family_head=True)
    r = scheme_matcher.match_citizen(biz)
    port_ids = {p["id"] for p in r["portfolio"]}
    assert not ({"pm-mudra", "stand-up-india"} <= port_ids), \
        "conflicting schemes must never both be in the portfolio"


def test_missed_has_reasons():
    r = scheme_matcher.match_citizen(LAKSHMI)
    assert len(r["missed"]) > 0
    assert all(m["blockers"] for m in r["missed"])


# ==========================================================================
# Module 4 — Corruption Detection Shield
# ==========================================================================
def test_corruption_deterministic():
    a, b = corruption.analyze(), corruption.analyze()
    assert a["total_transactions"] == b["total_transactions"]
    assert [d["risk_score"] for d in a["departments"]] == \
           [d["risk_score"] for d in b["departments"]]


def test_injected_fraud_detected():
    r = corruption.analyze()
    by_dept = {d["department"]: d for d in r["departments"]}
    # injected patterns must surface as HIGH risk
    assert by_dept["Public Works (PWD)"]["risk_level"] in ("HIGH", "CRITICAL")
    assert by_dept["Education"]["risk_level"] in ("HIGH", "CRITICAL")
    # clean departments must stay LOW
    assert by_dept["Health & Family Welfare"]["risk_level"] == "LOW"


def test_flagged_vendor_caught():
    r = corruption.analyze()
    flagged = [v for v in r["vendor_analysis"]["vendors"] if v["flagged"]]
    assert any("XYZ Infra" in v["vendor"] for v in flagged)


def test_ghost_duplicates_found():
    g = corruption.ghost_detection()
    assert g["duplicate_pairs"], "fuzzy duplicate beneficiaries must be found"
    assert g["duplicate_pairs"][0]["match_pct"] >= 86


def test_benford_valid_output():
    r = corruption.analyze()
    b = r["benford_overall"]
    assert abs(sum(b["actual"].values()) - 1.0) < 0.01
    assert b["expected"]["1"] > b["expected"]["9"]  # log-shaped


# ==========================================================================
# Module 7 — Transparency Blockchain
# ==========================================================================
import pytest


@pytest.fixture
def fresh_chain(tmp_path, monkeypatch):
    """Redirect the chain to a temp file so tests never touch app data."""
    monkeypatch.setattr(blockchain, "CHAIN_PATH", str(tmp_path / "chain.json"))
    return blockchain.GovernanceChain()


def test_chain_add_and_verify(fresh_chain):
    fresh_chain.add("DECISION", {"dept": "Test", "amount": 100})
    v = fresh_chain.verify()
    assert v["valid"] is True


def test_chain_detects_tampering(fresh_chain):
    fresh_chain.add("EXPENDITURE", {"dept": "Test", "amount": 500})
    fresh_chain.tamper(1)
    v = fresh_chain.verify()
    assert v["valid"] is False and v["broken_at"] == 1


def test_chain_repair(fresh_chain):
    fresh_chain.add("EXPENDITURE", {"dept": "Test", "amount": 500})
    fresh_chain.tamper(1)
    assert fresh_chain.repair()["valid"] is True


# ==========================================================================
# Module 2 — Resource Optimization Cortex
# ==========================================================================
def test_resources_reroute_advisory():
    # Vijayanagar: nearest hospital (PK Sanjivini) is 91% full -> advisory
    r = resources.recommend(12.3110, 76.6420, "hospital")
    assert r["nearest"]["util"] > 85
    assert r["advisory"] is not None
    assert "reroute" in r["advisory"]["action"].lower()


def test_resources_healthy_no_advisory():
    # JP Nagar water: nearest reservoir healthy -> no reroute needed
    r = resources.recommend(12.2820, 76.6240, "water")
    assert r["advisory"] is None or r["nearest"]["util"] <= 85


def test_resources_ranking_order():
    r = resources.recommend(12.3050, 76.6550, "school")
    scores = [x["allocation_score"] for x in r["ranked"]]
    assert scores == sorted(scores, reverse=True)


# ==========================================================================
# Module 5 — Disaster Response
# ==========================================================================
def test_seir_intervention_reduces_peak():
    base = disaster.simulate_seir(r0=2.8)
    full = disaster.simulate_seir(r0=2.8,
                                  intervention={"reduce_pct": 60, "from_day": 10})
    assert full["summary"]["peak_infected"] < \
           base["summary"]["peak_infected"] * 0.05


def test_seir_conservation():
    sim = disaster.simulate_seir(days=30)
    last = {k: v[-1] for k, v in sim["curves"].items()}
    assert abs(last["S"] + last["E"] + last["I"] + last["R"] - sim["population"]) < 5


def test_flood_kodagu_severe():
    f = disaster.flood_risk()
    top = f["districts"][0]
    assert top["district"] == "Kodagu"
    assert top["risk_level"] == "SEVERE"
    assert f["response_plans"], "response plans must be generated"


# ==========================================================================
# Module 8 — Citizen Voice NLP
# ==========================================================================
def test_voice_language_detection():
    assert voice.detect_language("no water supply problem") == "en"
    assert voice.detect_language("రోడ్డు పై గుండు ఉంది") == "te"
    assert voice.detect_language("अस्पताल में दवा नहीं") == "hi"
    assert voice.detect_language("ಆಸ್ಪತ್ರೆಯಲ್ಲಿ ಔಷಧಿ ಇಲ್ಲ") == "kn"


def test_voice_routes_to_correct_department():
    r = voice.analyze_message("No water supply for 3 days, urgent!")
    assert r["category"] == "water"
    assert "Water" in r["department"]
    assert r["priority"].startswith(("P1", "P2"))


def test_voice_corruption_escalates_to_lokayukta():
    r = voice.analyze_message("राशन कार्ड में नाम जुड़ने के लिए दलाल 500 रुपये मांग रहा है")
    assert r["category"] == "corruption"
    assert "Lokayukta" in r["department"] or "Anti-Corruption" in r["department"]


def test_voice_positive_sentiment():
    r = voice.analyze_message("The doctor was kind and helpful, thanks")
    assert r["sentiment"] > 0


def test_voice_emergency_priority():
    r = voice.analyze_message("Snake bite! unconscious, emergency hospital immediately")
    assert r["urgency"] >= 0.6
    assert r["priority"].startswith("P1")


def test_voice_feed_analytics():
    f = voice.feed_analytics()
    assert f["analytics"]["total"] >= 10
    assert len(f["analytics"]["languages"]) >= 3
