"""Policy Library, Feed Log & Upload API"""
from fastapi import APIRouter
from datetime import datetime, timedelta
import uuid, random

router = APIRouter()
_policies = []
_feed_log = []

SAMPLE_POLICIES = [
    {"title": "EU AI Act — Article 9: Risk Management Systems", "source": "EUR-Lex", "jurisdiction": "EU", "regulation": "EU AI Act", "risk_score": 0.82, "status": "reviewed", "doc_type": "regulation"},
    {"title": "NIST AI RMF 2.0 — MAP Function Controls", "source": "NIST", "jurisdiction": "US", "regulation": "NIST AI RMF", "risk_score": 0.61, "status": "reviewed", "doc_type": "guideline"},
    {"title": "UK AI Whitepaper — High-Risk System Criteria", "source": "GOV.UK", "jurisdiction": "UK", "regulation": "UK AI Bill", "risk_score": 0.74, "status": "pending_review", "doc_type": "whitepaper"},
    {"title": "FDA Guidance on AI/ML-Based SaMD", "source": "FDA RSS", "jurisdiction": "US", "regulation": "FDA SaMD", "risk_score": 0.91, "status": "flagged", "doc_type": "guidance"},
    {"title": "MAS TREx Framework v2 — Model Risk", "source": "MAS", "jurisdiction": "SG", "regulation": "MAS TREx", "risk_score": 0.68, "status": "reviewed", "doc_type": "standard"},
    {"title": "China AIGC Regulation — Article 4 Obligations", "source": "CAC", "jurisdiction": "CN", "regulation": "China AIGC", "risk_score": 0.77, "status": "reviewed", "doc_type": "regulation"},
    {"title": "ISO 42001:2023 — Annex B Bias Testing Controls", "source": "ISO", "jurisdiction": "GLOBAL", "regulation": "ISO 42001", "risk_score": 0.58, "status": "reviewed", "doc_type": "standard"},
    {"title": "GDPR Article 22 — Automated Decision-Making", "source": "EUR-Lex", "jurisdiction": "EU", "regulation": "GDPR", "risk_score": 0.79, "status": "reviewed", "doc_type": "regulation"},
]

SAMPLE_FEEDS = [
    {"feed": "EUR-Lex Official Journal", "jurisdiction": "EU", "regulation": "EU AI Act", "headline": "New implementing acts published for Article 52 transparency obligations", "status": "reviewed", "is_new": True, "impact": "high"},
    {"feed": "NIST AI RMF Updates", "jurisdiction": "US", "regulation": "NIST AI RMF", "headline": "NIST releases AI RMF Playbook v1.1 with 45 new subcategory actions", "status": "reviewed", "is_new": True, "impact": "medium"},
    {"feed": "GOV.UK Policy Papers", "jurisdiction": "UK", "regulation": "UK AI Bill", "headline": "UK AI Safety Institute publishes evaluation framework for frontier models", "status": "pending_review", "is_new": True, "impact": "high"},
    {"feed": "FDA MedTech Digest", "jurisdiction": "US", "regulation": "FDA SaMD", "headline": "FDA issues draft guidance on predetermined change control plans for AI/ML", "status": "flagged", "is_new": True, "impact": "critical"},
    {"feed": "ISO Standards Bulletin", "jurisdiction": "GLOBAL", "regulation": "ISO 42001", "headline": "ISO 42001:2023 Annex B controls updated — additional bias testing requirements", "status": "reviewed", "is_new": False, "impact": "medium"},
    {"feed": "MAS TREx Feed", "jurisdiction": "SG", "regulation": "MAS TREx", "headline": "MAS issues revised guidelines on model risk governance for AI systems", "status": "pending_review", "is_new": False, "impact": "high"},
]

def _seed():
    if not _policies:
        for s in SAMPLE_POLICIES:
            _policies.append({**s, "policy_id": f"POL-{str(uuid.uuid4())[:8].upper()}", "entities": ["AI System", s["regulation"], s["jurisdiction"]], "ingested_at": (datetime.utcnow() - timedelta(days=random.randint(1,30))).isoformat(), "word_count": random.randint(800,8000)})
    if not _feed_log:
        for f in SAMPLE_FEEDS:
            _feed_log.append({**f, "feed_id": f"FEED-{str(uuid.uuid4())[:8].upper()}", "fetched_at": (datetime.utcnow() - timedelta(hours=random.randint(1,48))).isoformat(), "risk_score": round(random.uniform(0.5,0.95),2)})

@router.get("/policies")
async def list_policies(jurisdiction: str = "ALL", status: str = "ALL"):
    _seed()
    result = _policies
    if jurisdiction != "ALL": result = [p for p in result if p["jurisdiction"] == jurisdiction]
    if status != "ALL": result = [p for p in result if p["status"] == status]
    return {"policies": result, "total": len(result)}

@router.post("/policies/upload")
async def upload_policy(payload: dict):
    text = payload.get("content", "")
    risk_kw = {"high-risk": 0.8, "bias": 0.7, "discrimination": 0.9, "surveillance": 0.95, "facial recognition": 0.9, "transparency": 0.5, "prohibited": 0.95, "penalty": 0.7, "fundamental rights": 0.85}
    found = {k: v for k,v in risk_kw.items() if k in text.lower()}
    risk_score = min(0.99, max(found.values(), default=round(random.uniform(0.2,0.6),2)))
    policy = {"policy_id": f"POL-{str(uuid.uuid4())[:8].upper()}", "title": payload.get("title","Uploaded Policy"), "jurisdiction": payload.get("jurisdiction","EU"), "regulation": payload.get("regulation","General"), "doc_type": payload.get("doc_type","policy"), "risk_score": risk_score, "risk_tags": [{"tag": k,"probability": v} for k,v in list(found.items())[:5]], "entities": ["AI System", payload.get("jurisdiction","EU"), payload.get("regulation","General")], "status": "pending_review", "word_count": len(text.split()), "content_preview": text[:300]+"..." if len(text)>300 else text, "ingested_at": datetime.utcnow().isoformat(), "source": "User Upload"}
    _seed(); _policies.append(policy)
    return policy

@router.put("/policies/{policy_id}/review")
async def review_policy(policy_id: str, payload: dict):
    _seed()
    for p in _policies:
        if p["policy_id"] == policy_id:
            p["status"] = payload.get("status","reviewed"); p["reviewed_at"] = datetime.utcnow().isoformat(); p["reviewer_notes"] = payload.get("notes","")
            return p
    return {"error": "Not found"}

@router.get("/feed-log")
async def get_feed_log(jurisdiction: str = "ALL"):
    _seed()
    result = _feed_log if jurisdiction == "ALL" else [f for f in _feed_log if f["jurisdiction"] == jurisdiction]
    return {"feeds": result, "total": len(result), "new_count": sum(1 for f in result if f["is_new"]), "last_polled": (datetime.utcnow()-timedelta(minutes=12)).isoformat(), "next_poll": (datetime.utcnow()+timedelta(minutes=48)).isoformat()}

@router.post("/feed-log/{feed_id}/approve")
async def approve_feed(feed_id: str):
    _seed()
    for f in _feed_log:
        if f["feed_id"] == feed_id:
            f["status"] = "reviewed"; f["is_new"] = False; f["approved_at"] = datetime.utcnow().isoformat()
            return {"approved": True, "feed_id": feed_id}
    return {"error": "Not found"}
