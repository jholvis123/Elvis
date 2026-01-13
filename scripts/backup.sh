#!/bin/bash
# ============================================
# Portfolio Application - Backup Script
# ============================================
# Run: chmod +x backup.sh && ./backup.sh
# Cron: 0 3 * * * /opt/portfolio/scripts/backup.sh
# ============================================

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/opt/portfolio/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
DATE=$(date +%Y%m%d_%H%M%S)
COMPOSE_FILE="${COMPOSE_FILE:-/opt/portfolio/docker-compose.yml}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

log_info "Starting backup at $DATE"

# Load environment variables
if [ -f /opt/portfolio/.env ]; then
    export $(cat /opt/portfolio/.env | grep -v '^#' | xargs)
fi

# Backup MySQL Database
log_info "Backing up MySQL database..."
if docker compose -f "$COMPOSE_FILE" exec -T db mysqldump -u root -p"${MYSQL_ROOT_PASSWORD}" portfolio_db 2>/dev/null | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"; then
    log_info "Database backup completed: db_$DATE.sql.gz"
else
    log_error "Database backup failed!"
fi

# Backup uploads volume
log_info "Backing up uploads..."
if docker run --rm \
    -v portfolio_uploads_data:/data:ro \
    -v "$BACKUP_DIR":/backup \
    alpine tar -czf /backup/uploads_$DATE.tar.gz -C /data . 2>/dev/null; then
    log_info "Uploads backup completed: uploads_$DATE.tar.gz"
else
    log_warn "Uploads backup failed or volume empty"
fi

# Backup Redis (optional)
log_info "Backing up Redis..."
if docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli -a "${REDIS_PASSWORD}" BGSAVE 2>/dev/null; then
    sleep 2
    docker cp portfolio_redis:/data/dump.rdb "$BACKUP_DIR/redis_$DATE.rdb" 2>/dev/null || log_warn "Redis backup skipped"
fi

# Cleanup old backups
log_info "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

# Show backup sizes
log_info "Backup summary:"
ls -lh "$BACKUP_DIR"/*_$DATE* 2>/dev/null || echo "No backups created"

# Calculate total size
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
log_info "Total backup directory size: $TOTAL_SIZE"

log_info "Backup completed successfully at $(date)"
