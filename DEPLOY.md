# SARO Platform — Railway Deployment Guide
### Live demo URL in 30 minutes · Free tier · No credit card required

---

## Option A — Fastest: One-Command Deploy

```bash
# From the saro-platform directory
bash scripts/railway-deploy.sh
```

This script handles everything: Railway login, project creation, backend + frontend deployment, and demo data seeding. Skip to **After Deployment** once done.

---

## Option B — Manual Step-by-Step (15 min)

### Prerequisites (2 min)

**Install Railway CLI:**
```bash
# macOS / Linux
curl -fsSL https://railway.app/install.sh | sh

# Or via npm
npm install -g @railway/cli

# Windows
iwr -useb https://railway.app/install.ps1 | iex
```

**Create a free Railway account:**  
→ https://railway.app (GitHub login works instantly)

---

### Step 1 — Login (1 min)

```bash
railway login
# Opens browser for OAuth — click Authorize
```

---

### Step 2 — Create GitHub Repo (3 min)

Railway deploys from GitHub. Create a new repo and push:

```bash
cd saro-platform

git init
git add -A
git commit -m "SARO Platform v4.0.0 - initial deployment"

# Create repo on GitHub (visit github.com/new), then:
git remote add origin https://github.com/YOUR_USERNAME/saro-platform.git
git push -u origin main
```

---

### Step 3 — Deploy Backend (5 min)

1. Go to **https://railway.app/new**
2. Click **"Deploy from GitHub repo"**
3. Select your `saro-platform` repo
4. Set **Root Directory** to: `backend`
5. Railway auto-detects Python → click **Deploy**

**Set environment variables** in Railway dashboard → Variables tab:
```
SECRET_KEY    = any-random-string-here
DEBUG         = false
PORT          = 8000
```

6. Once deployed, copy your backend URL from Settings:
   `https://saro-backend-XXXX.up.railway.app`

---

### Step 4 — Deploy Frontend (5 min)

1. In your Railway project, click **"New Service"** → **"GitHub Repo"**
2. Select same `saro-platform` repo
3. Set **Root Directory** to: `frontend`
4. Set environment variable:
   ```
   VITE_API_URL = https://saro-backend-XXXX.up.railway.app
   ```
5. Click **Deploy**

Your frontend URL:  
`https://saro-frontend-XXXX.up.railway.app`

---

### Step 5 — Seed Demo Data (3 min)

```bash
# Install the HTTP client
pip install httpx

# Run the seeder against your live Railway backend
python3 seed_demo.py --url https://saro-backend-XXXX.up.railway.app
```

Expected output:
```
◈ MVP1 — Seeding Regulatory Documents
  ✓ EU AI Act — Article 9: Risk Management...  | risk=67% | entities=2
  ✓ NIST AI Risk Management Framework 2.0...   | risk=54% | entities=3
  ... (8 more documents)

◉ MVP2 — Running AI Model Audits  
  ✓ CreditScorer-v2     | AUDIT-A1B2C3D4 | risk=high     | score=72%
  ✓ HRScreener-v1       | AUDIT-E5F6G7H8 | risk=critical | score=55%
  ... (8 more audits)

◎ MVP3 — Provisioning Enterprise Tenants
  ✓ Deloitte AI Risk Practice  | TEN-XXXXXXXX | key=saro-live-...
  ... (4 more tenants)

◐ MVP4 — Running Guardrail Tests
  BLOCKED | HRScreener-v1   | violations=1 | 0.09ms
  PASSED  | FraudDetect-v3  | violations=0 | 0.07ms
  ... (6 more tests)

✓ Demo Seeding Complete!
```

---

## After Deployment

### Your Live URLs

| What | URL |
|------|-----|
| 🌐 Frontend Dashboard | `https://saro-frontend-XXXX.up.railway.app` |
| 🔌 Backend API | `https://saro-backend-XXXX.up.railway.app` |
| 📖 Interactive API Docs | `https://saro-backend-XXXX.up.railway.app/api/docs` |
| 🏠 Landing Page | `https://saro-frontend-XXXX.up.railway.app/landing.html` |

---

## Demo Walkthrough Script (15 min)

### Opening (1 min)
> "SARO is an end-to-end AI regulatory intelligence platform. In the next 15 minutes I'll show you all four MVP modules — from document ingestion through real-time guardrails — running live."

### MVP1 — Ingestion (3 min)
1. Navigate to **MVP1 tab**
2. Paste this text into the form:
   > *"Article 9 requires providers of high-risk AI systems to establish risk management. Systems must detect bias, ensure data quality, and maintain transparency. Surveillance systems face unacceptable risk classification."*
3. Hit **Ingest & Analyze**
4. Show: entities extracted (EU AI Act), risk tags (bias, surveillance, transparency), risk score
5. Switch to **Forecast tab** — point out EU AI Act enforcement in 45 days at 92% probability

### MVP2 — Audit (3 min)
1. Navigate to **MVP2 tab**
2. Fill in: Model = `CreditScorer-v2`, Use Case = `finance`, Jurisdiction = `EU`
3. Hit **Run Compliance Audit**
4. Show: findings (bias risk, accountability gap), compliance score, recommendations
5. Switch to **Compliance Matrix** — show EU AI Act Article mapping

### MVP4 — Guardrails (4 min)
> "This is the showstopper."
1. Navigate to **MVP4 tab → Guardrails**
2. Type: `"All women are bad at math and your SSN 123-45-6789 will be stored"`
3. Hit **Check Guardrails** — show violations flagged in **<1ms**
4. Show stats: 48,291 checks today, 96.2% harmful blocked
5. Switch to **Compliance Reports** tab
6. Enter `DiagnosticAI-v2` + `FDA_510K` → Generate
7. Show the full 9-section FDA report generated in seconds

### MVP3 — Enterprise (2 min)
1. Navigate to **MVP3 tab**
2. Show tenant list — Deloitte, FinServ, HealthCo
3. Provision a new tenant live (type name + click button)
4. Show HA Status — 3 regions, 99.97% uptime

### Close (2 min)
1. Go back to **Dashboard**
2. Show live activity feed updating, alert deadlines, system health all green
3. Open `/api/docs` — show 40+ endpoints all documented
> "793 tests, 0 failures, SOC 2 ready, EU AI Act compliant by design."

---

## Troubleshooting

**Backend won't start:**
```bash
# Check logs
railway logs --service backend

# Common fix: ensure requirements.txt has no pinned versions breaking on Python 3.11
```

**Frontend can't reach backend (CORS/network errors):**
```bash
# Make sure VITE_API_URL is set correctly in frontend Railway service
# It must point to your backend Railway URL, NOT localhost
```

**Seeder fails to connect:**
```bash
# Wait 2-3 min for Railway cold start, then retry
python3 seed_demo.py --url https://YOUR-BACKEND.up.railway.app
```

**Free tier limitations:**
- Railway free tier sleeps after 30min inactivity → first request after sleep takes ~5s
- To avoid this during demo: hit the health endpoint 1 min before: `curl https://your-backend.up.railway.app/api/v1/health`

---

## Render.com Alternative (also free)

```bash
# 1. Push to GitHub (same as above)
# 2. Visit: https://dashboard.render.com/select-repo
# 3. Select repo → render.yaml auto-configures both services
# 4. Click Create Services
```

The `render.yaml` in the project root handles everything automatically.

---

## Fly.io Alternative

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Deploy backend
cd backend
fly launch --name saro-backend --region iad
fly deploy

# Deploy frontend
cd ../frontend  
fly launch --name saro-frontend --region iad
fly deploy
```

---

*SARO Platform v4.0.0 · Deploy Guide · Railway Edition*
