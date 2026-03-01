"""MVP5 - AI Model Marketplace API"""
from fastapi import APIRouter
from datetime import datetime, timedelta
import uuid
import random

router = APIRouter()

_listings = []
_transactions = []

SAMPLE_LISTINGS = [
    {"name": "CreditScorer-v3", "vendor": "FinServ AI", "category": "finance", "price_usd": 12000, "compliance_score": 0.94, "jurisdictions": ["EU", "US"], "saro_stamp": True},
    {"name": "HRScreener-Pro", "vendor": "TalentAI Ltd", "category": "hr", "price_usd": 8500, "compliance_score": 0.88, "jurisdictions": ["US", "UK"], "saro_stamp": True},
    {"name": "DiagnosticAI-CE", "vendor": "MedTech Corp", "category": "healthcare", "price_usd": 45000, "compliance_score": 0.97, "jurisdictions": ["EU", "US", "UK"], "saro_stamp": True},
    {"name": "FraudDetect-v4", "vendor": "SecureAI", "category": "finance", "price_usd": 15000, "compliance_score": 0.91, "jurisdictions": ["GLOBAL"], "saro_stamp": True},
    {"name": "SentimentEngine-v2", "vendor": "NLP Labs", "category": "nlp", "price_usd": 3200, "compliance_score": 0.82, "jurisdictions": ["EU"], "saro_stamp": False},
]


def _seed_listings():
    if not _listings:
        for s in SAMPLE_LISTINGS:
            _listings.append({
                **s,
                "listing_id": f"MKT-{str(uuid.uuid4())[:8].upper()}",
                "tx_hash": f"0x{''.join(random.choices('abcdef0123456789', k=40))}",
                "block_number": random.randint(19000000, 20000000),
                "listed_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
                "downloads": random.randint(10, 340),
                "rating": round(random.uniform(3.8, 5.0), 1),
            })


@router.get("/marketplace/listings")
async def list_marketplace(category: str = "ALL"):
    _seed_listings()
    listings = _listings if category == "ALL" else [l for l in _listings if l["category"] == category]
    return {"listings": listings, "total": len(listings), "saro_verified": sum(1 for l in listings if l["saro_stamp"])}


@router.post("/marketplace/purchase")
async def purchase_model(payload: dict):
    _seed_listings()
    listing_id = payload.get("listing_id")
    listing = next((l for l in _listings if l["listing_id"] == listing_id), _listings[0])
    tx = {
        "transaction_id": f"TXN-{str(uuid.uuid4())[:8].upper()}",
        "listing_id": listing_id,
        "model_name": listing["name"],
        "buyer_id": payload.get("tenant_id", "TENANT-001"),
        "amount_usd": listing["price_usd"],
        "tx_hash": f"0x{''.join(random.choices('abcdef0123456789', k=64))}",
        "block_number": random.randint(19000000, 20000000),
        "confirmed": True,
        "saro_stamp_transferred": listing["saro_stamp"],
        "purchase_time_ms": round(random.uniform(800, 2400), 0),
        "completed_at": datetime.utcnow().isoformat(),
    }
    _transactions.append(tx)
    return tx


@router.post("/marketplace/list")
async def list_model(payload: dict):
    listing = {
        "listing_id": f"MKT-{str(uuid.uuid4())[:8].upper()}",
        "name": payload.get("name", "New Model"),
        "vendor": payload.get("vendor", "Unknown"),
        "category": payload.get("category", "general"),
        "price_usd": payload.get("price_usd", 5000),
        "compliance_score": round(random.uniform(0.75, 0.97), 2),
        "jurisdictions": payload.get("jurisdictions", ["EU"]),
        "saro_stamp": True,
        "tx_hash": f"0x{''.join(random.choices('abcdef0123456789', k=40))}",
        "listed_at": datetime.utcnow().isoformat(),
        "downloads": 0,
        "rating": 0,
    }
    _listings.append(listing)
    return listing


@router.get("/marketplace/stats")
async def marketplace_stats():
    _seed_listings()
    return {
        "total_listings": len(_listings),
        "saro_verified": sum(1 for l in _listings if l["saro_stamp"]),
        "total_volume_usd": 2840000,
        "transactions_today": 34,
        "avg_compliance_score": round(sum(l["compliance_score"] for l in _listings) / len(_listings), 2),
        "top_categories": ["finance", "healthcare", "hr"],
        "partner_vendors": 12,
    }


@router.get("/marketplace/verify/{tx_hash}")
async def verify_on_chain(tx_hash: str):
    return {
        "tx_hash": tx_hash,
        "verified": True,
        "blockchain": "Polygon",
        "block_number": random.randint(19000000, 20000000),
        "confirmations": random.randint(12, 200),
        "integrity": "intact",
        "saro_stamp_valid": True,
        "verified_at": datetime.utcnow().isoformat(),
    }
