"""
SARO — Test Suite for Persona RBAC
Covers: admin provisioning, persona views, role switching, feature gating, deny tests.
Run: pytest tests/test_persona_rbac.py -v
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.models import Base, Tenant, TenantConfig, User, PersonaPermission
from app.models.database import get_db
from app.middleware.rbac import create_token
from app.services.seed_permissions import PERMISSIONS

# ---------------------------------------------------------------------------
# Test DB setup (SQLite in-memory)
# ---------------------------------------------------------------------------
TEST_DB_URL = "sqlite:///./test_saro.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


# Import app and override DB
from main import app
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables and seed before each test, drop after."""
    Base.metadata.create_all(bind=test_engine)
    db = TestSession()
    db.query(PersonaPermission).delete()
    for role, fkey, flabel, access, tab, desc in PERMISSIONS:
        db.add(PersonaPermission(role=role, feature_key=fkey, feature_label=flabel,
                                  access_level=access, tab_group=tab, description=desc))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_tenant_and_token():
    db = TestSession()
    tenant = Tenant(name="Test Corp", sector="finance")
    db.add(tenant)
    db.flush()
    config = TenantConfig(tenant_id=tenant.tenant_id, default_roles=["forecaster"], tier="pro")
    db.add(config)
    admin_user = User(
        tenant_id=tenant.tenant_id,
        email="admin@saro.ai",
        roles=["admin"],
        primary_role="admin",
        is_admin=True,
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    token = create_token(admin_user)
    return str(tenant.tenant_id), token, db, admin_user


def _create_persona_user(db, tenant_id, email, roles, primary_role):
    user = User(
        tenant_id=str(tenant_id),
        email=email,
        roles=roles,
        primary_role=primary_role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, create_token(user)


# ===========================================================================
# 1. Health & Root
# ===========================================================================
class TestHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "forecaster" in r.json()["personas"]


# ===========================================================================
# 2. Admin Provisioning (FR-001 to FR-004)
# ===========================================================================
class TestAdminProvisioning:
    def test_create_tenant(self, client, admin_tenant_and_token):
        tid, token, db, _ = admin_tenant_and_token
        r = client.post("/admin/tenants", json={"name": "NewCo", "sector": "healthcare"},
                        headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["name"] == "NewCo"

    def test_provision_user(self, client, admin_tenant_and_token):
        tid, token, db, _ = admin_tenant_and_token
        r = client.post(f"/admin/tenants/{tid}/users",
                        json={"email": "forecaster@test.com", "roles": ["forecaster", "enabler"]},
                        headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert data["roles"] == ["forecaster", "enabler"]
        assert data["primary_role"] == "forecaster"

    def test_provision_rejects_invalid_role(self, client, admin_tenant_and_token):
        tid, token, db, _ = admin_tenant_and_token
        r = client.post(f"/admin/tenants/{tid}/users",
                        json={"email": "bad@test.com", "roles": ["hacker"]},
                        headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 422

    def test_provision_rejects_duplicate(self, client, admin_tenant_and_token):
        tid, token, db, _ = admin_tenant_and_token
        body = {"email": "dup@test.com", "roles": ["forecaster"]}
        client.post(f"/admin/tenants/{tid}/users", json=body,
                    headers={"Authorization": f"Bearer {token}"})
        r = client.post(f"/admin/tenants/{tid}/users", json=body,
                        headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 409

    def test_non_admin_denied(self, client, admin_tenant_and_token):
        tid, token, db, _ = admin_tenant_and_token
        user, user_token = _create_persona_user(db, tid, "nonadmin@test.com", ["forecaster"], "forecaster")
        r = client.post("/admin/tenants", json={"name": "Fail"},
                        headers={"Authorization": f"Bearer {user_token}"})
        assert r.status_code == 403


# ===========================================================================
# 3. Persona Views (FR-005)
# ===========================================================================
class TestPersonaViews:
    def test_forecaster_view(self, client, admin_tenant_and_token):
        tid, _, db, _ = admin_tenant_and_token
        user, token = _create_persona_user(db, tid, "fc@test.com", ["forecaster"], "forecaster")
        r = client.get("/persona/view", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert data["role"] == "forecaster"
        feature_keys = [f["feature_key"] for f in data["features"]]
        assert "regulatory_simulations" in feature_keys
        assert "incident_audit_logs" not in feature_keys
        assert "remediation_workflow" not in feature_keys

    def test_autopsier_view(self, client, admin_tenant_and_token):
        tid, _, db, _ = admin_tenant_and_token
        user, token = _create_persona_user(db, tid, "aut@test.com", ["autopsier"], "autopsier")
        r = client.get("/persona/view", headers={"Authorization": f"Bearer {token}"})
        data = r.json()
        feature_keys = [f["feature_key"] for f in data["features"]]
        assert "incident_audit_logs" in feature_keys
        assert "checklist_review" in feature_keys
        assert "regulatory_simulations" not in feature_keys

    def test_enabler_view(self, client, admin_tenant_and_token):
        tid, _, db, _ = admin_tenant_and_token
        user, token = _create_persona_user(db, tid, "en@test.com", ["enabler"], "enabler")
        r = client.get("/persona/view", headers={"Authorization": f"Bearer {token}"})
        data = r.json()
        feature_keys = [f["feature_key"] for f in data["features"]]
        assert "remediation_workflow" in feature_keys
        assert "upload_input" in feature_keys
        assert "policy_chat" not in feature_keys

    def test_evangelist_view(self, client, admin_tenant_and_token):
        tid, _, db, _ = admin_tenant_and_token
        user, token = _create_persona_user(db, tid, "ev@test.com", ["evangelist"], "evangelist")
        r = client.get("/persona/view", headers={"Authorization": f"Bearer {token}"})
        data = r.json()
        feature_keys = [f["feature_key"] for f in data["features"]]
        assert "ethics_trust_reports" in feature_keys
        assert "policy_chat" in feature_keys
        assert "remediation_workflow" not in feature_keys
        assert "upload_input" not in feature_keys

    def test_metrics_included(self, client, admin_tenant_and_token):
        tid, _, db, _ = admin_tenant_and_token
        user, token = _create_persona_user(db, tid, "m@test.com", ["forecaster"], "forecaster")
        r = client.get("/persona/view", headers={"Authorization": f"Bearer {token}"})
        data = r.json()
        assert len(data["metrics"]) > 0
        assert data["metrics"][0]["tooltip"]


# ===========================================================================
# 4. Role Switching
# ===========================================================================
class TestRoleSwitching:
    def test_switch_to_assigned_role(self, client, admin_tenant_and_token):
        tid, _, db, _ = admin_tenant_and_token
        user, token = _create_persona_user(db, tid, "multi@test.com",
                                            ["forecaster", "enabler"], "forecaster")
        r = client.post("/persona/switch-role", json={"primary_role": "enabler"},
                        headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["role"] == "enabler"

    def test_switch_to_unassigned_role_denied(self, client, admin_tenant_and_token):
        tid, _, db, _ = admin_tenant_and_token
        user, token = _create_persona_user(db, tid, "single@test.com",
                                            ["forecaster"], "forecaster")
        r = client.post("/persona/switch-role", json={"primary_role": "autopsier"},
                        headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403


# ===========================================================================
# 5. Feature Gating — Deny Tests
# ===========================================================================
class TestFeatureGating:
    def test_forecaster_can_access_simulations(self, client, admin_tenant_and_token):
        tid, _, db, _ = admin_tenant_and_token
        user, token = _create_persona_user(db, tid, "fg1@test.com", ["forecaster"], "forecaster")
        r = client.get("/persona/features/regulatory-simulations",
                       headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    def test_forecaster_denied_audit_logs(self, client, admin_tenant_and_token):
        tid, _, db, _ = admin_tenant_and_token
        user, token = _create_persona_user(db, tid, "fg2@test.com", ["forecaster"], "forecaster")
        r = client.get("/persona/features/incident-audit-logs",
                       headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    def test_forecaster_denied_remediation(self, client, admin_tenant_and_token):
        tid, _, db, _ = admin_tenant_and_token
        user, token = _create_persona_user(db, tid, "fg3@test.com", ["forecaster"], "forecaster")
        r = client.get("/persona/features/remediation-workflow",
                       headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    def test_autopsier_can_access_audit_logs(self, client, admin_tenant_and_token):
        tid, _, db, _ = admin_tenant_and_token
        user, token = _create_persona_user(db, tid, "fg4@test.com", ["autopsier"], "autopsier")
        r = client.get("/persona/features/incident-audit-logs",
                       headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    def test_enabler_denied_policy_chat(self, client, admin_tenant_and_token):
        tid, _, db, _ = admin_tenant_and_token
        user, token = _create_persona_user(db, tid, "fg5@test.com", ["enabler"], "enabler")
        r = client.get("/persona/features/policy-chat",
                       headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    def test_evangelist_can_access_policy_chat(self, client, admin_tenant_and_token):
        tid, _, db, _ = admin_tenant_and_token
        user, token = _create_persona_user(db, tid, "fg6@test.com", ["evangelist"], "evangelist")
        r = client.get("/persona/features/policy-chat",
                       headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    def test_evangelist_denied_upload(self, client, admin_tenant_and_token):
        tid, _, db, _ = admin_tenant_and_token
        user, token = _create_persona_user(db, tid, "fg7@test.com", ["evangelist"], "evangelist")
        r = client.get("/persona/features/upload-input",
                       headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    def test_unauthenticated_denied(self, client):
        r = client.get("/persona/view")
        assert r.status_code == 401


# ===========================================================================
# 6. Auth Flow
# ===========================================================================
class TestAuth:
    def test_magic_link_known_user(self, client, admin_tenant_and_token):
        tid, _, db, admin = admin_tenant_and_token
        r = client.post("/auth/magic-link", json={"email": "admin@saro.ai"})
        assert r.status_code == 200
        assert "token" in r.json()

    def test_magic_link_unknown_email(self, client):
        r = client.post("/auth/magic-link", json={"email": "nobody@test.com"})
        assert r.status_code == 200
        assert "token" not in r.json()
