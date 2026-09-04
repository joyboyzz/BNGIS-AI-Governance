"""
BNGIS — Disaster Response Neural Network (DRNN) — MVP
=====================================================
Module 5 of the specification. Two engines:

  1. EPIDEMIC EARLY WARNING (SEIR + hospital-load coupling)
     - Compartmental SEIR simulation (Susceptible/Exposed/Infected/Removed)
     - Intervention scenarios (R0 reduction via vaccination/containment)
     - Cross-module link to the Resource Cortex: peak hospital demand vs
       actual district bed capacity → deficit alert + supply plan

  2. FLOOD RISK SCORING (multi-factor, Karnataka districts)
     - Rainfall forecast + river levels + terrain + historical exposure
     - Population exposure estimate + automatic response resource plan
       (shelters, water, medical kits, boats)
"""

import math
from datetime import datetime, timezone, timedelta

# ==========================================================================
# 1. SEIR EPIDEMIC ENGINE
# ==========================================================================
def simulate_seir(population=1_000_000, initial_infected=120, r0=2.8,
                  infectious_days=7.0, exposed_days=5.0, days=120,
                  intervention=None):
    """
    SEIR with Euler integration (dt = 1 day).
    intervention: None | {'reduce_pct': 20|40|60, 'from_day': N}
    Returns daily curves + summary statistics.
    """
    gamma = 1.0 / infectious_days        # recovery rate
    sigma = 1.0 / exposed_days           # incubation rate
    beta = r0 * gamma                    # transmission rate

    S = population - initial_infected - initial_infected * 2.0
    E = initial_infected * 2.0
    I = float(initial_infected)
    R = 0.0

    curves = {"S": [], "E": [], "I": [], "R": [], "new": []}
    peak_i, peak_day = I, 0

    for day in range(days):
        eff_beta = beta
        if intervention and day >= intervention.get("from_day", 0):
            eff_beta = beta * (1 - intervention["reduce_pct"] / 100.0)

        new_infections = eff_beta * S * I / population
        s2e = new_infections
        e2i = sigma * E
        i2r = gamma * I

        S -= s2e
        E += s2e - e2i
        I += e2i - i2r
        R += i2r

        if I > peak_i:
            peak_i, peak_day = I, day
        curves["S"].append(S)
        curves["E"].append(E)
        curves["I"].append(I)
        curves["R"].append(R)
        curves["new"].append(new_infections)

    total_infected = population - curves["S"][-1]
    return {
        "population": population,
        "r0": r0,
        "effective_r0": round(
            r0 * (1 - (intervention or {}).get("reduce_pct", 0) / 100.0), 2),
        "days": days,
        "curves": curves,
        "summary": {
            "peak_infected": round(peak_i),
            "peak_day": peak_day,
            "total_infected": round(total_infected),
            "attack_rate_pct": round(100 * total_infected / population, 1),
            "final_recovered": curves["R"][-1],
        },
    }


def hospital_impact(peak_infected, hospitalization_rate=0.05,
                    avg_stay_days=5.0, region_beds=None):
    """Couple epidemic peak to the Resource Cortex bed network."""
    beds_needed_daily = peak_infected * hospitalization_rate
    total_bed_days = beds_needed_daily * avg_stay_days
    impact = {
        "hospitalization_rate": hospitalization_rate,
        "beds_needed_at_peak": round(beds_needed_daily),
        "total_bed_days": round(total_bed_days),
        "region_beds": region_beds,
        "deficit": None,
        "coverage_pct": None,
        "verdict": "",
    }
    if region_beds:
        impact["coverage_pct"] = round(
            100 * region_beds / max(beds_needed_daily, 1), 1)
        if beds_needed_daily <= region_beds * 0.6:
            impact["verdict"] = "CAPACITY OK — existing network absorbs the surge"
        elif beds_needed_daily <= region_beds:
            impact["verdict"] = "STRAINED — activate surge protocol + rerouting"
        else:
            impact["deficit"] = round(beds_needed_daily - region_beds)
            impact["verdict"] = (
                f"DEFICIT of {impact['deficit']:,} beds — deploy field hospitals, "
                f"redirect to neighbouring districts (Resource Cortex reroute)")
    return impact


def epidemic_analysis(pathogen="Dengue (demo serotype 2)", population=1_000_000,
                      initial_infected=120, r0=2.8):
    """Base outbreak + 3 intervention scenarios, benchmarked side by side."""
    base = simulate_seir(population, initial_infected, r0)
    scenarios = [
        {"name": "No intervention", "reduce_pct": 0,
         "note": "uncontrolled spread"},
        {"name": "Weak containment (−20% contact)", "reduce_pct": 20,
         "note": "awareness campaigns only"},
        {"name": "Strong containment (−40% contact)", "reduce_pct": 40,
         "note": "fogging + source reduction + outreach"},
        {"name": "Full response (−60% contact)", "reduce_pct": 60,
         "note": "containment zones + medical camps + vector control"},
    ]
    results = []
    for sc in scenarios:
        sim = simulate_seir(
            population, initial_infected, r0,
            intervention={"reduce_pct": sc["reduce_pct"], "from_day": 10}
            if sc["reduce_pct"] else None)
        results.append({
            "name": sc["name"], "note": sc["note"],
            "reduce_pct": sc["reduce_pct"],
            "peak_infected": sim["summary"]["peak_infected"],
            "peak_day": sim["summary"]["peak_day"],
            "total_infected": sim["summary"]["total_infected"],
            "attack_rate_pct": sim["summary"]["attack_rate_pct"],
        })

    # Resource Cortex bed network (Mysuru demo region)
    region_beds = 4640  # 9 facilities x plausible govt+private surge capacity
    impact = hospital_impact(base["summary"]["peak_infected"],
                             region_beds=region_beds)

    best = min(results[1:], key=lambda x: x["total_infected"])
    lives_saved = results[0]["total_infected"] - best["total_infected"]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "pathogen": pathogen,
        "base": base,
        "scenarios": results,
        "hospital_impact": impact,
        "recommendation": (
            f"Strong containment (−40% contact) prevents ~{lives_saved:,} infections "
            f"versus no action and cuts the peak from "
            f"{results[0]['peak_infected']:,} to {best['peak_infected']:,} concurrent "
            f"cases. {impact['verdict']}."),
    }


# ==========================================================================
# 2. FLOOD RISK SCORING (Karnataka districts, deterministic demo data)
# ==========================================================================
DISTRICTS = [
    # district, rain48_mm_forecast, river_level_pct_of_danger, terrain_risk(0-1),
    # population_lakh, historical_floods_10y, low_lying_pct
    ("Kodagu",            186, 92, 0.82, 5.5, 6, 24),
    ("Chamarajanagar",    142, 78, 0.66, 10.2, 3, 15),
    ("Mysuru",            121, 81, 0.48, 32.4, 3, 12),
    ("Hassan",            134, 69, 0.58, 18.1, 2, 11),
    ("Mandya",            108, 88, 0.52, 22.3, 4, 18),  # KRS downstream
    ("Dakshina Kannada",  168, 85, 0.71, 20.9, 5, 20),
    ("Uttara Kannada",    174, 90, 0.77, 14.4, 6, 22),
    ("Belagavi",          132, 72, 0.60, 48.5, 3, 10),
    ("Ballari",           64, 45, 0.35, 25.1, 1, 5),
    ("Kalaburagi",        52, 38, 0.28, 25.6, 1, 4),
    ("Bengaluru Rural",   88, 52, 0.33, 10.1, 1, 6),
    ("Bidar",             41, 30, 0.22, 17.6, 0, 3),
]


def flood_risk():
    """Composite flood risk = 0.35·rainfall + 0.30·river + 0.20·terrain
    + 0.15·history, with population exposure and a response resource plan."""
    rows = []
    for (name, rain, river, terrain, pop_l, hist, lowlying) in DISTRICTS:
        rain_n = min(rain / 200.0, 1.0)
        river_n = river / 100.0
        hist_n = hist / 6.0
        risk = (0.35 * rain_n + 0.30 * river_n + 0.20 * terrain
                + 0.15 * hist_n) * 100

        # exposure model: share of population in low-lying zones affected at
        # high risk
        displaced = int(pop_l * 100000 * (lowlying / 100)
                        * max(0, (risk - 45) / 100) * 0.6) if risk > 45 else 0
        level = ("SEVERE" if risk > 70 else "HIGH" if risk > 58
                 else "MODERATE" if risk > 45 else "LOW")
        rows.append({
            "district": name,
            "rain48_mm": rain,
            "river_level_pct": river,
            "terrain_risk": round(terrain, 2),
            "population_lakh": pop_l,
            "historical_floods": hist,
            "risk_score": round(risk, 1),
            "risk_level": level,
            "est_displaced": displaced,
        })

    rows.sort(key=lambda r: -r["risk_score"])
    alerts = [r for r in rows if r["risk_level"] in ("SEVERE", "HIGH")]

    # response resource plan for top-risk districts
    plans = []
    for r in alerts[:3]:
        d = max(r["est_displaced"], 1)
        plans.append({
            "district": r["district"],
            "risk": r["risk_score"],
            "actions": [
                f"Activate {math.ceil(d / 400)} relief shelters "
                f"(capacity 400 each, current need: {d:,} people)",
                f"Pre-position {math.ceil(d * 5 / 2000)} water tankers "
                f"({d * 5:,} L/day potable water @5L/person)",
                f"Deploy {math.ceil(d / 1500)} medical teams with ORS + test kits",
                f"Reserve {max(2, math.ceil(d / 3000))} boats + NDRF standby",
                "Push early-warning SMS in Kannada/Urdu/adivasi languages 48h ahead",
            ],
        })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "window": "48-hour monsoon forecast (demo, deterministic)",
        "districts": rows,
        "alerts": [{"district": a["district"], "level": a["risk_level"],
                    "risk": a["risk_score"]} for a in alerts],
        "response_plans": plans,
        "total_displaced_estimate": sum(r["est_displaced"] for r in rows),
    }
