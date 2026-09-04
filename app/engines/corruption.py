"""
BNGIS — Corruption Detection Shield (CDS)
=========================================
Multi-layered anomaly detection (Module 4 of specification):

  Layer 1: Benford's Law analysis        (first-digit distribution)
  Layer 2: Statistical anomaly detection (z-score outlier scoring)
  Layer 3: Vendor network analysis       (concentration / clustering)
  Layer 4: Temporal pattern analysis     (threshold-splitting, weekend,
                                           fiscal-year spikes)
  Layer 5: Ghost beneficiary detection   (fuzzy name + address clustering)

All data is synthetic (seeded) for the demo — patterns injected
deliberately so the detector has something to find.
"""

import math
import random
import statistics
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

DEPARTMENTS = [
    "Public Works (PWD)",
    "Water Supply & Sanitation",
    "Rural Development",
    "Education",
    "Health & Family Welfare",
]

VENDORS = [
    "Sri Venkateshwara Constructions", "Bharat Infra Pvt Ltd",
    "Mysore Road Works Co", "Kaveri Traders", "Ganesh Supplies",
    "Sunrise Electricals", "Deccan Cement Agencies", "Nandi Transport",
    "Green Valley Landscapers", "Sagar Hardware & Paints",
    "Vishwa Enterprises", "Chethana Interiors",
]

FRAUD_VENDOR = "XYZ Infra Solutions (suspect)"
THRESHOLD = 50000  # approval threshold for demo


# ==========================================================================
# Synthetic transaction generator (deterministic)
# ==========================================================================
def generate_transactions():
    """~1,250 transactions across 5 departments, with injected fraud patterns.
    Fully deterministic: each call uses a fresh seeded generator."""
    rng = random.Random(42)  # noqa: F811 (local on purpose)
    txns = []
    fiscal_start = datetime(2025, 4, 1)
    tid = 1000

    for dept in DEPARTMENTS:
        n = 210 + rng.randint(0, 50)
        for _ in range(n):
            days_in = rng.randint(0, 364)
            dt = fiscal_start + timedelta(days=days_in)
            if dt.weekday() >= 5:          # govt offices work weekdays only
                dt += timedelta(days=2)
            # log-normal legitimate amounts, rupee-level (NOT rounded —
            # rounding would itself distort Benford's Law)
            amt = int(math.exp(rng.gauss(9.8, 0.85)))
            amt = max(1500, min(amt, 900000))
            vendor = rng.choice(VENDORS)
            txns.append({
                "id": tid, "dept": dept, "vendor": vendor,
                "amount": amt, "date": dt.strftime("%Y-%m-%d"),
                "dow": dt.weekday(),
            })
            tid += 1

    # --- Injected pattern A: threshold splitting (just below ₹50k) --------
    for i in range(12):
        dt = fiscal_start + timedelta(days=110 + i * 4)
        if dt.weekday() >= 5:
            dt += timedelta(days=2)
        txns.append({
            "id": tid, "dept": "Public Works (PWD)", "vendor": FRAUD_VENDOR,
            "amount": rng.choice([48700, 49100, 49300, 49700, 49900]),
            "date": dt.strftime("%Y-%m-%d"), "dow": dt.weekday(),
        })
        tid += 1

    # --- Injected pattern B: round-amount weekend payments ---------------
    for i in range(20):
        dt = fiscal_start + timedelta(days=200 + i * 5)
        if dt.weekday() < 5:
            dt += timedelta(days=5 - dt.weekday())  # push to Saturday
        txns.append({
            "id": tid, "dept": "Education", "vendor": FRAUD_VENDOR,
            "amount": rng.choice([100000, 150000, 200000]),
            "date": dt.strftime("%Y-%m-%d"), "dow": 5,
        })
        tid += 1

    # --- Injected pattern C: fiscal-year-end spike ------------------------
    for i in range(30):
        dt = datetime(2026, 3, 18 + (i % 13))
        if dt.weekday() >= 5:
            dt += timedelta(days=2)
        txns.append({
            "id": tid, "dept": "Water Supply & Sanitation", "vendor": rng.choice(VENDORS[:4]),
            "amount": int(math.exp(rng.gauss(11.2, 0.35))),
            "date": dt.strftime("%Y-%m-%d"), "dow": dt.weekday(),
        })
        tid += 1

    txns.sort(key=lambda t: t["date"])
    return txns


# ==========================================================================
# Layer 1: Benford's Law
# ==========================================================================
def benford_expected():
    return {d: math.log10(1 + 1 / d) for d in range(1, 10)}


def benford_analysis(amounts):
    if not amounts:
        return None
    counts = {d: 0 for d in range(1, 10)}
    for a in amounts:
        first = int(str(int(a))[0])
        if 1 <= first <= 9:
            counts[first] += 1
    total = sum(counts.values())
    actual = {d: counts[d] / total for d in range(1, 10)}
    expected = benford_expected()

    # Chi-square statistic
    chi2 = sum(
        (counts[d] - total * expected[d]) ** 2 / (total * expected[d])
        for d in range(1, 10)
    )
    # Mean Absolute Deviation (quick conformity check)
    mad = sum(abs(actual[d] - expected[d]) for d in range(1, 10)) / 9

    if mad < 0.006: conformity = "Close conformity — low risk"
    elif mad < 0.012: conformity = "Acceptable — some deviation"
    elif mad < 0.015: conformity = "Marginal — needs review"
    else: conformity = "NON-CONFORMITY — high manipulation risk"

    return {
        "actual": {str(d): round(actual[d], 4) for d in range(1, 10)},
        "expected": {str(d): round(expected[d], 4) for d in range(1, 10)},
        "chi_square": round(chi2, 2),
        "critical_value_1pct": 20.09,   # df=8, alpha=0.01
        "mad": round(mad, 5),
        "conformity": conformity,
        "n": total,
    }


# ==========================================================================
# Layer 2: Transaction anomaly scoring (robust z-scores)
# ==========================================================================
def detect_anomalies(txns):
    amounts = [t["amount"] for t in txns]
    med = statistics.median(amounts)
    mad = statistics.median([abs(a - med) for a in amounts]) or 1.0

    vendor_counts, vendor_subthr, vendor_round = {}, {}, {}
    for t in txns:
        v = t["vendor"]
        vendor_counts[v] = vendor_counts.get(v, 0) + 1
        if THRESHOLD * 0.95 <= t["amount"] < THRESHOLD:
            vendor_subthr[v] = vendor_subthr.get(v, 0) + 1
        if t["amount"] % 50000 == 0 and t["amount"] >= 100000:
            vendor_round[v] = vendor_round.get(v, 0) + 1

    flagged = []
    for t in txns:
        score, why = 0.0, []
        z = abs(0.6745 * (t["amount"] - med) / mad)
        if z > 3.5:
            score += min(z / 8, 0.4); why.append(f"statistical outlier (z={z:.1f})")
        if THRESHOLD * 0.95 <= t["amount"] < THRESHOLD:
            score += 0.35; why.append("just below ₹50k approval threshold")
        if t["amount"] % 50000 == 0 and t["amount"] >= 100000:
            score += 0.2; why.append("suspiciously round amount")
        if t["dow"] >= 5:
            score += 0.25; why.append("weekend transaction (offices closed)")
        if vendor_subthr.get(t["vendor"], 0) >= 4:
            score += 0.3; why.append("vendor systematically paid below threshold")
        if vendor_round.get(t["vendor"], 0) >= 4:
            score += 0.2; why.append("vendor receives repeated round amounts")
        if score >= 0.5:
            flagged.append({**t, "risk": round(min(score, 1.0), 2), "flags": why})
    flagged.sort(key=lambda x: -x["risk"])
    return flagged[:25]


# ==========================================================================
# Layer 3: Vendor concentration
# ==========================================================================
def vendor_analysis(txns):
    by_vendor = {}
    for t in txns:
        v = t["vendor"]
        by_vendor.setdefault(v, {"count": 0, "total": 0.0, "subthr": 0, "round": 0})
        by_vendor[v]["count"] += 1
        by_vendor[v]["total"] += t["amount"]
        if THRESHOLD * 0.95 <= t["amount"] < THRESHOLD:
            by_vendor[v]["subthr"] += 1
        if t["amount"] % 50000 == 0 and t["amount"] >= 100000:
            by_vendor[v]["round"] += 1
    grand = sum(v["total"] for v in by_vendor.values())
    rows = [
        {
            "vendor": v,
            "count": d["count"],
            "total": round(d["total"], 0),
            "share_pct": round(d["total"] / grand * 100, 1),
            "flagged": d["subthr"] >= 4 or d["round"] >= 4,
            "flag_reason": (
                (f"{d['subthr']} payments just below ₹50k threshold" if d["subthr"] >= 4
                 else f"{d['round']} round-amount payments" if d["round"] >= 4 else "")
            ),
        }
        for v, d in by_vendor.items()
    ]
    rows.sort(key=lambda r: -r["share_pct"])
    # HHI concentration index
    hhi = sum((r["share_pct"]) ** 2 for r in rows)
    return {
        "vendors": rows[:8],
        "hhi": round(hhi, 0),
        "verdict": (
            "HIGH concentration (cartel risk)" if hhi > 2000
            else "Moderate concentration" if hhi > 1500
            else "Healthy competition"
        ),
    }


# ==========================================================================
# Layer 4: Temporal patterns
# ==========================================================================
def temporal_analysis(txns):
    by_month = {}
    for t in txns:
        m = t["date"][:7]
        by_month.setdefault(m, {"count": 0, "total": 0.0})
        by_month[m]["count"] += 1
        by_month[m]["total"] += t["amount"]

    months = sorted(by_month)
    totals = [by_month[m]["total"] for m in months]
    mean, sd = statistics.mean(totals), (statistics.pstdev(totals) or 1)
    spikes = [
        {"month": m, "total": round(by_month[m]["total"]),
         "z": round((by_month[m]["total"] - mean) / sd, 1)}
        for m in months if (by_month[m]["total"] - mean) / sd > 1.8
    ]
    weekend_pct = round(
        100 * len([t for t in txns if t["dow"] >= 5]) / len(txns), 1
    )
    split_pct = round(
        100 * len([t for t in txns
                   if THRESHOLD * 0.95 <= t["amount"] < THRESHOLD]) / len(txns), 2
    )
    return {
        "monthly": [{"month": m, "total": round(by_month[m]["total"]),
                     "count": by_month[m]["count"]} for m in months],
        "spikes": spikes,
        "weekend_pct": weekend_pct,
        "threshold_split_pct": split_pct,
        "patterns_found": (
            [f"Fiscal-year-end spike in {sp['month']} ({sp['z']}σ)" for sp in spikes]
            + (weekend_pct > 20 and [f"{weekend_pct}% weekend transactions"] or [])
            + (split_pct > 1 and [f"{split_pct}% payments just below approval threshold"] or [])
        ),
    }


# ==========================================================================
# Layer 5: Ghost beneficiary detection
# ==========================================================================
GHOST_NAMES = [
    "Ramesh Kumar", "Ramesh Kumar", "Ramesh Kumaar", "Sunita Devi", "Sunita Devi",
    "Mohammed Irfan", "Mohammad Irfan", "Lakshmi Bai", "Lakshmibai", "Venkatesh Rao",
    "Venkatesh Rao", "Anita Sharma", "Anitha Sharma", "Ravi Shankar", "Ravi Sankar",
    "Ganga Bai", "Gangabai", "Imran Khan", "Imraan Khan", "Joseph Thomas",
    "Manjunath S", "Manjunatha S", "Fatima Begum", "Fatima Begum", "Shivakumar",
    "Shiva Kumar", "Padma Priya", "Padmapriya", "Nagaraj Gowda", "Nagaraja Gowda",
    "Deepa Nair", "Deepa Nair", "Suresh Babu", "Suresh Babu", "Kavitha Reddy",
    "Kavitha Reddy", "Prakash Jha", "Prakash Jhaa", "Mohan Das", "Mohan Das",
]
AREAS = ["GH-Block-A/4", "GH-Block-A/4", "Ward-12", "Ward-12", "Colony-3",
         "Colony-3", "Ward-07", "GH-Block-B/9", "Ward-12", "Colony-3"]


def ghost_detection():
    rng = random.Random(99)
    beneficiaries = []
    for i, name in enumerate(GHOST_NAMES):
        beneficiaries.append({
            "id": 5000 + i,
            "name": name,
            "area": rng.choice(AREAS),
            "scheme": rng.choice(["PM-KISAN", "Old-age pension", "Ration (NFSA)"]),
        })
    area_counts = {}
    for b in beneficiaries:
        area_counts[b["area"]] = area_counts.get(b["area"], 0) + 1

    # fuzzy duplicate pairs
    pairs = []
    for i in range(len(beneficiaries)):
        for j in range(i + 1, len(beneficiaries)):
            ratio = SequenceMatcher(
                None, beneficiaries[i]["name"].lower(), beneficiaries[j]["name"].lower()
            ).ratio()
            if ratio >= 0.86:
                pairs.append({
                    "a": beneficiaries[i], "b": beneficiaries[j],
                    "match_pct": round(ratio * 100),
                })
    clusters = {a: c for a, c in area_counts.items() if c >= 8}
    return {
        "total_beneficiaries": len(beneficiaries),
        "duplicate_pairs": pairs,
        "suspicious_address_clusters": clusters,
        "estimated_ghosts": len(pairs) + sum(1 for _ in clusters),
        "estimated_leakage_lakh": round(
            (len(pairs) + len(clusters)) * 0.18, 1
        ),
    }


# ==========================================================================
# Full department-level report
# ==========================================================================
_CACHE = {}


def analyze():
    if "report" in _CACHE:
        return _CACHE["report"]
    txns = generate_transactions()
    report = {"generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
              "total_transactions": len(txns)}

    # Global Benford
    report["benford_overall"] = benford_analysis([t["amount"] for t in txns])

    # Per-department risk — adaptive baseline-excess scoring.
    # Clean departments sit near baseline (outlier≈5-7%, flag≈0.4%,
    # weekend=0, March≈8.5%, top-vendor≈12%); fraud pushes a department
    # ABOVE baseline, and only the EXCESS counts as risk (spec Layer 4:
    # "Adaptive threshold based on department baseline").
    depts = []
    for dept in DEPARTMENTS:
        sub = [t for t in txns if t["dept"] == dept]
        b = benford_analysis([t["amount"] for t in sub])
        n_sub = max(len(sub), 1)
        flag_ratio = len([t for t in sub
                          if THRESHOLD * 0.95 <= t["amount"] < THRESHOLD]) / n_sub
        weekend = len([t for t in sub if t["dow"] >= 5]) / n_sub
        fye_share = len([t for t in sub if t["date"][5:7] == "03"]) / n_sub
        amounts = [t["amount"] for t in sub]
        med = statistics.median(amounts)
        mad = statistics.median([abs(a - med) for a in amounts]) or 1
        outlier_ratio = len([a for a in amounts if abs(0.6745 * (a - med) / mad) > 3.5]) / n_sub
        vend_amt = {}
        for t in sub:
            vend_amt[t["vendor"]] = vend_amt.get(t["vendor"], 0) + t["amount"]
        top_share = max(vend_amt.values()) / sum(vend_amt.values())

        # baseline excesses
        flag_ex = max(0.0, flag_ratio - 0.01)
        outlier_ex = max(0.0, outlier_ratio - 0.07)
        wknd_ex = weekend                      # legit data: weekdays only
        fye_ex = max(0.0, fye_share - 0.10)
        vend_ex = max(0.0, top_share - 0.18)

        anom_layer = min(1, outlier_ex * 5 + flag_ex * 20)
        vend_layer = min(1, vend_ex * 4 + flag_ex * 6)
        temp_layer = min(1, wknd_ex * 6 + fye_ex * 12)
        benf_layer = min(b["mad"] / 0.03, 1)   # noise floor keeps it > 0

        risk = (anom_layer * 0.35 + vend_layer * 0.30 +
                temp_layer * 0.20 + benf_layer * 0.15) * 100

        depts.append({
            "department": dept,
            "n_txns": len(sub),
            "benford_mad": b["mad"],
            "risk_score": round(risk, 1),
            "risk_level": ("CRITICAL" if risk > 65 else "HIGH" if risk > 45
                           else "MEDIUM" if risk > 25 else "LOW"),
            "layers": {
                "anomaly": round(anom_layer * 100),
                "vendor": round(vend_layer * 100),
                "temporal": round(temp_layer * 100),
                "benford": round(benf_layer * 100),
            },
        })
    depts.sort(key=lambda d: -d["risk_score"])
    report["departments"] = depts
    report["flagged_transactions"] = detect_anomalies(txns)
    report["vendor_analysis"] = vendor_analysis(txns)
    report["temporal"] = temporal_analysis(txns)
    report["ghosts"] = ghost_detection()
    _CACHE["report"] = report
    return report


if __name__ == "__main__":
    import json
    r = analyze()
    print(json.dumps({k: r[k] for k in ("total_transactions", "departments", "ghosts")},
                     indent=2)[:1500])
