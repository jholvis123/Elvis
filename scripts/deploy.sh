#!/bin/bash
# ============================================
# Manual Deploy Script
# ============================================
# Run this script on the server for manual deployments
# Usage: ./deploy.sh
# ============================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DEPLOY_PATH="${DEPLOY_PATH:-/opt/portfolio}"

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

cd "$DEPLOY_PATH"

log_info "🚀 Starting deployment..."

# Check if there are local changes
if [[ -n $(git status --porcelain) ]]; then
    log_warn "Local changes detected. Stashing..."
    git stash
fi

# Pull latest code
log_info "📥 Pulling latest code from main..."
git fetch origin main
git reset --hard origin/main

# Check if docker-compose.yml changed
if git diff HEAD~1 --name-only | grep -q "docker-compose.yml\|Dockerfile"; then
    log_info "🐳 Docker files changed. Rebuilding containers..."
    docker compose build --no-cache
else
    log_info "🐳 Building containers (with cache)..."
    docker compose build
fi

# Restart services
log_info "♻️ Restarting services..."
docker compose down
docker compose up -d

# Wait for services to be ready
log_info "⏳ Waiting for services to start..."
sleep 15

# Run migrations
log_info "📊 Running database migrations..."
docker compose exec -T backend alembic upgrade head || log_warn "Migrations may have issues"

# Health check
log_info "🏥 Running health check..."
if curl -sf http://localhost/api/v1/health > /dev/null; then
    log_info "✅ Backend is healthy"
else
    log_warn "Backend health check failed - checking logs..."
    docker compose logs --tail=20 backend
fi

# Cleanup
log_info "🧹 Cleaning up old Docker images..."
docker image prune -f

log_info "✅ Deployment completed successfully!"

# Show status
docker compose ps
