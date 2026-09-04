"""
BNGIS — Scheme Matching & Delivery Engine (SMDE)
=================================================
Algorithm: BNGIS-Match (from project specification)

Steps:
 1. Convert citizen profile -> feature vector (10 dimensions)
 2. Convert each scheme -> eligibility feature vector
 3. Compute cosine similarity
 4. Apply HARD constraints (mandatory eligibility rules)
 5. Rank by priority score (benefit/effort/similarity/urgency weights)
 6. Optimize portfolio (knapsack variant with conflict rules)
 7. Return portfolio + reasons + missed opportunities
"""

import json
import math
import os
from datetime import datetime, timezone

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "schemes.json")


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------
def load_schemes():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["schemes"]


# --------------------------------------------------------------------------
# Step 1: Citizen -> feature vector
# --------------------------------------------------------------------------
def citizen_vector(c: dict) -> list:
    """10-dimensional need vector (matches scheme vector space)."""
    income_lakh = c.get("income_annual", 0) / 100000.0
    return [
        1.0 if income_lakh < 2 else (0.5 if income_lakh < 5 else 0.0),  # low income
        1.0 if c.get("area_type") in ("rural", "tribal") else 0.0,      # rural
        1.0 if c.get("occupation") == "farmer" else 0.0,                # farmer
        1.0 if c.get("gender") == "F" else 0.0,                         # female
        1.0 if c.get("age", 0) >= 60 else 0.0,                          # senior
        1.0 if c.get("occupation") == "student" else 0.0,               # student
        1.0 if c.get("caste") in ("sc", "st") else 0.0,                 # sc/st
        1.0 if c.get("caste") == "obc" else 0.0,                        # obc
        1.0 if c.get("disability") != "none" else 0.0,                  # disabled
        1.0 if c.get("wants_business") else 0.0,                        # biz intent
    ]


# --------------------------------------------------------------------------
# Step 2: Scheme -> eligibility feature vector (same space)
# --------------------------------------------------------------------------
def scheme_vector(s: dict) -> list:
    e = s["eligibility"]
    keys = json.dumps(e)
    return [
        1.0 if "income_max" in keys else 0.2,
        1.0 if e.get("area_type") in (["rural", "tribal"], ["rural"],) else 0.3,
        1.0 if "farmer" in str(e.get("occupation", "")) else 0.0,
        1.0 if e.get("gender") == "F" else 0.2,
        1.0 if e.get("age_min", 0) >= 60 else 0.1,
        1.0 if "student" in str(e.get("occupation", "")) else 0.0,
        0.8 if "sc" in str(e.get("caste", e.get("caste_any", ""))) else 0.1,
        0.6 if "obc" in str(e.get("caste", e.get("caste_any", ""))) else 0.1,
        1.0 if "has_disability" in str(e.get("flags", "")) else 0.1,
        0.9 if "wants_business" in str(e.get("flags_any", "")) else 0.1,
    ]


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


# --------------------------------------------------------------------------
# Step 4: Hard constraint evaluation
# --------------------------------------------------------------------------
def check_eligibility(citizen: dict, s: dict):
    """Return (eligible: bool, reasons: [str], blockers: [str])."""
    e = s["eligibility"]
    reasons, blockers = [], []

    ok = True

    # State-specific scheme
    if e.get("state") and citizen.get("state") != e["state"]:
        blockers.append(f"Only for {e['state']} residents")
        ok = False

    # Age
    age = citizen.get("age", 0)
    if "age_min" in e and age < e["age_min"]:
        blockers.append(f"Minimum age {e['age_min']} (you: {age})")
        ok = False
    if "age_max" in e and age > e["age_max"]:
        blockers.append(f"Maximum age {e['age_max']} (you: {age})")
        ok = False

    # Gender
    if "gender" in e and citizen.get("gender") != e["gender"]:
        blockers.append(f"Only for {e['gender'] == 'F' and 'women' or 'men'}")
        ok = False

    # Occupation
    if "occupation" in e and citizen.get("occupation") not in e["occupation"]:
        blockers.append(f"Requires occupation: {', '.join(e['occupation'])}")
        ok = False

    # Area type
    if "area_type" in e and citizen.get("area_type") not in e["area_type"]:
        blockers.append(f"Only for {', '.join(e['area_type'])} areas")
        ok = False

    # Income (annual -> lakh)
    inc_l = citizen.get("income_annual", 0) / 100000.0
    if "income_max_lakh" in e and inc_l > e["income_max_lakh"]:
        blockers.append(f"Annual income must be under ₹{e['income_max_lakh']} lakh")
        ok = False

    # Land
    land = citizen.get("land_hectares", 0) or 0
    if "land_min" in e and land < e["land_min"]:
        blockers.append("Must own agricultural land")
        ok = False
    if "land_max" in e and land > e["land_max"]:
        blockers.append(f"Land holding above limit ({e['land_max']} ha)")
        ok = False

    # Caste
    if "caste" in e and citizen.get("caste") not in e["caste"]:
        blockers.append(f"For {', '.join(e['caste']).upper()} categories")
        ok = False

    # Caste OR gender (Stand-Up India style)
    if "caste_any" in e and "gender_any" in e:
        if citizen.get("caste") not in e["caste_any"] and citizen.get("gender") not in e["gender_any"]:
            blockers.append("For SC/ST/OBC or women entrepreneurs")
            ok = False

    # House status (PMAY)
    if "house_status" in e and citizen.get("house_status") not in e["house_status"]:
        blockers.append("You already own a pucca house")
        ok = False

    # Bank account
    if e.get("bank_required") and not citizen.get("bank_account"):
        blockers.append("Bank account required")
        ok = False

    # Flags (ALL required)
    for flag in e.get("flags", []):
        if not citizen.get(flag):
            label = {
                "is_pregnant": "pregnant/lactating mothers",
                "is_widow": "widows",
                "has_girl_child": "families with girl child below 10",
                "has_disability": "persons with disability (40%+)",
                "is_minority": "minority community",
                "is_self_employed": "self-employed",
            }.get(flag, flag)
            blockers.append(f"Only for {label}")
            ok = False

    # Flags (ANY of them)
    if "flags_any" in e:
        if not any(citizen.get(f) for f in e["flags_any"]):
            blockers.append("Requires business / self-employment intent")
            ok = False

    # Female family head (Gruha Lakshmi)
    if e.get("family_head_female") and not (
        citizen.get("gender") == "F" and citizen.get("is_family_head")
    ):
        blockers.append("Woman must be declared head of family (ration card)")
        ok = False

    if ok:
        reasons = list(s.get("reasons", []))
        if s.get("level") == "State":
            reasons.append(f"{s.get('state')} state scheme — you qualify")
    return ok, reasons, blockers


# --------------------------------------------------------------------------
# Vulnerability / urgency score (0-1)
# --------------------------------------------------------------------------
def urgency_score(c: dict) -> float:
    u = 0.0
    if c.get("income_annual", 0) < 100000: u += 0.35
    elif c.get("income_annual", 0) < 200000: u += 0.2
    if c.get("disability", "none") != "none": u += 0.2
    if c.get("is_widow"): u += 0.15
    if c.get("age", 0) >= 60: u += 0.15
    if c.get("caste") in ("sc", "st"): u += 0.1
    if c.get("house_status") in ("kutcha", "none"): u += 0.1
    return min(u, 1.0)


# --------------------------------------------------------------------------
# Main matching pipeline
# --------------------------------------------------------------------------
def match_citizen(citizen: dict) -> dict:
    schemes = load_schemes()
    cv = citizen_vector(citizen)
    eligible, rejected = [], []

    for s in schemes:
        ok, reasons, blockers = check_eligibility(citizen, s)
        sim = cosine(cv, scheme_vector(s))
        if ok:
            benefit_norm = min(s["benefit_value"] / 100000.0, 1.0)
            effort_norm = (6 - s["effort"]) / 5.0
            urg = urgency_score(citizen)
            priority = (
                benefit_norm * 0.35
                + s["success_rate"] * 0.25
                + effort_norm * 0.20
                + sim * 0.10
                + urg * 0.10
            )
            eligible.append({
                "id": s["id"],
                "name": s["name"],
                "department": s["department"],
                "level": s["level"],
                "benefit_type": s["benefit_type"],
                "benefit_display": s["benefit_display"],
                "benefit_value": s["benefit_value"],
                "description": s["description"],
                "docs": s["docs"],
                "url": s["url"],
                "avg_days": s["avg_days"],
                "reasons": reasons,
                "similarity": round(sim, 3),
                "urgency": round(urg, 2),
                "priority_score": round(priority * 100, 1),
                "breakdown": {
                    "benefit (35%)": round(benefit_norm * 35, 1),
                    "success (25%)": round(s["success_rate"] * 25, 1),
                    "effort (20%)": round(effort_norm * 20, 1),
                    "similarity (10%)": round(sim * 10, 1),
                    "urgency (10%)": round(urg * 10, 1),
                },
            })
        else:
            rejected.append({
                "id": s["id"],
                "name": s["name"],
                "blockers": blockers,
                "similarity": round(sim, 3),
            })

    eligible.sort(key=lambda x: -x["priority_score"])

    # ------------------------------------------------------------------
    # Step 6: Portfolio optimization (greedy knapsack + conflict rules)
    # ------------------------------------------------------------------
    EFFORT_BUDGET = 9
    conflicts = {}
    for item in eligible:
        src = next(s for s in schemes if s["id"] == item["id"])
        if src.get("conflicts_with"):
            conflicts[item["id"]] = src["conflicts_with"]

    chosen, used = [], 0
    taken_ids = set()
    for item in eligible:  # already sorted by priority
        effort = next(s for s in schemes if s["id"] == item["id"])["effort"]
        if used + effort > EFFORT_BUDGET:
            continue
        if any(cid in taken_ids for cid in conflicts.get(item["id"], [])):
            item["portfolio_note"] = "Skipped — conflicts with higher-priority scheme"
            continue
        chosen.append(item["id"])
        taken_ids.add(item["id"])
        used += effort

    total_yearly = sum(
        i["benefit_value"] for i in eligible if i["id"] in taken_ids
        and i["benefit_type"] in ("Cash", "Subsidy", "Wage", "Pension", "Savings")
    )

    return {
        "citizen_vector": [round(x, 2) for x in cv],
        "eligible": eligible,
        "portfolio": [i for i in eligible if i["id"] in taken_ids],
        "effort_budget": EFFORT_BUDGET,
        "effort_used": used,
        "total_estimated_yearly_value": total_yearly,
        "missed": sorted(
            rejected, key=lambda x: -x["similarity"]
        )[:5],
        "matched_at": datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
    }
