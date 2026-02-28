#!/bin/bash
# SARO Platform — Docker Deployment Script
# MVP1 + MVP2 + MVP3 + MVP4 Unified

set -e

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║         SARO PLATFORM — DOCKER DEPLOYMENT           ║"
echo "║   MVP1: Forecast | MVP2: Audit | MVP3: Enterprise   ║"
echo "║               MVP4: Agentic GA                      ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose plugin."
    exit 1
fi

echo "✓ Docker found: $(docker --version)"
echo ""

# Build and start
echo "🔨 Building containers..."
docker compose build --no-cache

echo ""
echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 8

# Check health
echo ""
echo "🔍 Checking service health..."

if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Backend API    → http://localhost:8000"
    echo "  └─ API Docs    → http://localhost:8000/docs"
else
    echo "⚠ Backend not ready yet, check: docker compose logs backend"
fi

if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo "✓ Frontend       → http://localhost:3000"
else
    echo "⚠ Frontend not ready yet, check: docker compose logs frontend"
fi

if curl -sf http://localhost:80/health > /dev/null 2>&1; then
    echo "✓ Gateway        → http://localhost:80"
else
    echo "⚠ Gateway not ready yet"
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║                   ENDPOINTS                         ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  🌐 Frontend Dashboard  → http://localhost:3000     ║"
echo "║  ⚡ Backend API         → http://localhost:8000     ║"
echo "║  📖 API Docs (Swagger)  → http://localhost:8000/docs║"
echo "║  🔀 Nginx Gateway       → http://localhost:80       ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  MVP1: /api/mvp1/forecast   /api/mvp1/regulations  ║"
echo "║  MVP2: /api/mvp2/audit      /api/mvp2/policy/eval  ║"
echo "║  MVP3: /api/mvp3/tenants    /api/mvp3/ha-status    ║"
echo "║  MVP4: /api/mvp4/guardrails /api/mvp4/training     ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  📋 Logs:  docker compose logs -f                   ║"
echo "║  🛑 Stop:  docker compose down                      ║"
echo "║  🔄 Reset: docker compose down -v && ./deploy.sh   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
