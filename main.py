"""
SARO Persona-Level RBAC — FastAPI Application
===============================================
Main app with all persona RBAC routes mounted.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.database import engine
from models.db_models import Base
from api.persona_routes import router as persona_router
from api.access_routes import router as access_router
from api.domain_routes import router as domain_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("saro.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup (dev mode). Use Alembic migrations in prod."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("SARO Persona RBAC — tables created / verified")
    yield
    await engine.dispose()


app = FastAPI(
    title="SARO Persona RBAC API",
    description=(
        "Smart AI Risk Orchestrator — Persona-level role-based access control. "
        "FR-005: Persona Limitation | FR-003: Multi-role assignment (up to 4) | "
        "FR-007: Persona-limited report access | NFR-002: Full audit logging."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — adjust origins for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://saro.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(persona_router)
app.include_router(access_router)
app.include_router(domain_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "saro-persona-rbac"}
