"""
SARO — Persona Permission Seed Data
Maps every FR-FOR/AUT/ENA/EVA feature to access levels.
Run via: python -m app.services.seed_permissions
"""

from app.models import SessionLocal, PersonaPermission, Base, engine


# ---------------------------------------------------------------------------
# Permission matrix derived from Persona Spec Section 2
# ---------------------------------------------------------------------------
PERMISSIONS = [
    # ── Forecaster ──────────────────────────────────────────────────────
    ("forecaster", "regulatory_simulations",   "Regulatory Simulations",      "full",      "Forecast",   "Run 6-12 mo gap forecasts with custom priors (FR-FOR-01)"),
    ("forecaster", "feed_log_view",            "Feed Log View",               "summary",   "Forecast",   "View ingested policies/feeds — summary only, no raw export (FR-FOR-02)"),
    ("forecaster", "forecast_metrics",         "Forecast Metrics Dashboard",  "full",      "Metrics",    "Accuracy 85%, gap preempt %, CI width (FR-FOR-03)"),
    ("forecaster", "incident_audit_logs",      "Incident Audit Logs",         "denied",    "Audit",      "Forecaster cannot access audit logs"),
    ("forecaster", "checklist_review",         "Checklist Review",            "denied",    "Audit",      "Forecaster cannot access checklists"),
    ("forecaster", "remediation_workflow",     "Remediation Workflow",        "denied",    "Remediation","Forecaster cannot access remediation"),
    ("forecaster", "upload_input",             "Upload/Input Tools",          "denied",    "Remediation","Forecaster cannot upload"),
    ("forecaster", "ethics_trust_reports",     "Ethics/Trust Reports",        "denied",    "Ethics",     "Forecaster cannot access ethics reports"),
    ("forecaster", "policy_chat",              "Policy Chat Agent",           "denied",    "Ethics",     "Forecaster cannot use policy chat"),

    # ── Autopsier ──────────────────────────────────────────────────────
    ("autopsier", "incident_audit_logs",       "Incident Audit Logs",         "full",      "Audit",      "Deep dive into findings/evidence chains (FR-AUT-01)"),
    ("autopsier", "checklist_review",          "Checklist Review",            "full",      "Audit",      "Interactive checklists with standards mappings (FR-AUT-02)"),
    ("autopsier", "audit_metrics",             "Audit Metrics Dashboard",     "full",      "Metrics",    "Alert precision 88%, false positives <5%, mitigation 70% (FR-AUT-03)"),
    ("autopsier", "regulatory_simulations",    "Regulatory Simulations",      "denied",    "Forecast",   "Autopsier cannot run simulations"),
    ("autopsier", "feed_log_view",             "Feed Log View",               "read_only", "Forecast",   "Autopsier can view feeds read-only"),
    ("autopsier", "remediation_workflow",      "Remediation Workflow",        "denied",    "Remediation","Autopsier cannot remediate"),
    ("autopsier", "upload_input",              "Upload/Input Tools",          "denied",    "Remediation","Autopsier cannot upload"),
    ("autopsier", "ethics_trust_reports",      "Ethics/Trust Reports",        "summary",   "Ethics",     "Autopsier sees summary ethics reports"),
    ("autopsier", "policy_chat",               "Policy Chat Agent",           "denied",    "Ethics",     "Autopsier cannot use policy chat"),

    # ── Enabler ────────────────────────────────────────────────────────
    ("enabler",   "remediation_workflow",      "Remediation Workflow",        "full",      "Remediation","Generate/execute actions from findings (FR-ENA-01)"),
    ("enabler",   "upload_input",              "Upload/Input Tools",          "full",      "Remediation","Submit model outputs for processing (FR-ENA-02)"),
    ("enabler",   "enabler_metrics",           "Enabler Metrics Dashboard",   "full",      "Metrics",    "Effort days, impact scores, ROI $150K (FR-ENA-03)"),
    ("enabler",   "regulatory_simulations",    "Regulatory Simulations",      "denied",    "Forecast",   "Enabler cannot run simulations"),
    ("enabler",   "feed_log_view",             "Feed Log View",               "summary",   "Forecast",   "Enabler sees feed summaries only"),
    ("enabler",   "incident_audit_logs",       "Incident Audit Logs",         "summary",   "Audit",      "Enabler sees audit summaries only"),
    ("enabler",   "checklist_review",          "Checklist Review",            "denied",    "Audit",      "Enabler cannot access checklists"),
    ("enabler",   "ethics_trust_reports",      "Ethics/Trust Reports",        "denied",    "Ethics",     "Enabler cannot access ethics reports"),
    ("enabler",   "policy_chat",               "Policy Chat Agent",           "denied",    "Ethics",     "Enabler cannot use policy chat"),

    # ── Evangelist ─────────────────────────────────────────────────────
    ("evangelist", "ethics_trust_reports",     "Ethics/Trust Reports",        "full",      "Ethics",     "Generate standards-aligned summaries/PDFs (FR-EVA-01)"),
    ("evangelist", "policy_chat",              "Policy Chat Agent",           "full",      "Ethics",     "Query explanations via Claude API (FR-EVA-02)"),
    ("evangelist", "evangelist_metrics",       "Evangelist Metrics Dashboard","full",      "Metrics",    "NPS >75, compliance 82%, trust uplift 70% (FR-EVA-03)"),
    ("evangelist", "regulatory_simulations",   "Regulatory Simulations",      "denied",    "Forecast",   "Evangelist cannot run simulations"),
    ("evangelist", "feed_log_view",            "Feed Log View",               "read_only", "Forecast",   "Evangelist can view feeds read-only"),
    ("evangelist", "incident_audit_logs",      "Incident Audit Logs",         "denied",    "Audit",      "Evangelist cannot access audit logs"),
    ("evangelist", "checklist_review",         "Checklist Review",            "denied",    "Audit",      "Evangelist cannot access checklists"),
    ("evangelist", "remediation_workflow",     "Remediation Workflow",        "denied",    "Remediation","Evangelist cannot remediate"),
    ("evangelist", "upload_input",             "Upload/Input Tools",          "denied",    "Remediation","Evangelist cannot upload — read-only role"),
]


def seed_permissions():
    """Insert/update all persona permissions into DB."""
    db = SessionLocal()
    try:
        # Clear existing and re-seed (idempotent)
        db.query(PersonaPermission).delete()
        for role, fkey, flabel, access, tab, desc in PERMISSIONS:
            db.add(PersonaPermission(
                role=role,
                feature_key=fkey,
                feature_label=flabel,
                access_level=access,
                tab_group=tab,
                description=desc,
            ))
        db.commit()
        print(f"Seeded {len(PERMISSIONS)} persona permissions.")
    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    seed_permissions()
