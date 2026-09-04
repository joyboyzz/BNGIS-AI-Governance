"""
BNGIS — Resource Optimization Cortex (ROC) — MVP
================================================
Module 2 of the specification: real-time mapping of public resources
(hospitals, schools, water) + AI allocation with fairness constraints.

This MVP demonstrates the core allocation algorithm over a deterministic
dataset of ~24 public facilities in and around Mysuru, Karnataka:

  1. Haversine distance from citizen location
  2. Availability (1 - utilization)
  3. Quality rating
  → BNGIS Allocation Score = 0.55·proximity + 0.30·availability + 0.15·quality
  → Reroute advisory when the nearest facility is overloaded (>85%)

Constraints from the spec implemented in simplified form:
  accessibility (distance), efficiency (idle capacity), quality (rating).
"""

import math
from datetime import datetime, timezone

# --------------------------------------------------------------------------
# Mysuru-area citizen locations (approximate ward coordinates)
# --------------------------------------------------------------------------
AREAS = {
    "Devaraja Mohalla": (12.3050, 76.6550),
    "Vijayanagar": (12.3110, 76.6420),
    "Gokulam 3rd Stage": (12.3180, 76.6530),
    "Kuvempunagar": (12.2890, 76.6340),
    "JP Nagar": (12.2820, 76.6240),
    "Saraswathipuram": (12.2950, 76.6350),
    "Hebbal": (12.3390, 76.6320),
    "Bannimantap": (12.3180, 76.6680),
    "Nanjangud (rural)": (12.1200, 76.6800),
    "T. Narsipur (rural)": (12.2300, 76.8900),
    "Hunsur (rural)": (12.3100, 76.2900),
}

# --------------------------------------------------------------------------
# Resource dataset (deterministic demo data, plausible Mysuru facilities)
# utilization = % capacity in use right now
# --------------------------------------------------------------------------
RESOURCES = [
    # ---- HOSPITALS ----
    {"id": "h1", "type": "hospital", "name": "KR Hospital (Govt. District HQ)",
     "lat": 12.3059, "lng": 76.6553, "capacity": 1050, "util": 88, "quality": 3.8},
    {"id": "h2", "type": "hospital", "name": "JSS Hospital (Multi-speciality)",
     "lat": 12.2870, "lng": 76.6460, "capacity": 1800, "util": 74, "quality": 4.4},
    {"id": "h3", "type": "hospital", "name": "Apollo BGS Mysuru",
     "lat": 12.2950, "lng": 76.6260, "capacity": 500, "util": 69, "quality": 4.5},
    {"id": "h4", "type": "hospital", "name": "PK Sanjivini Hospital",
     "lat": 12.3095, "lng": 76.6480, "capacity": 300, "util": 91, "quality": 4.0},
    {"id": "h5", "type": "hospital", "name": "Cheluvamba Hospital (Maternity)",
     "lat": 12.3045, "lng": 76.6520, "capacity": 420, "util": 82, "quality": 3.9},
    {"id": "h6", "type": "hospital", "name": "PHC Hebbal (Urban Health Centre)",
     "lat": 12.3380, "lng": 76.6350, "capacity": 60, "util": 47, "quality": 3.4},
    {"id": "h7", "type": "hospital", "name": "Nanjangud Govt. Hospital (Taluk)",
     "lat": 12.1250, "lng": 76.6850, "capacity": 220, "util": 63, "quality": 3.5},
    {"id": "h8", "type": "hospital", "name": "T. Narsipur CHC",
     "lat": 12.2280, "lng": 76.8870, "capacity": 90, "util": 52, "quality": 3.3},
    {"id": "h9", "type": "hospital", "name": "Hunsur Govt. Hospital (Taluk)",
     "lat": 12.3080, "lng": 76.2950, "capacity": 160, "util": 58, "quality": 3.6},

    # ---- SCHOOLS ----
    {"id": "s1", "type": "school", "name": "Govt. Higher Primary School, Vani Vilasa Mohalla",
     "lat": 12.3020, "lng": 76.6600, "capacity": 480, "util": 71, "quality": 3.6},
    {"id": "s2", "type": "school", "name": "Govt. High School, Vijayanagar",
     "lat": 12.3100, "lng": 76.6400, "capacity": 620, "util": 78, "quality": 3.8},
    {"id": "s3", "type": "school", "name": "Morarji Desai Residential School (SC/ST)",
     "lat": 12.2980, "lng": 76.6700, "capacity": 400, "util": 92, "quality": 4.1},
    {"id": "s4", "type": "school", "name": "Govt. School, Gokulam",
     "lat": 12.3170, "lng": 76.6540, "capacity": 350, "util": 64, "quality": 3.5},
    {"id": "s5", "type": "school", "name": "Kuvempunagar Govt. High School",
     "lat": 12.2900, "lng": 76.6360, "capacity": 540, "util": 73, "quality": 3.7},
    {"id": "s6", "type": "school", "name": "Govt. Higher Primary, JP Nagar",
     "lat": 12.2830, "lng": 76.6250, "capacity": 300, "util": 55, "quality": 3.4},
    {"id": "s7", "type": "school", "name": "Nanjangud Govt. High School",
     "lat": 12.1220, "lng": 76.6820, "capacity": 510, "util": 76, "quality": 3.6},
    {"id": "s8", "type": "school", "name": "Hunsur Govt. Junior College",
     "lat": 12.3120, "lng": 76.2920, "capacity": 700, "util": 80, "quality": 3.9},

    # ---- WATER SUPPLY ----
    {"id": "w1", "type": "water", "name": "Hongalli Water Treatment Plant (135 MLD)",
     "lat": 12.2900, "lng": 76.6700, "capacity": 135, "util": 84, "quality": 4.2},
    {"id": "w2", "type": "water", "name": "Belagola WTP (135 MLD)",
     "lat": 12.3300, "lng": 76.6900, "capacity": 135, "util": 79, "quality": 4.3},
    {"id": "w3", "type": "water", "name": "Melapura WTP Phase-1 (135 MLD)",
     "lat": 12.3600, "lng": 76.6100, "capacity": 135, "util": 81, "quality": 4.1},
    {"id": "w4", "type": "water", "name": "Melapura WTP Phase-2 (135 MLD)",
     "lat": 12.3620, "lng": 76.6150, "capacity": 135, "util": 66, "quality": 4.0},
    {"id": "w5", "type": "water", "name": "Vijayanagar Elevated Service Reservoir",
     "lat": 12.3080, "lng": 76.6440, "capacity": 40, "util": 88, "quality": 3.9},
    {"id": "w6", "type": "water", "name": "JP Nagar Ground Reservoir + Booster",
     "lat": 12.2810, "lng": 76.6230, "capacity": 25, "util": 59, "quality": 3.8},
    {"id": "w7", "type": "water", "name": "Nanjangud Mini Water Supply Scheme",
     "lat": 12.1180, "lng": 76.6780, "capacity": 18, "util": 72, "quality": 3.5},
]

TYPE_META = {
    "hospital": {"icon": "🏥", "label": "Hospitals", "unit": "beds",
                 "advisory": "emergency-care routing"},
    "school": {"icon": "🏫", "label": "Schools", "unit": "seats",
               "advisory": "enrollment routing"},
    "water": {"icon": "💧", "label": "Water Supply", "unit": "MLD",
              "advisory": "supply-zone routing"},
}


def haversine_km(lat1, lng1, lat2, lng2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def recommend(lat, lng, rtype="hospital", top_n=5):
    pool = [r for r in RESOURCES if r["type"] == rtype]
    meta = TYPE_META[rtype]

    scored = []
    for r in pool:
        dist = haversine_km(lat, lng, r["lat"], r["lng"])
        prox = max(0.0, 1 - dist / 20.0)            # accessibility constraint
        avail = 1 - r["util"] / 100.0               # efficiency constraint
        qual = r["quality"] / 5.0                   # quality constraint
        score = 0.55 * prox + 0.30 * avail + 0.15 * qual
        free = max(0, round(r["capacity"] * (1 - r["util"] / 100.0)))
        est_wait = 5 if r["util"] <= 70 else (r["util"] - 70) * 3
        scored.append({
            "id": r["id"], "type": rtype, "name": r["name"],
            "lat": r["lat"], "lng": r["lng"],
            "distance_km": round(dist, 2),
            "capacity": r["capacity"], "util": r["util"],
            "free": free, "unit": meta["unit"],
            "quality": r["quality"], "est_wait_min": est_wait,
            "allocation_score": round(score * 100, 1),
            "status": ("OVERLOADED" if r["util"] > 85
                       else "STRAINED" if r["util"] > 75 else "OK"),
        })

    by_dist = sorted(scored, key=lambda x: x["distance_km"])
    ranked = sorted(scored, key=lambda x: -x["allocation_score"])[:top_n]

    # Reroute advisory — spec's core idea: don't send everyone to the nearest
    # facility; balance load across the network.
    nearest = by_dist[0]
    advisory = None
    if nearest["util"] > 85:
        alt = next((r for r in ranked if r["util"] <= 80), None)
        if alt:
            extra_dist = round(alt["distance_km"] - nearest["distance_km"], 2)
            advisory = {
                "problem": f"Nearest facility '{nearest['name']}' is running at "
                           f"{nearest['util']}% capacity (only {nearest['free']} "
                           f"{meta['unit']} free).",
                "action": f"BNGIS reroutes to '{alt['name']}' — {alt['distance_km']} km "
                          f"(+{extra_dist} km) with {alt['free']} {meta['unit']} free "
                          f"and ~{alt['est_wait_min']} min expected wait.",
                "saves_min": max(0, nearest["est_wait_min"] - alt["est_wait_min"]),
            }

    network_util = round(sum(r["util"] for r in pool) / len(pool), 1)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "citizen": {"lat": lat, "lng": lng},
        "type": rtype, "meta": meta,
        "nearest": nearest,
        "ranked": ranked,
        "all_by_distance": by_dist,
        "advisory": advisory,
        "network": {
            "facilities": len(pool),
            "avg_utilization": network_util,
            "free_total": sum(r["free"] for r in scored),
            "overloaded": len([r for r in pool if r["util"] > 85]),
        },
    }
