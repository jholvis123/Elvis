@echo off
:: ============================================
:: ngrok Quick Start - Portfolio
:: ============================================
:: Double-click this file to start ngrok tunnel
:: ============================================

echo.
echo ========================================
echo    ngrok Tunnel - Portfolio App
echo ========================================
echo.

:: Check if ngrok exists
where ngrok >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] ngrok no esta instalado
    echo.
    echo Para instalar ngrok:
    echo 1. Ve a: https://ngrok.com/download
    echo 2. Descarga ngrok para Windows
    echo 3. Extrae ngrok.exe en C:\ngrok\
    echo 4. Agrega C:\ngrok\ a tu PATH
    echo.
    echo O ejecuta: winget install ngrok.ngrok
    echo.
    pause
    exit /b 1
)

echo [OK] ngrok encontrado
echo.
echo Iniciando tunel en puerto 80...
echo.
echo ========================================
echo    URL PUBLICA APARECERA ABAJO
echo ========================================
echo.
echo Copia la URL "Forwarding" y abrela
echo en tu celular o cualquier navegador.
echo.
echo Presiona Ctrl+C para detener.
echo ----------------------------------------
echo.

ngrok http 80

pause
