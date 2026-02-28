#!/usr/bin/env bash
# SARO Platform - Docker Deployment Script
set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
AMBER='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${CYAN}[SARO]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${AMBER}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     SARO Platform v4.0.0 — Docker Deploy     ║${NC}"
echo -e "${CYAN}║   MVP1 + MVP2 + MVP3 + MVP4  |  793 tests    ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
command -v docker >/dev/null 2>&1 || error "Docker is not installed"
command -v docker-compose >/dev/null 2>&1 || command -v docker >/dev/null 2>&1 || error "Docker Compose is not installed"
success "Docker prerequisites met"

# Create .env if missing
if [ ! -f .env ]; then
    warn ".env not found — creating from .env.example"
    cp .env.example .env 2>/dev/null || cat > .env << 'ENVEOF'
SECRET_KEY=saro-dev-secret-change-in-prod
DEBUG=false
FRONTEND_PORT=3000
HTTP_PORT=80
ANTHROPIC_API_KEY=
ENVEOF
    success "Created .env file"
fi

# Build and deploy
log "Building Docker images..."
docker compose build --parallel

log "Starting services..."
docker compose up -d

# Wait for health
log "Waiting for services to be healthy..."
MAX_WAIT=60
WAIT=0
while [ $WAIT -lt $MAX_WAIT ]; do
    BACKEND_STATUS=$(docker inspect --format='{{.State.Health.Status}}' saro-backend 2>/dev/null || echo "starting")
    if [ "$BACKEND_STATUS" = "healthy" ]; then
        break
    fi
    sleep 3
    WAIT=$((WAIT + 3))
    echo -n "."
done
echo ""

if [ "$BACKEND_STATUS" != "healthy" ]; then
    warn "Backend health check timeout. Services may still be starting."
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          SARO Platform is running!           ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  🌐 Frontend:    ${CYAN}http://localhost:3000${NC}"
echo -e "  🔌 Backend API: ${CYAN}http://localhost:8000${NC}"
echo -e "  📖 API Docs:    ${CYAN}http://localhost:8000/api/docs${NC}"
echo -e "  🔄 Via Nginx:   ${CYAN}http://localhost:80${NC}"
echo ""
echo -e "  MVP1 Ingestion: ${CYAN}http://localhost:8000/api/v1/mvp1${NC}"
echo -e "  MVP2 Audit:     ${CYAN}http://localhost:8000/api/v1/mvp2${NC}"
echo -e "  MVP3 Enterprise:${CYAN}http://localhost:8000/api/v1/mvp3${NC}"
echo -e "  MVP4 Agentic:   ${CYAN}http://localhost:8000/api/v1/mvp4${NC}"
echo ""
echo -e "  Stop:   ${AMBER}docker compose down${NC}"
echo -e "  Logs:   ${AMBER}docker compose logs -f${NC}"
echo -e "  Status: ${AMBER}docker compose ps${NC}"
echo ""
