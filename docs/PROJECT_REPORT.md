# BHARATH NEURO-GOVERNANCE INTELLIGENCE SYSTEM (BNGIS)
## AI-Powered Real-Time Democratic Governance & Public Resource Optimization Platform — Project Report (MVP)

---

## 1. Abstract

India runs thousands of welfare schemes, yet an estimated 67% of eligible citizens remain unaware of them, corruption leaks over ₹1.2 lakh crore a year from delivery systems, and grievance redressal is slow and reactive. Existing platforms (MyGov, UMANG, DigiLocker) provide access or feedback, but none of them create an *intelligent layer* that connects citizens, schemes, resources and auditors automatically.

BNGIS (Bharath Neuro-Governance Intelligence System) proposes a zero-cost, fully open-source "AI brain" for governance. This project implements the MVP of that vision as a working web platform with three core intelligence engines: (1) a **Scheme Matching & Delivery Engine** that converts a citizen's profile into a need-vector and computes an optimal portfolio of eligible government schemes using vector similarity, hard-constraint filtering, weighted priority scoring and knapsack optimization; (2) a **Corruption Detection Shield** that audits government transactions using Benford's Law, robust statistical outlier detection, vendor-network concentration analysis, temporal pattern recognition and fuzzy ghost-beneficiary detection, using adaptive baseline-excess scoring; and (3) a **Transparency Blockchain** — a lightweight SHA-256 hash chain that immutably records every AI action for public audit. A bilingual (English/తెలుగు) real-time dashboard ties the system together. The MVP indexes 21 real schemes (Central + Karnataka state) and demonstrates detection of four deliberately-injected fraud patterns in a 1,250-transaction synthetic dataset. The entire stack — Python/FastAPI backend, vanilla-JS frontend, zero paid APIs — can be deployed at ₹0 cost.

**Keywords:** e-governance, AI, Benford's Law, anomaly detection, scheme matching, knapsack optimization, blockchain transparency, DBT.

---

## 2. Introduction

### 2.1 Problem statement
| Problem | Scale (from BNGIS specification) |
|---|---|
| Undelivered government schemes | ₹3.8 lakh crore/year |
| Citizens unaware of eligible schemes | 67% of eligible people |
| Corruption leakage in delivery | ₹1.2 lakh crore |
| Ghost beneficiaries (ration fraud) | 23% |
| Avg grievance resolution delay | Weeks–months, reactive |

### 2.2 Why existing systems fail
- **MyGov / grievance portals** → feedback only, no intelligence.
- **UMANG** → service access, no optimization or matching.
- **DigiLocker** → documents, no resource mapping.
- **Smart City projects** → siloed, no cross-domain learning.

None of them connect citizens → schemes → resources → audits as one neural network. BNGIS is designed to be that connective intelligence.

### 2.3 Objectives
1. Match every citizen automatically to every scheme they are eligible for, ranked by a transparent priority score, and compute an *optimal portfolio* respecting the citizen's application-effort budget.
2. Detect financial anomalies and fraud patterns in department expenditure using multi-layer statistical AI.
3. Guarantee auditability of every AI action through an append-only hash chain.
4. Keep the entire system free and open-source (₹0 build & run cost).

---

## 3. Literature Survey / Background

- **Benford's Law (1938 / Nigrini 2012):** in natural financial datasets the leading digit *d* occurs with probability log₁₀(1+1/d). Manipulated or fabricated ledgers deviate measurably; conformity is judged with χ² tests and Nigrini's Mean Absolute Deviation (MAD) thresholds.
- **Fraud detection:** Isolation Forest / autoencoder ensembles (in the full spec) detect point anomalies; we implement robust z-score detection (median/MAD-based, resistant to outliers) in the MVP, plus graph-level vendor concentration via the Herfindahl–Hirschman Index (HHI).
- **Recommender matching:** scheme-citizen matching is framed as a vector-space retrieval + constraint-satisfaction problem, analogous to job-resume matching systems.
- **Knapsack optimization:** choosing the best set of schemes under an effort budget with mutual-exclusion constraints is a variant of the 0/1 knapsack; the MVP uses a greedy density heuristic (priority/effort), with DP/bitmask planned for larger portfolios.
- **Tamper-evident logs:** hash-chained append-only logs (the idea behind blockchains and certificate transparency) provide integrity without cryptocurrency.

---

## 4. Proposed System — Architecture

```
┌────────────────────────── Browser (SPA: EN/తెలుగు) ──────────────────────────┐
│  Dashboard │ Scheme Matching │ Corruption Shield │ Transparency Chain │ About │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │ REST/JSON
┌───────────────────────────────────▼──────────────────────────────────────────┐
│                     FastAPI application (app/main.py)                        │
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐  ┌────────────┐  │
│  │ Scheme Matcher │  │ Corruption CDS │  │ Blockchain    │  │ Stats      │  │
│  │ (Module 3)     │  │ (Module 4)     │  │ (Module 7)    │  │ (Module 10)│  │
│  └───────┬────────┘  └───────┬────────┘  └───────┬───────┘  └─────┬──────┘  │
│          │ schemes.json      │ seeded txn DB     │ chain.json     │         │
└──────────┴───────────────────┴───────────────────┴────────────────┴─────────┘
```

Every `/api/match` and `/api/corruption/analyze` call automatically appends a block to the transparency chain (Module 7 integration).

---

## 5. Module Design (as implemented)

### 5.1 Citizen Neural Profile (Module 1)
Privacy-first profile (no Aadhaar, no address): age, gender, state, area type, income band, occupation, caste category, land holding, house status, disability and special circumstances (pregnancy, widowhood, girl child, business intent, family head, minority). The profile is vectorized into a **10-dimensional need vector**: `[low_income, rural, farmer, female, senior, student, scst, obc, disabled, biz_intent]`.

### 5.2 Scheme Matching & Delivery Engine (Module 3)
**Algorithm BNGIS-Match:**
1. **Vectorize** citizen (10-d) and every scheme's eligibility signature (same space).
2. **Cosine similarity** `sim = (v·s)/(|v||s|)`.
3. **Hard constraints**: state, age band, gender, occupation, area type, income ceiling, land holding, caste, house status, bank requirement, special flags (ALL) and any-of flags — evaluated per scheme with human-readable blockers.
4. **Priority score** (0–100):
   `P = 0.35·benefit_norm + 0.25·success_prob + 0.20·effort_norm + 0.10·similarity + 0.10·urgency`
   where benefit_norm = min(benefit/₹1L, 1), effort_norm = (6−effort)/5, and urgency is a capped vulnerability score (income < ₹1L +0.35, disability +0.20, widow +0.15, senior +0.15, SC/ST +0.10, kutcha house +0.10).
5. **Portfolio optimization**: greedy knapsack under an application-effort budget (9 points) with mutual-exclusion conflict rules (e.g., PM MUDRA ↔ Stand-Up India).
6. Output: ranked eligible schemes with score breakdown, optimal portfolio, estimated yearly value, and the 5 *nearest misses* with reasons (explainability).

**Database:** 21 real schemes — PM-KISAN, Ayushman Bharat PM-JAY, PMAY-G/U, MGNREGA, NSAP pensions (old-age/widow/disability), PM Matru Vandana, Sukanya Samriddhi, PM Ujjwala, PM Fasal Bima, Kisan Credit Card, Atal Pension, PM MUDRA, Stand-Up India, Post-Matric Scholarship, Merit-cum-Means, and Karnataka's Gruha Lakshmi, Shakti and Gruha Jyothi — each with structured eligibility JSON, documents list, effort score, historical success rate and official URL.

### 5.3 Corruption Detection Shield (Module 4)
Synthetic dataset (seeded, deterministic): ~1,250 transactions, 5 departments, 12+1 vendors, FY 2025-26. Deliberately injected patterns:
- **A. Threshold splitting** — 12 payments just below the ₹50,000 approval threshold to one vendor in PWD.
- **B. Weekend round payments** — 20 round-amount (₹1L/₹1.5L/₹2L) payments on Saturdays in Education.
- **C. Fiscal-year-end spike** — 30 rushed payments in the last two weeks of March in Water Dept.
- **D. Ghost beneficiaries** — near-duplicate names + clustered addresses in a 40-person beneficiary sample.

**Five detection layers:**
1. **Benford's Law** — first-digit distribution vs log₁₀(1+1/d); χ² statistic (df=8, 1% critical value 20.09) and Nigrini MAD conformity bands (<0.006 close … >0.015 non-conformity).
2. **Statistical anomalies** — robust z-score `z = 0.6745(x−median)/MAD`; transactions flagged at |z|>3.5, combined with rule flags (just-below-threshold, round amount, weekend, vendor-pattern).
3. **Vendor network** — amount-share per vendor, top-share table, HHI concentration verdict (>2000 = cartel risk), automatic vendor flagging (≥4 sub-threshold or round payments).
4. **Temporal patterns** — monthly totals with σ-spikes, weekend %, threshold-split %, FY-end concentration.
5. **Ghost beneficiaries** — difflib SequenceMatcher fuzzy name matching (≥86%) + address-cluster counting → duplicate pairs and estimated annual leakage.

**Adaptive scoring:** department risk uses *baseline-excess* features — only the excess over the clean baseline (outlier≈7%, flag≈1%, weekend=0, March≈10%, top-vendor share≈18%) counts toward risk, mirroring the specification's "adaptive threshold based on department baseline". Final risk (0–100) = `0.35·anomaly + 0.30·vendor + 0.20·temporal + 0.15·benford`, graded LOW/MEDIUM/HIGH/CRITICAL.

### 5.4 Transparency Blockchain (Module 7)
Lightweight governance chain — no mining, no cryptocurrency. `hash = SHA-256(json{index, timestamp, type, data, previous_hash, nonce})`. Block types: GENESIS, SERVICE_MATCH, CORRUPTION_AUDIT, DECISION, EXPENDITURE, ASSET. `/api/chain/verify` recomputes every hash and link, detecting any tamper. Persisted to `chain.json`.

### 5.5 Resource Optimization Cortex (Module 2, MVP)
A deterministic dataset of 24 Mysuru-area public facilities (9 hospitals, 8 schools, 7 water works) with coordinates, capacity and live utilization. For a citizen location the engine computes haversine distance, free capacity and quality, and produces an **Allocation Score = 0.55·proximity + 0.30·availability + 0.15·quality** — implementing the spec's accessibility/efficiency/quality constraints in simplified form. When the nearest facility exceeds 85% utilization, the engine issues a **reroute advisory** recommending the next best facility with estimated wait-time savings — the core idea that de-congests public resources (e.g., 34% of hospital beds lie empty while the nearest hospital turns patients away). The frontend renders a live SVG network map with distance rings and AI top-pick routing lines.

### 5.5b Disaster Response Neural Network (Module 5, MVP)
Two engines: (1) **SEIR epidemic simulator** — compartmental model dS/dt=−βSI/N, dE/dt=βSI/N−σE, dI/dt=σE−γI, dR/dt=γI (Euler, dt=1 day) over a 1M-population dengue demo, with four intervention scenarios (0/20/40/60% contact reduction from day 10). The peak infected count is coupled to the Resource Cortex bed network (cross-module integration): peak × 5% hospitalization rate vs. 4,640 regional beds → surplus/strained/deficit verdict with field-hospital deployment advice. (2) **Flood risk scoring** for 12 Karnataka districts: risk = 0.35·rainfall + 0.30·river level + 0.20·terrain + 0.15·historical exposure; displacement estimation via low-lying population share; automatic response resource plans (shelters @400 capacity, water tankers @5 L/person/day, medical teams, boats, vernacular early-warning SMS).

### 5.5c Citizen Voice NLP (Module 8, MVP)
Five-stage pure-Python pipeline: (1) **language detection** via Unicode script ranges (Latin/Devanagari/Telugu/Kannada/Tamil/Bengali) with code-mix handling; (2) **sentiment** via multilingual lexicon with negation flipping; (3) **intent classification** into 9 grievance categories (water, road, electricity, health, education, pension, ration, sanitation, corruption) with weighted keyword matching — corruption terms weighted ×4 so bribe mentions always escalate to the Lokayukta/ACB rather than the line department; (4) **urgency** from emergency lexicon + punctuation + negative sentiment + category bump → P1–P4 priority tickets with SLAs; (5) **department auto-routing** + ticket ID, all recorded on the transparency chain.

### 5.6 Public Dashboard (Module 10)
Real-time KPI cards, SVG line/bar/grouped-bar charts and gauges (hand-rolled — zero CDN dependencies), resource-utilization meters, department risk table, and a language toggle (English ⇄ తెలుగు) demonstrating the multi-language roadmap.

---

## 6. Technology Stack (100% free & open source)

| Layer | Technology |
|---|---|
| Backend | Python 3.13, FastAPI, Uvicorn |
| AI/Analytics | Pure-Python statistics (median/MAD, χ², HHI, cosine similarity, greedy knapsack, SequenceMatcher) |
| Frontend | Vanilla JS SPA, hand-rolled SVG charts, CSS3 (no frameworks) |
| Blockchain | SHA-256 hash chain (hashlib) |
| Testing | pytest (25 engine tests), GitHub Actions CI (3.11/3.12/3.13 + boot smoke test) |
| Packaging | Dockerfile + docker-compose, MIT license |
| Production path (roadmap) | PostgreSQL 16 + PostGIS/pgvector/TimescaleDB, Redis, Kafka, Airflow, Next.js, K3s on Oracle Cloud Free Tier |

---

## 7. Testing & Results

### 7.1 Test cases
| # | Test | Expected | Result |
|---|---|---|---|
| 1 | Rural SC daily-wage woman (₹96k/yr, KA, girl child, family head) | Eligible for PM-JAY, PMAY-G, Shakti, Gruha Lakshmi, MGNREGA, SSY | ✅ 9 schemes, portfolio of 4 |
| 2 | PWD threshold-splitting injection | PWD risk HIGH, anomaly layer dominant, vendor XYZ flagged | ✅ 45.3 HIGH, anomaly 87 |
| 3 | Education weekend round payments | Education risk HIGH, temporal layer elevated | ✅ 47.5 HIGH, temporal 54 |
| 4 | Water Dept FY-end spike | March spike detected (2.7σ), risk MEDIUM | ✅ 41.2 MEDIUM |
| 5 | Clean departments (Health, Rural Dev) | Risk LOW, all fraud layers ≈ 0 | ✅ 8.6 / 8.1 LOW |
| 6 | Ghost duplicates ("Ramesh Kumar" vs "Ramesh Kumaar") | Fuzzy match ≥86% flagged | ✅ 21 pairs detected |
| 7 | Chain integrity | Verify returns valid across all blocks | ✅ |
| 8 | Conflict rule | MUDRA + Stand-Up India never both in portfolio | ✅ |
| 9 | ResourceFinder: Vijayanagar → hospitals | Nearest (PK Sanjivini, 0.67 km, 91% full) flagged; reroute advisory issued to a facility with spare capacity | ✅ |
| 10 | ResourceFinder: clean area (JP Nagar → water) | Nearest reservoir healthy → no reroute, correct top ranking | ✅ |
| 11 | SEIR conservation | S+E+I+R = population at every step (caught & fixed an initial-condition bug) | ✅ |
| 12 | SEIR −60% intervention | Peak collapses >95% vs no-action | ✅ |
| 13 | Flood: Kodagu ranked SEVERE, response plans generated | ✅ |
| 14 | Voice: language detection (en/hi/te/kn) | 4/4 correct | ✅ |
| 15 | Voice: "दलाल 500 रुपये" bribe message | Routed to Lokayukta (corruption ×4 weighting) | ✅ |
| 16 | Voice: emergency message → P1 ticket | ✅ |

### 7.2 Performance
All engines respond in < 300 ms on a single CPU core (no caching needed for demo scale); the audit of 1,250 transactions completes in ~120 ms.

---

## 8. Limitations (honest scoping)
- Transaction & beneficiary data are synthetic (seeded) — no live government feeds.
- 21 schemes indexed vs 2,700+ in reality; eligibility rules simplified.
- Per-department Benford testing needs n>500 transactions for stability — hence the MVP weights Benford at 15% and relies on pattern layers.
- Portfolio optimization is a greedy heuristic, not exact DP (planned).
- Authentication/RBAC not included in MVP.

## 9. Future Scope (from full BNGIS specification)
Module 2 Resource Optimization Cortex (hospital/water/power/transport with Hungarian algorithm + RL), Module 5 Disaster Response Neural Network (SEIR epidemic models, flood prediction), Module 6 Predictive Governance (LSTM + Prophet ensembles), Module 8 12-language Citizen Voice NLP (AI4Bharat/IndicBERT), Module 9 Inter-Department Coordination Brain, PostgreSQL/PostGIS/pgvector persistence, Kafka streaming, Airflow ETL pipelines from data.gov.in, Ollama-served local LLM for citizen Q&A, K3s deployment on Oracle Cloud Free Tier — all at ₹0 cost.

## 10. References
1. BNGIS full project specification (project document, 2024).
2. F. Benford (1938), *The Law of Anomalous Numbers*; M. Nigrini (2012), *Benford's Law: Applications for Forensic Accounting, Auditing, and Fraud Detection*.
3. Government of India scheme portals — pmkisan.gov.in, pmjay.gov.in, pmayg.nic.in, nrega.nic.in, nsap.nic.in, scholarships.gov.in, sevasindhuservices.karnataka.gov.in.
4. FastAPI documentation — https://fastapi.tiangolo.com
5. Indian NPAG/DBT reports on direct benefit transfer leakage and ghost beneficiaries.

---
*Prepared as part of the BNGIS college final-year project. Demo: run `bash run.sh` and open http://localhost:8000*
