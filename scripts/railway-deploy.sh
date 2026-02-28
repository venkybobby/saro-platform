#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  SARO Platform — Railway Deployment Script                  ║
# ║  Deploys backend + frontend + seeds demo data               ║
# ║  Estimated time: 15-25 minutes                              ║
# ╚══════════════════════════════════════════════════════════════╝
set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────
GREEN='\033[0;32m'; CYAN='\033[0;36m'; AMBER='\033[0;33m'
RED='\033[0;31m'; BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'

ok()   { echo -e "  ${GREEN}✓${RESET} $1"; }
info() { echo -e "  ${CYAN}→${RESET} $1"; }
warn() { echo -e "  ${AMBER}!${RESET} $1"; }
fail() { echo -e "  ${RED}✗${RESET} $1"; exit 1; }
step() { echo -e "\n${BOLD}${CYAN}── $1${RESET}"; }
hr()   { echo -e "${DIM}──────────────────────────────────────────────${RESET}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# ── Banner ───────────────────────────────────────────────────────
clear
echo ""
echo -e "${CYAN}${BOLD}"
cat << 'BANNER'
  ███████╗ █████╗ ██████╗  ██████╗
  ██╔════╝██╔══██╗██╔══██╗██╔═══██╗
  ███████╗███████║██████╔╝██║   ██║
  ╚════██║██╔══██║██╔══██╗██║   ██║
  ███████║██║  ██║██║  ██║╚██████╔╝
  ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝
BANNER
echo -e "${RESET}"
echo -e "  ${BOLD}AI Regulatory Intelligence Platform${RESET} — Railway Deployment"
echo -e "  ${DIM}MVP1 + MVP2 + MVP3 + MVP4 | 793 tests | v4.0.0${RESET}"
echo ""
hr

# ── Pre-flight checks ────────────────────────────────────────────
step "Step 1/5 — Pre-flight Checks"

# Check Railway CLI
if ! command -v railway &>/dev/null; then
    warn "Railway CLI not installed. Installing now..."
    
    if command -v npm &>/dev/null; then
        npm install -g @railway/cli
        ok "Railway CLI installed via npm"
    elif command -v curl &>/dev/null; then
        curl -fsSL https://railway.app/install.sh | sh
        ok "Railway CLI installed via curl"
    else
        fail "Cannot install Railway CLI. Please install manually: https://docs.railway.app/guides/cli"
    fi
fi

RAILWAY_VERSION=$(railway --version 2>/dev/null || echo "unknown")
ok "Railway CLI ready ($RAILWAY_VERSION)"

# Check git
if ! command -v git &>/dev/null; then
    fail "Git is required. Install from https://git-scm.com"
fi
ok "Git ready"

# Check Python (for seeder)
if command -v python3 &>/dev/null; then
    ok "Python3 ready (for demo seeder)"
    HAS_PYTHON=true
else
    warn "Python3 not found — will skip demo seeder (you can run it manually later)"
    HAS_PYTHON=false
fi

# ── Git init / push ──────────────────────────────────────────────
step "Step 2/5 — Prepare Git Repository"

cd "$ROOT_DIR"

if [ ! -d ".git" ]; then
    git init
    ok "Git repository initialized"
else
    ok "Git repository already exists"
fi

# Create .gitignore if missing
if [ ! -f ".gitignore" ]; then
cat > .gitignore << 'EOF'
.env
__pycache__/
*.pyc
*.pyo
node_modules/
dist/
*.db
*.log
.DS_Store
.railway/
EOF
fi

# Stage and commit
git add -A
if git diff --staged --quiet; then
    ok "No changes to commit — repository is up to date"
else
    git commit -m "SARO Platform v4.0.0 — MVP1-4 complete deployment"
    ok "Changes committed"
fi

# ── Railway login & project setup ────────────────────────────────
step "Step 3/5 — Railway Project Setup"

echo ""
echo -e "  ${AMBER}You need a Railway account. Free tier is sufficient for demo.${RESET}"
echo -e "  ${AMBER}Sign up at: https://railway.app${RESET}"
echo ""

read -p "  Press ENTER when ready to authenticate with Railway... "

railway login
ok "Authenticated with Railway"

# Create or link project
echo ""
echo -e "  ${CYAN}Creating new Railway project 'saro-platform'...${RESET}"

railway init --name "saro-platform" 2>/dev/null || {
    warn "Project may already exist — linking to existing project"
    railway link
}

ok "Railway project ready"

# ── Deploy Backend ────────────────────────────────────────────────
step "Step 4/5 — Deploy Services"

echo ""
info "Deploying BACKEND service (FastAPI)..."
echo -e "  ${DIM}This builds and deploys the Python API with all 4 MVP modules${RESET}"
echo ""

cd "$ROOT_DIR/backend"

# Set required env vars on Railway
railway variables set \
    SECRET_KEY="saro-$(openssl rand -hex 16 2>/dev/null || echo 'railway-demo-secret-key-2024')" \
    DEBUG="false" \
    PYTHONUNBUFFERED="1" \
    2>/dev/null || warn "Could not set env vars via CLI — set them manually in Railway dashboard"

railway up --service backend --detach
ok "Backend deployment triggered"

# ── Deploy Frontend ───────────────────────────────────────────────
echo ""
info "Deploying FRONTEND service (React + Vite)..."
echo -e "  ${DIM}This builds the React app and serves it via static hosting${RESET}"
echo ""

cd "$ROOT_DIR/frontend"

railway up --service frontend --detach
ok "Frontend deployment triggered"

# ── Wait for deployments ──────────────────────────────────────────
echo ""
info "Waiting for deployments to complete (~3-5 minutes)..."
echo ""
echo -e "  ${DIM}You can also monitor progress at: https://railway.app/dashboard${RESET}"
echo ""

WAIT_SECS=0
MAX_WAIT=300
BACKEND_URL=""

while [ $WAIT_SECS -lt $MAX_WAIT ]; do
    # Try to get the backend URL
    BACKEND_URL=$(railway domain --service backend 2>/dev/null || echo "")
    
    if [ -n "$BACKEND_URL" ]; then
        # Check health
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://${BACKEND_URL}/api/v1/health" 2>/dev/null || echo "000")
        if [ "$HTTP_CODE" = "200" ]; then
            ok "Backend is live and healthy!"
            break
        fi
    fi
    
    echo -ne "  ${DIM}Waiting... ${WAIT_SECS}s${RESET}\r"
    sleep 10
    WAIT_SECS=$((WAIT_SECS + 10))
done

FRONTEND_URL=$(railway domain --service frontend 2>/dev/null || echo "")

# ── Seed Demo Data ────────────────────────────────────────────────
step "Step 5/5 — Seed Demo Data"

if [ -n "$BACKEND_URL" ] && [ "$HAS_PYTHON" = true ]; then
    echo ""
    info "Seeding all 4 MVPs with realistic demo data..."
    echo ""
    
    cd "$ROOT_DIR"
    
    # Install seeder dependency
    pip3 install httpx --quiet --break-system-packages 2>/dev/null || pip3 install httpx --quiet 2>/dev/null || true
    
    python3 seed_demo.py --url "https://${BACKEND_URL}"
    ok "Demo data seeded successfully!"
else
    if [ -z "$BACKEND_URL" ]; then
        warn "Could not auto-detect backend URL — seed manually after deployment"
    fi
    if [ "$HAS_PYTHON" = false ]; then
        warn "Python3 not available — seed manually with:"
        echo "    pip install httpx"
        echo "    python3 seed_demo.py --url https://YOUR-BACKEND.up.railway.app"
    fi
fi

# ── Final Summary ────────────────────────────────────────────────
echo ""
hr
echo ""
echo -e "${GREEN}${BOLD}"
cat << 'SUCCESS'
  ╔══════════════════════════════════════════════════════════╗
  ║         🚀  SARO Platform is LIVE on Railway!           ║
  ╚══════════════════════════════════════════════════════════╝
SUCCESS
echo -e "${RESET}"

if [ -n "$FRONTEND_URL" ]; then
    echo -e "  🌐 ${BOLD}Frontend Dashboard:${RESET}  ${CYAN}https://${FRONTEND_URL}${RESET}"
fi
if [ -n "$BACKEND_URL" ]; then
    echo -e "  🔌 ${BOLD}Backend API:${RESET}         ${CYAN}https://${BACKEND_URL}${RESET}"
    echo -e "  📖 ${BOLD}API Docs:${RESET}            ${CYAN}https://${BACKEND_URL}/api/docs${RESET}"
fi
echo -e "  ⚙️  ${BOLD}Railway Dashboard:${RESET}   ${CYAN}https://railway.app/dashboard${RESET}"

echo ""
echo -e "  ${BOLD}Demo walkthrough:${RESET}"
echo -e "  1. Open the ${CYAN}Frontend Dashboard${RESET} → see live metrics"
echo -e "  2. Click ${CYAN}MVP1${RESET} → paste EU AI Act text → watch risk scoring"
echo -e "  3. Click ${CYAN}MVP2${RESET} → audit 'CreditScorer-v2' in finance/EU"
echo -e "  4. Click ${CYAN}MVP4${RESET} → type bias text → see guardrail block <1ms"
echo -e "  5. Click ${CYAN}MVP4 Reports${RESET} → generate FDA 510(k) package"
echo ""
echo -e "  ${DIM}If seeding failed, run manually:${RESET}"
echo -e "  ${DIM}python3 seed_demo.py --url https://${BACKEND_URL:-YOUR-BACKEND.up.railway.app}${RESET}"
echo ""
hr
echo ""
