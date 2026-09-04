"""
BNGIS — Citizen Voice & Feedback Neural Network — MVP
=====================================================
Module 8 of the specification: multi-channel, multi-language grievance NLP.

Pipeline (all pure Python, zero paid APIs):
  1. LANGUAGE DETECTION   — Unicode script ranges (en/hi/te/kn/ta + mixed)
  2. SENTIMENT ANALYSIS   — lexicon + negation handling, -1..+1
  3. INTENT / CATEGORY    — weighted keyword classifier → 9 grievance
                            categories with department auto-routing
  4. URGENCY DETECTION    — emergency lexicon + punctuation + sentiment
  5. TICKET GENERATION    — P1..P4 priority + SLA + officer department
"""

import re
from datetime import datetime, timezone

# --------------------------------------------------------------------------
# 1. Language detection (script ranges)
# --------------------------------------------------------------------------
SCRIPTS = [
    ("te", re.compile(r"[\u0C00-\u0C7F]")),
    ("kn", re.compile(r"[\u0C80-\u0CFF]")),
    ("ta", re.compile(r"[\u0B80-\u0BFF]")),
    ("hi", re.compile(r"[\u0900-\u097F]")),
    ("bn", re.compile(r"[\u0980-\u09FF]")),
]
LANG_NAMES = {"en": "English", "hi": "हिंदी (Hindi)", "te": "తెలుగు (Telugu)",
              "kn": "ಕನ್ನಡ (Kannada)", "ta": "தமிழ் (Tamil)", "bn": "বাংলা (Bengali)",
              "mixed": "Code-mixed"}


def detect_language(text):
    counts = {}
    for code, rx in SCRIPTS:
        counts[code] = len(rx.findall(text))
    latin = len(re.findall(r"[A-Za-z]", text))
    counts["en"] = latin
    total = sum(counts.values()) or 1
    # dominant language if >35% of letters, else mixed
    dom = max(counts, key=counts.get)
    if counts[dom] / total < 0.35 or sum(1 for c in counts.values() if c / total > 0.2) >= 2:
        if sum(v for k, v in counts.items() if v > 0 and k != dom) / total > 0.3:
            return "mixed"
    return dom if counts[dom] > 0 else "en"


# --------------------------------------------------------------------------
# 2. Sentiment lexicons (multilingual)
# --------------------------------------------------------------------------
POSITIVE = [
    "good", "great", "thanks", "thank", "happy", "helpful", "fast", "quick",
    "solved", "resolved", "excellent", "amazing", "kind", "best", "love",
    "ధన్యవాదాలు", "మంచి", "సంతోషం", "త్వరగా",  # te: thanks, good, happy, fast
    "अच्छा", "धन्यवाद", "खुश", "जल्दी",  # hi: good, thanks, happy, quick
    "ಒಳ್ಳೆಯದು", "ಧನ್ಯವಾದ", "ಸಂತೋಷ",  # kn: good, thanks, happy
]
NEGATIVE = [
    "bad", "worst", "terrible", "poor", "slow", "delay", "delayed", "broken",
    "not working", "no water", "corrupt", "bribe", "bribed", "rude", "ignored",
    "problem", "issue", "complaint", "angry", "sad", "pathetic", "useless",
    "చెడు", "ఆలస్యం", "సమస్య", "పనిచేయడంలేదు", "అవినీతి", "లంచం",  # te
    "बुरा", "देरी", "समस्या", "काम नहीं", "भ्रष्टाचार", "रिश्वत",  # hi
    "ಕೆಟ್ಟ", "ವಿಳಂಬ", "ಸಮಸ್ಯೆ", "ಕೆಲಸಮಾಡುತ್ತಿಲ್ಲ", "ಲಂಚ",  # kn
]
NEGATORS = ["not", "no", "never", "లేదు", "కాదు", "नहीं", "ಇಲ್ಲ", "illaa"]
EMERGENCY = [
    "emergency", "urgent", "immediately", "death", "died", "dying", "snake",
    "fire", "accident", "bleeding", "unconscious", "flood", "drown", "electrocuted",
    "అత్యవసరం", "ప్రమాదం", " " "మరణ", "పాము", "నిప్పు", "కరెంటు",  # te
    "आपातकाल", "तुरंत", "मौत", "सांप", "आग", "बाढ़",  # hi
    "ತುರ್ತು", "ಅಪಘಾತ", "ಸಾವು", "ಹಾವು", "ಬೆಂಕಿ", "ಪ್ರವಾಹ",  # kn
]


# --------------------------------------------------------------------------
# 3. Intent categories → department routing
# --------------------------------------------------------------------------
CATEGORIES = {
    "water": {
        "keywords": ["water", "tap", "pipeline", "borewell", "tanker", "drinking water",
                     "నీళ్లు", "కుళాయి", "నీరు", "पानी", "नल", "पाइपलाइन",
                     "ನೀರು", "ಕೊಳವೆ"],
        "department": "Water Supply & Sanitation Board", "sla_days": 3},
    "road": {
        "keywords": ["road", "pothole", "street", "footpath", "bridge", "signal",
                     "రోడ్డు", "గుండ్లు", "వీధి", "सड़क", "गड्ढा", "सड़क",
                     "ರಸ್ತೆ", "ಗುಂಡು"],
        "department": "Public Works Department (PWD)", "sla_days": 7},
    "electricity": {
        "keywords": ["power", "electricity", "transformer", "wire", "current",
                     "outage", "light",
                     "కరెంటు", "విద్యుత్తు", "దీపం", "बिजली", "करेंट", "ट्रांसफार्मर",
                     "ವಿದ್ಯುತ್", "ದೀಪ"],
        "department": "Energy Department (ESCOM)", "sla_days": 2},
    "health": {
        "keywords": ["hospital", "doctor", "medicine", "clinic", "phc", "fever",
                     "dengue", "treatment",
                     "ఆసుపత్రి", "వైద్యుడు", "మందు", "ज़्वर", "अस्पताल", "दवा",
                     "ಆಸ್ಪತ್ರೆ", "ವೈದ್ಯ", "ಔಷಧಿ"],
        "department": "Health & Family Welfare", "sla_days": 2},
    "education": {
        "keywords": ["school", "teacher", "classroom", "midday meal", "textbook",
                     "exam", "college",
                     "పాఠశాల", "ఉపాధ్యాయ", "स्कूल", "शिक्षक", "मध्याह्न भोजन",
                     "ಶಾಲೆ", "ಶಿಕ್ಷಕ"],
        "department": "Education Department", "sla_days": 10},
    "pension": {
        "keywords": ["pension", "old age", "widow", "disable", "allowance",
                     "పెన్షన్", "గంగపెన్షన్", "पेंशन", "वृद्धावस्था",
                     "ಪಿಂಚಣಿ"],
        "department": "Social Welfare (Pension Cell)", "sla_days": 14},
    "ration": {
        "keywords": ["ration", "card", "fair price", "fps", "kerosene", "rice",
                     "రేషన్", "కార్డు", "राशन", "कार्ड", "ಪಡಿತರ", "ಕಾರ್ಡ್"],
        "department": "Food & Civil Supplies", "sla_days": 7},
    "sanitation": {
        "keywords": ["garbage", "trash", "toilet", "drain", "sewage", "smell",
                     "waste", "చెత్త", "మురుగునీరు", "మరుగుదొడ్లు",
                     "कचरा", "शौचालय", "नाली", "ಕಸ", "ಶೌಚಾಲಯ", "ಚರಂಡಿ"],
        "department": "Municipal Corporation (Swachh Bharat Cell)", "sla_days": 5},
    "corruption": {
        "keywords": ["bribe", "corrupt", "middleman", "agent fee", "commission",
                     "officer demanded", "లంచం", "అవినీతి", "బట్టబయలు",
                     "रिश्वत", "भ्रष्टाचार", "दलाल", "ಲಂಚ", "ಭ್ರಷ್ಟಾಚಾರ"],
        "department": "Lokayukta / Anti-Corruption Bureau", "sla_days": 21},
}
OTHER = {"department": "General Grievance Cell", "sla_days": 10}

URGENCY_BUMP = {"health": 0.15, "water": 0.10, "electricity": 0.10}


def analyze_message(text):
    """Full NLP pipeline for one grievance message."""
    text_lower = text.lower()
    words = set(re.findall(r"[\w\u0900-\u0DFF]+", text_lower))

    # language
    lang = detect_language(text)

    # sentiment with simple negation flipping
    score = 0
    hits = 0
    for i, w in enumerate(NEGATIVE + POSITIVE):
        wl = w.lower()
        if wl in text_lower:
            polarity = -1 if w in NEGATIVE else 1
            # check negator immediately before
            window = text_lower[max(0, text_lower.index(wl) - 12):text_lower.index(wl)]
            if any(n in window for n in NEGATORS):
                polarity *= -0.7
            score += polarity
            hits += 1
    sentiment = round(max(-1, min(1, score / max(hits, 1))), 2) if hits else 0.0
    sentiment_label = ("ANGRY/NEGATIVE" if sentiment <= -0.4
                       else "NEGATIVE" if sentiment < -0.05
                       else "NEUTRAL" if sentiment <= 0.05
                       else "POSITIVE")

    # intent / category scoring
    cat_scores = {}
    matched = {}
    for cat, cfg in CATEGORIES.items():
        s = 0
        found = []
        for kw in cfg["keywords"]:
            if kw.lower() in text_lower:
                # corruption terms are highly diagnostic — always outweigh
                # generic category words (a bribe mention must reach Lokayukta)
                weight = 4 if cat == "corruption" else (1 if len(kw) < 5 else 2)
                s += weight
                found.append(kw)
        if s:
            cat_scores[cat] = s
            matched[cat] = found
    category = max(cat_scores, key=cat_scores.get) if cat_scores else "other"
    cfg = CATEGORIES.get(category, OTHER)

    # urgency
    urgency = 0.0
    emg_hits = [e for e in EMERGENCY if e and e in text_lower]
    urgency += min(0.25 * len(emg_hits), 0.6)
    urgency += 0.1 if "!" in text else 0.0
    urgency += max(0.0, -sentiment) * 0.25          # angrier → more urgent
    urgency += URGENCY_BUMP.get(category, 0.0)
    urgency = round(min(urgency, 1.0), 2)

    # priority + SLA
    if urgency >= 0.65:
        priority, sla = "P1 — EMERGENCY", 1
    elif urgency >= 0.4:
        priority, sla = "P2 — HIGH", cfg["sla_days"] - 2
    elif urgency >= 0.2:
        priority, sla = "P3 — NORMAL", cfg["sla_days"]
    else:
        priority, sla = "P4 — FEEDBACK", cfg["sla_days"] + 5

    ticket = "BNG-" + datetime.now(timezone.utc).strftime("%y%m%d%H%M%S")

    return {
        "ticket": ticket,
        "language": lang,
        "language_name": LANG_NAMES.get(lang, lang),
        "sentiment": sentiment,
        "sentiment_label": sentiment_label,
        "category": category,
        "matched_keywords": matched.get(category, [])[:6],
        "department": cfg["department"],
        "urgency": urgency,
        "priority": priority,
        "sla_days": max(sla, 1),
        "recommended_action": (
            "Immediate field dispatch + call citizen within 1 hour"
            if priority.startswith("P1") else
            f"Assign to {cfg['department']}, resolve within {max(sla,1)} days "
            f"+ status SMS to citizen"),
    }


# --------------------------------------------------------------------------
# Sample multilingual feed + analytics
# --------------------------------------------------------------------------
SAMPLES = [
    ("te", "మా వీధిలో మూడు రోజులుగా నీళ్లు రావడం లేదు, త్వరగా చూడండి"),
    ("en", "No water supply in our street for 3 days, please solve immediately!"),
    ("kn", "ನಮ್ಮ ಪ್ರದೇಶದಲ್ಲಿ ದೊಡ್ಡ ಗುಂಡು ಇದೆ, ರಸ್ತೆ ಅಪಘಾತವಾಗುತ್ತಿದೆ ತುರ್ತು"),
    ("hi", "पेंशन तीन महीने से नहीं आई, बुढ़ापे में परेशानी हो रही है"),
    ("te", "రోడ్డు పై పెద్ద గుండు ఉంది, ప్రమాదం జరుగుతుంది, అత్యవసరంగా సరిచేయండి"),
    ("en", "The PHC doctor was very kind and medicine was given quickly, thanks"),
    ("hi", "राशन कार्ड में नाम जुड़ने के लिए दलाल 500 रुपये मांग रहा है"),
    ("kn", "ಆಸ್ಪತ್ರೆಯಲ್ಲಿ ಔಷಧಿ ಇಲ್ಲ, ಜ್ವರ ಬಂದಿದೆ ತುರ್ತು ಸಹಾಯ ಬೇಕು"),
    ("en", "Street lights not working for a week, area is dark at night"),
    ("te", "మా పాఠశాలలో ఉపాధ్యాయులు లేరు, పిల్లలకు తరగతులు లేవు"),
    ("en", "Garbage not collected for 5 days, whole street smells terrible"),
    ("hi", "बिजली कटौती रोज़ हो रही है, पढ़ाई प्रभावित हो रही है"),
    ("te", "మరుగుదొడ్లు పనిచేయడం లేదు, మురుగునీరు వీధుల్లో నిలిచింది"),
    ("kn", "ವಿದ್ಯುತ್ ಟ್ರಾನ್ಸ್ಫಾರ್ಮರ್ ಸ್ಫೋಟಗೊಂಡಿದೆ, ಅಪಘಾತ ಆಗಿದೆ ತುರ್ತು"),
]


def feed_analytics():
    """Pre-analyzed sample feed + aggregate insights (Module 8.4)."""
    items = []
    for lang, msg in SAMPLES:
        a = analyze_message(msg)
        a["message"] = msg
        items.append(a)

    cat_counts = {}
    sentiment_sum = 0
    p1_count = 0
    for it in items:
        cat_counts[it["category"]] = cat_counts.get(it["category"], 0) + 1
        sentiment_sum += it["sentiment"]
        if it["priority"].startswith("P1"):
            p1_count += 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "items": items,
        "analytics": {
            "total": len(items),
            "languages": sorted(set(i["language"] for i in items)),
            "avg_sentiment": round(sentiment_sum / len(items), 2),
            "p1_emergencies": p1_count,
            "category_counts": dict(sorted(cat_counts.items(),
                                           key=lambda x: -x[1])),
        },
    }
