# 🚀 Guía de Despliegue - Portfolio Application

## Despliegue en Ubuntu Server 22.04/24.04 LTS

---

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#-requisitos-previos)
2. [Instalación de Docker](#-instalación-de-docker)
3. [Configuración del Servidor](#-configuración-del-servidor)
4. [Despliegue de la Aplicación](#-despliegue-de-la-aplicación)
5. [Configuración SSL/HTTPS](#-configuración-sslhttps-opcional)
6. [Comandos Útiles](#-comandos-útiles)
7. [Monitoreo y Logs](#-monitoreo-y-logs)
8. [Troubleshooting](#-troubleshooting)
9. [Backup y Restauración](#-backup-y-restauración)

---

## 📦 Requisitos Previos

### Hardware Mínimo
- **CPU**: 2 cores
- **RAM**: 4 GB (recomendado 8 GB)
- **Disco**: 20 GB SSD
- **Red**: IP pública estática

### Software
- Ubuntu Server 22.04 LTS o 24.04 LTS
- Acceso SSH con usuario sudo
- Puerto 80 y 443 abiertos en firewall

---

## 🐳 Instalación de Docker

### Paso 1: Actualizar el sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### Paso 2: Instalar dependencias

```bash
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    htop \
    nano
```

### Paso 3: Agregar repositorio oficial de Docker

```bash
# Agregar clave GPG
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Agregar repositorio
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### Paso 4: Instalar Docker Engine

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### Paso 5: Configurar usuario (sin sudo)

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Paso 6: Verificar instalación

```bash
docker --version
docker compose version
docker run hello-world
```

---

## ⚙️ Configuración del Servidor

### Paso 1: Configurar Firewall (UFW)

```bash
# Habilitar UFW
sudo ufw enable

# Permitir SSH
sudo ufw allow OpenSSH

# Permitir HTTP y HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Verificar reglas
sudo ufw status
```

### Paso 2: Configurar Swap (si RAM < 4GB)

```bash
# Crear archivo swap de 2GB
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Hacer permanente
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Paso 3: Crear directorio de la aplicación

```bash
sudo mkdir -p /opt/portfolio
sudo chown $USER:$USER /opt/portfolio
cd /opt/portfolio
```

---

## 🚀 Despliegue de la Aplicación

### Paso 1: Clonar el repositorio

```bash
cd /opt/portfolio
git clone https://github.com/tu-usuario/elvis.git .
# O subir archivos via SCP/SFTP
```

### Paso 2: Crear archivo de variables de entorno

```bash
# Copiar plantilla
cp .env.example .env

# Editar con valores reales
nano .env
```

**Configuración mínima requerida:**

```env
# Database
MYSQL_DATABASE=portfolio_db
MYSQL_USER=portfolio_user
MYSQL_PASSWORD=TuPasswordSeguro123!
MYSQL_ROOT_PASSWORD=TuRootPasswordSeguro456!

# Security - GENERAR NUEVOS VALORES
SECRET_KEY=$(openssl rand -hex 32)
CSRF_SECRET_KEY=$(openssl rand -hex 32)

# Redis
REDIS_PASSWORD=TuRedisPasswordSeguro789!

# App
DEBUG=false
COOKIE_SECURE=true
COOKIE_SAMESITE=strict
COOKIE_DOMAIN=.tudominio.com

# CORS - Tu dominio
CORS_ORIGINS=https://tudominio.com,https://www.tudominio.com

# Timezone
TZ=America/Mexico_City
```

**Generar claves seguras:**

```bash
# Generar SECRET_KEY
openssl rand -hex 32

# Generar CSRF_SECRET_KEY
openssl rand -hex 32

# Generar passwords seguros
openssl rand -base64 24
```

### Paso 3: Construir imágenes

```bash
# Build de todas las imágenes
docker compose build --no-cache

# O build individual
docker compose build backend
docker compose build frontend
```

### Paso 4: Iniciar servicios

```bash
# Iniciar en modo detached
docker compose up -d

# Verificar estado
docker compose ps
```

### Paso 5: Verificar logs

```bash
# Todos los servicios
docker compose logs -f

# Solo backend
docker compose logs -f backend

# Solo frontend
docker compose logs -f frontend

# Solo database
docker compose logs -f db
```

### Paso 6: Verificar migraciones de BD

```bash
# Ver estado de migraciones
docker compose exec backend alembic current

# Si necesitas correr migraciones manualmente
docker compose exec backend alembic upgrade head
```

### Paso 7: Crear usuario administrador

```bash
docker compose exec backend python create_admin.py
```

### Paso 8: Verificar endpoints

```bash
# Health check del backend
curl http://localhost/api/v1/health

# O desde el navegador
# http://tu-ip-servidor/
# http://tu-ip-servidor/api/v1/docs
```

---

## 🔒 Configuración SSL/HTTPS (Opcional)

### Opción A: Certbot con Let's Encrypt

```bash
# Instalar Certbot
sudo apt install -y certbot

# Obtener certificado (detener nginx primero)
docker compose stop frontend
sudo certbot certonly --standalone -d tudominio.com -d www.tudominio.com

# Los certificados estarán en:
# /etc/letsencrypt/live/tudominio.com/fullchain.pem
# /etc/letsencrypt/live/tudominio.com/privkey.pem
```

### Opción B: Usar Traefik como reverse proxy

Crear `docker-compose.override.yml`:

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    container_name: traefik
    restart: unless-stopped
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=tu@email.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik_letsencrypt:/letsencrypt
    networks:
      - portfolio_network

  frontend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`tudominio.com`)"
      - "traefik.http.routers.frontend.entrypoints=websecure"
      - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"
    ports: []  # Remove direct port mapping

volumes:
  traefik_letsencrypt:
```

---

## 🛠️ Comandos Útiles

### Gestión de Contenedores

```bash
# Ver estado de todos los servicios
docker compose ps

# Reiniciar un servicio específico
docker compose restart backend

# Detener todos los servicios
docker compose down

# Detener y eliminar volúmenes (⚠️ BORRA DATOS)
docker compose down -v

# Reconstruir sin cache
docker compose build --no-cache

# Actualizar y reiniciar
git pull && docker compose up -d --build
```

### Acceso a Contenedores

```bash
# Shell en el backend
docker compose exec backend bash

# Shell en la base de datos
docker compose exec db mysql -u root -p

# Shell en Redis
docker compose exec redis redis-cli -a $REDIS_PASSWORD
```

### Migraciones de Base de Datos

```bash
# Ver migraciones pendientes
docker compose exec backend alembic history

# Aplicar migraciones
docker compose exec backend alembic upgrade head

# Revertir última migración
docker compose exec backend alembic downgrade -1

# Crear nueva migración
docker compose exec backend alembic revision --autogenerate -m "descripcion"
```

---

## 📊 Monitoreo y Logs

### Ver Logs en Tiempo Real

```bash
# Todos los servicios
docker compose logs -f --tail=100

# Filtrar por servicio
docker compose logs -f backend --tail=50
docker compose logs -f frontend --tail=50
docker compose logs -f db --tail=50
```

### Monitorear Recursos

```bash
# Uso de recursos por contenedor
docker stats

# Uso de disco
docker system df

# Limpiar recursos no usados
docker system prune -af
```

### Health Checks

```bash
# Verificar salud de contenedores
docker compose ps

# Health check manual
curl -f http://localhost/api/v1/health
curl -f http://localhost/nginx-health
```

---

## 🔧 Troubleshooting

### Problema: Contenedor no inicia

```bash
# Ver logs detallados
docker compose logs backend --tail=100

# Verificar configuración
docker compose config

# Reiniciar servicio
docker compose restart backend
```

### Problema: Error de conexión a BD

```bash
# Verificar que MySQL esté corriendo
docker compose ps db

# Verificar logs de MySQL
docker compose logs db

# Probar conexión
docker compose exec backend python -c "from app.core.database import engine; print(engine.connect())"
```

### Problema: Error de CORS

```bash
# Verificar variable CORS_ORIGINS en .env
cat .env | grep CORS

# Debe coincidir exactamente con el dominio del frontend
# Ejemplo: CORS_ORIGINS=https://tudominio.com
```

### Problema: Error 502 Bad Gateway

```bash
# Verificar que backend esté corriendo
docker compose ps backend

# Verificar logs de nginx
docker compose logs frontend

# Verificar que backend responda
docker compose exec frontend curl http://backend:8000/health
```

### Problema: Permisos de archivos

```bash
# Corregir permisos de uploads
docker compose exec backend chown -R appuser:appgroup /app/uploads
```

---

## 💾 Backup y Restauración

### Backup de Base de Datos

```bash
# Crear backup
docker compose exec db mysqldump -u root -p${MYSQL_ROOT_PASSWORD} portfolio_db > backup_$(date +%Y%m%d).sql

# Backup comprimido
docker compose exec db mysqldump -u root -p${MYSQL_ROOT_PASSWORD} portfolio_db | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restaurar Base de Datos

```bash
# Restaurar desde backup
docker compose exec -T db mysql -u root -p${MYSQL_ROOT_PASSWORD} portfolio_db < backup.sql

# Restaurar desde backup comprimido
gunzip -c backup.sql.gz | docker compose exec -T db mysql -u root -p${MYSQL_ROOT_PASSWORD} portfolio_db
```

### Backup de Uploads

```bash
# Crear backup de uploads
docker compose exec backend tar -czf /tmp/uploads_backup.tar.gz /app/uploads
docker cp portfolio_backend:/tmp/uploads_backup.tar.gz ./backups/

# O copiar directamente el volumen
docker run --rm -v portfolio_uploads_data:/data -v $(pwd)/backups:/backup alpine tar -czf /backup/uploads_$(date +%Y%m%d).tar.gz /data
```

### Script de Backup Automatizado

Crear `/opt/portfolio/scripts/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/portfolio/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup DB
docker compose exec -T db mysqldump -u root -p${MYSQL_ROOT_PASSWORD} portfolio_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup uploads
docker run --rm -v portfolio_uploads_data:/data -v $BACKUP_DIR:/backup alpine tar -czf /backup/uploads_$DATE.tar.gz /data

# Mantener solo últimos 7 días
find $BACKUP_DIR -mtime +7 -delete

echo "Backup completado: $DATE"
```

Agregar al crontab:

```bash
# Backup diario a las 3:00 AM
0 3 * * * /opt/portfolio/scripts/backup.sh >> /var/log/portfolio_backup.log 2>&1
```

---

## ✅ Checklist Post-Despliegue

- [ ] Frontend accesible en el navegador
- [ ] API responde en `/api/v1/health`
- [ ] Documentación Swagger en `/api/v1/docs`
- [ ] Login funciona correctamente
- [ ] CORS configurado correctamente
- [ ] SSL/HTTPS configurado (producción)
- [ ] Backups automatizados configurados
- [ ] Monitoreo de logs activo
- [ ] Firewall configurado (solo puertos necesarios)
- [ ] Variables sensibles no expuestas

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs: `docker compose logs -f`
2. Verifica el estado: `docker compose ps`
3. Consulta la documentación de FastAPI/Angular
4. Abre un issue en el repositorio

---

**Última actualización:** Enero 2026
