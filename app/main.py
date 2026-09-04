"""
BNGIS — Bharath Neuro-Governance Intelligence System (MVP backend)
FastAPI application: serves the dashboard + AI engines as REST API.
"""

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.engines import (blockchain, corruption, disaster, resources,
                         scheme_matcher, stats, voice)

app = FastAPI(title="BNGIS API", version="1.0.0",
              description="AI-Powered Democratic Governance Platform (MVP)")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

BASE = os.path.dirname(__file__)
STATIC = os.path.join(BASE, "..", "static")

chain = blockchain.GovernanceChain()
_corruption_cache = None


# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------
class CitizenProfile(BaseModel):
    name: str = Field(default="", description="Optional")
    age: int = 25
    gender: str = "F"            # M / F / Other
    state: str = "KA"
    area_type: str = "rural"     # urban / semi / rural / tribal
    income_annual: int = 120000
    occupation: str = "farmer"   # farmer / daily_wage / labour / student /
    # unemployed / self_employed / salaried / housewife / retired
    caste: str = "general"       # general / obc / sc / st
    education: str = "10th"
    family_size: int = 4
    land_hectares: float = 0.0
    house_status: str = "kutcha"  # own_pucca / kutcha / rented / none
    disability: str = "none"     # none / locomotor / visual / hearing / intellectual
    bank_account: bool = True
    is_pregnant: bool = False
    is_widow: bool = False
    has_girl_child: bool = False
    wants_business: bool = False
    is_family_head: bool = False
    is_minority: bool = False


class RecordRequest(BaseModel):
    block_type: str = "DECISION"
    data: dict = {}


# --------------------------------------------------------------------------
# API routes
# --------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "BNGIS", "version": "1.0.0"}


@app.get("/api/stats")
def get_stats():
    return stats.build_stats()


@app.get("/api/schemes")
def get_schemes():
    return {"schemes": scheme_matcher.load_schemes()}


@app.get("/api/resources")
def get_resources(lat: float = 12.3050, lng: float = 76.6550,
                  type: str = "hospital"):
    """Module 2 MVP: resource allocation recommendations for a location."""
    if type not in resources.TYPE_META:
        type = "hospital"
    return resources.recommend(lat, lng, type)


# ---------------- Module 5: Disaster Response ----------------
_epidemic_cache = None


@app.get("/api/disaster/epidemic")
def get_epidemic():
    """Module 5: SEIR epidemic simulation + intervention scenarios +
    hospital-load coupling."""
    global _epidemic_cache
    if _epidemic_cache is None:
        _epidemic_cache = disaster.epidemic_analysis()
        block = chain.add("DISASTER_MODEL", {
            "model": "SEIR",
            "pathogen": _epidemic_cache["pathogen"],
            "peak_infected": _epidemic_cache["base"]["summary"]["peak_infected"],
        })
        _epidemic_cache["chain_block"] = {"index": block["index"],
                                          "hash": block["hash"]}
    return _epidemic_cache


@app.get("/api/disaster/flood")
def get_flood():
    """Module 5: district flood risk scoring + response resource plans."""
    result = disaster.flood_risk()
    block = chain.add("DISASTER_ALERT", {
        "severe_districts": [a["district"] for a in result["alerts"]
                             if a["level"] == "SEVERE"],
        "displaced_estimate": result["total_displaced_estimate"],
    })
    result["chain_block"] = {"index": block["index"], "hash": block["hash"]}
    return result


# ---------------- Module 8: Citizen Voice NLP ----------------
class VoiceRequest(BaseModel):
    message: str


@app.post("/api/voice")
def analyze_voice(req: VoiceRequest):
    """Module 8: multilingual grievance NLP (language, sentiment, intent,
    urgency, routing, ticket)."""
    result = voice.analyze_message(req.message)
    block = chain.add("GRIEVANCE", {
        "ticket": result["ticket"],
        "category": result["category"],
        "priority": result["priority"].split(" ")[0],
        "department": result["department"],
    })
    result["chain_block"] = {"index": block["index"], "hash": block["hash"]}
    return result


@app.get("/api/voice/samples")
def voice_samples():
    """Module 8: pre-analyzed multilingual sample feed + analytics."""
    return voice.feed_analytics()


@app.post("/api/match")
def match(profile: CitizenProfile):
    citizen = profile.model_dump()
    result = scheme_matcher.match_citizen(citizen)

    # Record on transparency chain (Module 7 integration)
    summary = {
        "citizen": citizen.get("name") or "anonymous-citizen",
        "state": citizen["state"],
        "eligible_count": len(result["eligible"]),
        "portfolio_ids": [p["id"] for p in result["portfolio"]],
        "estimated_yearly_value": result["total_estimated_yearly_value"],
    }
    block = chain.add("SERVICE_MATCH", summary)
    result["chain_block"] = {"index": block["index"], "hash": block["hash"]}
    return result


@app.get("/api/corruption/analyze")
def corruption_analyze():
    global _corruption_cache
    if _corruption_cache is None:
        _corruption_cache = corruption.analyze()
        block = chain.add(
            "CORRUPTION_AUDIT",
            {
                "departments_scanned": len(_corruption_cache["departments"]),
                "transactions": _corruption_cache["total_transactions"],
                "flagged": len(_corruption_cache["flagged_transactions"]),
                "top_risk": _corruption_cache["departments"][0]["department"],
            },
        )
        _corruption_cache["chain_block"] = {
            "index": block["index"], "hash": block["hash"]}
    return _corruption_cache


@app.get("/api/chain")
def get_chain():
    return {"blocks": chain.list(60), "total": len(chain.chain)}


@app.post("/api/chain/record")
def record_on_chain(req: RecordRequest):
    block = chain.add(req.block_type, req.data)
    return {"recorded": True, "block": block}


@app.get("/api/chain/verify")
def verify_chain():
    return chain.verify()


@app.post("/api/chain/tamper")
def tamper_chain():
    """DEMO: simulate a hacker editing the ledger, then verify to catch it."""
    result = chain.tamper(1)
    return result


@app.post("/api/chain/repair")
def repair_chain():
    return chain.repair()


# --------------------------------------------------------------------------
# Static frontend
# --------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC, "index.html"))
