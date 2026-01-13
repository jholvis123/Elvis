#!/bin/bash
# ============================================
# Portfolio Application - Health Check Script
# ============================================
# Verifica el estado de todos los servicios
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Portfolio Health Check${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check Docker
echo -e "${YELLOW}Checking Docker...${NC}"
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker is running${NC}"
else
    echo -e "${RED}✗ Docker is not running${NC}"
    exit 1
fi

# Check containers
echo ""
echo -e "${YELLOW}Checking containers...${NC}"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# Check Backend API
echo ""
echo -e "${YELLOW}Checking Backend API...${NC}"
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend API is healthy${NC}"
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/health
elif curl -sf http://localhost/api/v1/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend API is healthy (via nginx)${NC}"
    curl -s http://localhost/api/v1/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost/api/v1/health
else
    echo -e "${RED}✗ Backend API is not responding${NC}"
fi

# Check Frontend
echo ""
echo -e "${YELLOW}Checking Frontend...${NC}"
if curl -sf http://localhost/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is serving${NC}"
else
    echo -e "${RED}✗ Frontend is not responding${NC}"
fi

# Check Database
echo ""
echo -e "${YELLOW}Checking Database...${NC}"
if docker compose exec -T db mysqladmin ping -h localhost -u root -p"${MYSQL_ROOT_PASSWORD}" 2>/dev/null | grep -q "alive"; then
    echo -e "${GREEN}✓ MySQL is running${NC}"
else
    # Try without password (check if container is running)
    if docker compose ps db | grep -q "Up"; then
        echo -e "${GREEN}✓ MySQL container is running${NC}"
    else
        echo -e "${RED}✗ MySQL is not running${NC}"
    fi
fi

# Check Redis
echo ""
echo -e "${YELLOW}Checking Redis...${NC}"
if docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}✓ Redis is running${NC}"
else
    if docker compose ps redis | grep -q "Up"; then
        echo -e "${GREEN}✓ Redis container is running${NC}"
    else
        echo -e "${YELLOW}○ Redis is not configured or not running${NC}"
    fi
fi

# Disk usage
echo ""
echo -e "${YELLOW}Disk Usage...${NC}"
docker system df

# Resource usage
echo ""
echo -e "${YELLOW}Resource Usage...${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Health check completed${NC}"
echo -e "${BLUE}========================================${NC}"
