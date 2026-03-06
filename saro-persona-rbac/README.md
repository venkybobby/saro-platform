# SARO — Persona-Level RBAC & Admin Provisioning

Smart AI Risk Orchestrator: Role-based access control with 4 personas (Forecaster, Autopsier, Enabler, Evangelist), admin provisioning, multi-role switching, and audit logging.

## Quick Start (Local Dev)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy env template
cp .env.example .env

# 3. Run the server (auto-creates SQLite DB + seeds permissions)
uvicorn main:app --reload --port 8000

# 4. Open API docs
open http://localhost:8000/docs
```

## Run Tests

```bash
pytest tests/ -v
```

## Push to GitHub

```bash
# IMPORTANT: Generate a NEW token (revoke the old one!)
# GitHub → Settings → Developer Settings → Personal Access Tokens → Generate New

git init
git add .
git commit -m "feat: SARO persona-level RBAC with admin provisioning"
git remote add origin https://github.com/YOUR_USERNAME/saro-persona-rbac.git
git branch -M main
git push -u origin main
```

## Deploy to Koyeb

**Option A: Docker**
```bash
# Build & push to Docker Hub or GitHub Container Registry
docker build -f deploy/Dockerfile -t saro-persona-rbac .
docker push YOUR_REGISTRY/saro-persona-rbac

# In Koyeb dashboard: Create Service → Docker → YOUR_REGISTRY/saro-persona-rbac
```

**Option B: GitHub Integration (Recommended)**
1. In Koyeb dashboard → Create Service → GitHub
2. Select your repo → Branch: main
3. Build command: `pip install -r requirements.txt`
4. Run command: `uvicorn main:app --host 0.0.0.0 --port 8000`
5. Set environment variables from `.env.example`
6. Deploy

## Environment Variables for Production

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SARO_JWT_SECRET` | Yes | 256-bit secret for JWT signing |
| `SARO_ADMIN_EMAILS` | Yes | Comma-separated admin emails |
| `SARO_ADMIN_IPS` | No | IP allowlist (default: localhost) |
| `SENDGRID_API_KEY` | No | For magic link emails |
| `STRIPE_SECRET_KEY` | No | For subscription management |

## API Overview

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | None | Health check |
| `/auth/magic-link` | POST | None | Request login link |
| `/admin/tenants` | POST | Admin | Create tenant |
| `/admin/tenants/{id}/users` | POST | Admin | Provision user |
| `/persona/view` | GET | User | Get persona-limited view |
| `/persona/switch-role` | POST | User | Switch active persona |
| `/persona/features/*` | GET | User | Feature-gated endpoints |

## Architecture

```
Login (Magic Link) → JWT Token → RBAC Middleware → Persona View
                                      ↓
                              Permission Matrix (DB)
                                      ↓
                         Feature Gating (allow/deny/summary)
                                      ↓
                              Audit Log (every access)
```

## Persona Permission Matrix

| Feature | Forecaster | Autopsier | Enabler | Evangelist |
|---------|-----------|-----------|---------|------------|
| Regulatory Simulations | FULL | denied | denied | denied |
| Feed Log View | summary | read_only | summary | read_only |
| Incident Audit Logs | denied | FULL | summary | denied |
| Checklist Review | denied | FULL | denied | denied |
| Remediation Workflow | denied | denied | FULL | denied |
| Upload/Input | denied | denied | FULL | denied |
| Ethics/Trust Reports | denied | summary | denied | FULL |
| Policy Chat | denied | denied | denied | FULL |
