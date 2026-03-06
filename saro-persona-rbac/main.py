"""
SARO — FastAPI Application Entry Point
Smart AI Risk Orchestrator: Persona-Level RBAC + Admin Provisioning
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import Base, engine
from app.api import admin_router, persona_router, auth_router
from app.services.seed_permissions import seed_permissions

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("saro")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables + seed permissions."""
    logger.info("SARO starting — creating tables & seeding permissions...")
    Base.metadata.create_all(bind=engine)
    seed_permissions()
    logger.info("SARO ready.")
    yield
    logger.info("SARO shutting down.")


app = FastAPI(
    title="SARO — Smart AI Risk Orchestrator",
    description=(
        "Persona-level RBAC API with admin provisioning. "
        "4 personas (Forecaster, Autopsier, Enabler, Evangelist) with "
        "role-limited views, contextual metrics, and audit logging."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for Streamlit / frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(persona_router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "saro-persona-rbac", "version": "1.0.0"}


@app.get("/")
async def root():
    return {
        "service": "SARO — Smart AI Risk Orchestrator",
        "docs": "/docs",
        "personas": ["forecaster", "autopsier", "enabler", "evangelist"],
        "admin": "/admin/tenants",
    }
