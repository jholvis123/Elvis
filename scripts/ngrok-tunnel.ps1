# ============================================
# ngrok Tunnel Script - Portfolio
# ============================================
# Creates a temporary public URL for your local app
# ============================================

param(
    [int]$Port = 80,
    [string]$Region = "us"
)

$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ngrok Tunnel - Portfolio App" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if ngrok is installed
$ngrokPath = Get-Command ngrok -ErrorAction SilentlyContinue

if (-not $ngrokPath) {
    Write-Host "[!] ngrok no esta instalado" -ForegroundColor $Yellow
    Write-Host ""
    Write-Host "Instalando ngrok con winget..." -ForegroundColor $Yellow
    
    # Try to install with winget
    $wingetAvailable = Get-Command winget -ErrorAction SilentlyContinue
    
    if ($wingetAvailable) {
        winget install ngrok.ngrok
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        $ngrokPath = Get-Command ngrok -ErrorAction SilentlyContinue
        if (-not $ngrokPath) {
            Write-Host ""
            Write-Host "[ERROR] No se pudo instalar ngrok automaticamente" -ForegroundColor $Red
            Write-Host ""
            Write-Host "Instalacion manual:" -ForegroundColor $Yellow
            Write-Host "1. Ve a: https://ngrok.com/download" -ForegroundColor White
            Write-Host "2. Descarga ngrok para Windows" -ForegroundColor White
            Write-Host "3. Extrae ngrok.exe a una carpeta en tu PATH" -ForegroundColor White
            Write-Host "4. Ejecuta este script de nuevo" -ForegroundColor White
            Write-Host ""
            exit 1
        }
    } else {
        Write-Host ""
        Write-Host "Descarga manual requerida:" -ForegroundColor $Yellow
        Write-Host "1. Ve a: https://ngrok.com/download" -ForegroundColor White
        Write-Host "2. Descarga ngrok para Windows" -ForegroundColor White
        Write-Host "3. Extrae ngrok.exe en: C:\ngrok\" -ForegroundColor White
        Write-Host "4. Agrega C:\ngrok\ a tu PATH" -ForegroundColor White
        Write-Host "5. Ejecuta este script de nuevo" -ForegroundColor White
        Write-Host ""
        exit 1
    }
}

Write-Host "[OK] ngrok encontrado" -ForegroundColor $Green

# Check if ngrok is authenticated
Write-Host ""
Write-Host "Verificando autenticacion de ngrok..." -ForegroundColor $Yellow

$ngrokConfig = ngrok config check 2>&1
if ($ngrokConfig -match "error" -or $ngrokConfig -match "ERR") {
    Write-Host ""
    Write-Host "[!] ngrok no esta autenticado" -ForegroundColor $Yellow
    Write-Host ""
    Write-Host "Para autenticar ngrok:" -ForegroundColor White
    Write-Host "1. Crea cuenta gratis en: https://ngrok.com/signup" -ForegroundColor Cyan
    Write-Host "2. Copia tu authtoken desde: https://dashboard.ngrok.com/get-started/your-authtoken" -ForegroundColor Cyan
    Write-Host "3. Ejecuta:" -ForegroundColor White
    Write-Host "   ngrok config add-authtoken TU_TOKEN_AQUI" -ForegroundColor Green
    Write-Host ""
    Write-Host "4. Ejecuta este script de nuevo" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "[OK] ngrok autenticado" -ForegroundColor $Green

# Check if Docker containers are running
Write-Host ""
Write-Host "Verificando contenedores Docker..." -ForegroundColor $Yellow

$dockerRunning = docker ps --format "{{.Names}}" 2>&1
if ($dockerRunning -match "portfolio_frontend") {
    Write-Host "[OK] Frontend corriendo en puerto $Port" -ForegroundColor $Green
} else {
    Write-Host "[!] El frontend no esta corriendo" -ForegroundColor $Yellow
    Write-Host ""
    Write-Host "Iniciando contenedores Docker..." -ForegroundColor $Yellow
    Set-Location $PSScriptRoot\..
    docker compose up -d
    Start-Sleep -Seconds 10
}

# Start ngrok tunnel
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Iniciando tunel ngrok..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tu aplicacion sera accesible desde internet!" -ForegroundColor $Green
Write-Host ""
Write-Host "IMPORTANTE:" -ForegroundColor $Yellow
Write-Host "- Copia la URL 'Forwarding' que aparece abajo" -ForegroundColor White
Write-Host "- Abrela en tu celular o cualquier dispositivo" -ForegroundColor White
Write-Host "- Presiona Ctrl+C para detener el tunel" -ForegroundColor White
Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor Cyan

# Run ngrok
ngrok http $Port --region $Region
