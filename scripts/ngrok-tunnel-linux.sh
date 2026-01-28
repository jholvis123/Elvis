#!/bin/bash
# ============================================
# ngrok Tunnel Script for Ubuntu Server
# ============================================
# Creates a temporary public URL for your deployed app
# Usage: ./ngrok-tunnel-linux.sh
# ============================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

PORT=${1:-80}

echo ""
echo -e "${CYAN}========================================"
echo "   ngrok Tunnel - Ubuntu Server"
echo -e "========================================${NC}"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo -e "${YELLOW}[!] ngrok no está instalado${NC}"
    echo ""
    echo -e "${GREEN}Instalando ngrok...${NC}"
    
    # Install ngrok on Ubuntu/Debian
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
    sudo apt update && sudo apt install ngrok -y
    
    echo ""
    echo -e "${GREEN}[OK] ngrok instalado correctamente${NC}"
fi

echo -e "${GREEN}[OK] ngrok encontrado: $(ngrok version)${NC}"

# Check if ngrok is authenticated
echo ""
echo -e "${YELLOW}Verificando autenticación...${NC}"

if ! ngrok config check &> /dev/null; then
    echo ""
    echo -e "${RED}[!] ngrok no está autenticado${NC}"
    echo ""
    echo -e "${CYAN}Para autenticar ngrok (GRATIS):${NC}"
    echo ""
    echo "1. Crea cuenta en: https://ngrok.com/signup"
    echo "2. Obtén tu token en: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "3. Ejecuta:"
    echo ""
    echo -e "   ${GREEN}ngrok config add-authtoken TU_TOKEN_AQUI${NC}"
    echo ""
    echo "4. Ejecuta este script de nuevo"
    echo ""
    exit 1
fi

echo -e "${GREEN}[OK] ngrok autenticado${NC}"

# Check if Docker containers are running
echo ""
echo -e "${YELLOW}Verificando contenedores Docker...${NC}"

if docker ps --format "{{.Names}}" | grep -q "portfolio_frontend"; then
    echo -e "${GREEN}[OK] Frontend corriendo en puerto $PORT${NC}"
else
    echo -e "${YELLOW}[!] Frontend no está corriendo. Iniciando...${NC}"
    cd /opt/portfolio
    docker compose up -d
    sleep 10
fi

# Start ngrok tunnel
echo ""
echo -e "${CYAN}========================================"
echo "   🚀 Iniciando túnel ngrok..."
echo -e "========================================${NC}"
echo ""
echo -e "${GREEN}Tu aplicación será accesible desde internet!${NC}"
echo ""
echo -e "${YELLOW}IMPORTANTE:${NC}"
echo "- Copia la URL 'Forwarding' que aparece abajo"
echo "- Ábrela en tu celular o cualquier dispositivo"
echo "- Presiona Ctrl+C para detener el túnel"
echo ""
echo "----------------------------------------"
echo ""

# Run ngrok
ngrok http $PORT
