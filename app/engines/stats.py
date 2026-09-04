"""
BNGIS — Dashboard statistics (Module 10: Public Dashboard)
Simulated but deterministic KPIs for the demo dashboard.
Real values come from the corruption engine + scheme DB where possible.
"""

import random
from datetime import datetime, timezone, timedelta

from .corruption import analyze
from .scheme_matcher import load_schemes

def build_stats():
    rng = random.Random(7)
    schemes = load_schemes()
    corruption = analyze()

    # monthly application/satisfaction trend (simulated)
    months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep",
              "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
    applications = [4200, 5100, 6300, 7400, 7100, 8600,
                    9900, 10400, 9700, 11200, 12100, 13800]
    satisfaction = [61, 62, 64, 65, 67, 68, 70, 71, 73, 74, 76, 78]

    resources = [
        {"name": "Hospital beds", "utilization": 71,
         "note": f"{rng.randint(28, 34)}% daily vacancy being re-routed"},
        {"name": "Water supply", "utilization": 64,
         "note": "Leakage reduced 9% after pattern detection"},
        {"name": "Power grid", "utilization": 82,
         "note": "Peak-load forecasting active"},
        {"name": "Public transport", "utilization": 58,
         "note": "Route optimization recovered 12% capacity"},
        {"name": "School capacity", "utilization": 77,
         "note": "Teacher allocation gaps flagged in 3 blocks"},
    ]

    dept_counts = {}
    for s in schemes:
        d = s["department"].split("(")[0].strip()
        dept_counts[d] = dept_counts.get(d, 0) + 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        "kpi": {
            "schemes_indexed": len(schemes),
            "central_schemes": len([s for s in schemes if s["level"] == "Central"]),
            "state_schemes": len([s for s in schemes if s["level"] == "State"]),
            "citizens_matched": 1284503,
            "benefits_routed_cr": 4872,
            "grievance_resolution_days": 6.2,
            "ghosts_detected": corruption["ghosts"]["estimated_ghosts"],
            "leakage_detected_cr": round(
                corruption["ghosts"]["estimated_leakage_lakh"] / 100, 2),
        },
        "monthly": {"labels": months, "applications": applications,
                    "satisfaction": satisfaction},
        "resources": resources,
        "schemes_by_dept": dept_counts,
        "dept_risk": [
            {"department": d["department"], "risk": d["risk_score"],
             "level": d["risk_level"]}
            for d in corruption["departments"]
        ],
    }
