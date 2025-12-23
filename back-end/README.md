# Portfolio Backend

Backend para portafolio personal con arquitectura Clean Architecture + Hexagonal.

## 🚀 Características

- ✅ Sistema de autenticación JWT completo
- ✅ CRUD de proyectos del portafolio
- ✅ Gestión de CTF (Capture The Flag)  
- ✅ Writeups de soluciones CTF
- ✅ Formulario de contacto
- ✅ Rate limiting y seguridad reforzada
- ✅ API REST documentada con Swagger

## 📋 Requisitos

- Python 3.10+
- MySQL 8.0+ (o PostgreSQL)
- pip y virtualenv

## 🔧 Instalación

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd back-end
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia `.env.example` a `.env` y configura:

```env
# Database
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/portfolio_db

# Security
SECRET_KEY=tu-clave-secreta-muy-segura-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# App
DEBUG=true
APP_NAME=Portfolio API
APP_VERSION=1.0.0
API_V1_PREFIX=/api/v1

# CORS
CORS_ORIGINS=["http://localhost:4200","http://localhost"]
```

### 5. Crear base de datos

```bash
# Ejecutar en MySQL
CREATE DATABASE portfolio_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6. Ejecutar migraciones (si usas Alembic)

```bash
alembic upgrade head
```

### 7. Ejecutar servidor de desarrollo

```bash
# Opción 1: Directamente con Python
python -m app.main

# Opción 2: Con Uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en: `http://localhost:8000`

## 📚 Documentación

### Swagger UI
```
http://localhost:8000/docs
```

### ReDoc
```
http://localhost:8000/redoc
```

## 🗂️ Estructura del Proyecto

```
back-end/
├── app/
│   ├── main.py                      # Punto de entrada
│   │
│   ├── core/                        # Configuración base
│   │   ├── config.py                # Variables de entorno
│   │   ├── database.py              # Setup de SQLAlchemy
│   │   ├── security.py              # Hashing de contraseñas
│   │   ├── security_middleware.py   # Rate limiting & headers
│   │   └── logging.py               # Configuración de logs
│   │
│   ├── domain/                      # Lógica de negocio
│   │   ├── entities/                # Entidades del dominio
│   │   ├── repositories/            # Interfaces de repositorios
│   │   └── services/                # Servicios de dominio
│   │
│   ├── application/                 # Casos de uso
│   │   ├── dto/                     # Data Transfer Objects
│   │   ├── use_cases/               # Casos de uso
│   │   └── dependencies.py          # Factories DI
│   │
│   ├── infrastructure/              # Implementaciones
│   │   ├── persistence/             # SQLAlchemy models & repos
│   │   ├── storage/                 # Almacenamiento de archivos
│   │   └── security/                # JWT provider
│   │
│   ├── api/                         # Capa de API
│   │   ├── routers/                 # Endpoints FastAPI
│   │   │   ├── auth.py             # Autenticación
│   │   │   ├── ctf.py              # CTFs
│   │   │   ├── projects.py         # Proyectos
│   │   │   ├── writeups.py         # Writeups
│   │   │   ├── contact.py          # Contacto
│   │   │   ├── attachments.py      # Archivos adjuntos
│   │   │   └── portfolio.py        # Info del portfolio
│   │   └── dependencies.py          # DI para routers
│   │
│   └── tests/                       # Tests
│       ├── unit/                    # Tests unitarios
│       └── integration/             # Tests de integración
│
├── requirements.txt                 # Dependencias
├── .env.example                     # Ejemplo de variables
└── README.md                        # Este archivo
```

## 🔐 Seguridad

### Características Implementadas

✅ **Rate Limiting**
- Login: 10 intentos/minuto por IP
- Registro: 5 registros/hora por IP
- Límite global: 200 solicitudes/hora

✅ **Security Headers**
- X-Frame-Options: DENY
- Content-Security-Policy configurado
- HSTS habilitado
- X-Content-Type-Options: nosniff

✅ **Autenticación JWT**
- Access tokens con expiración
- Refresh tokens para renovación
- Hashing seguro de contraseñas (bcrypt)

✅ **Validaciones**
- Pydantic para validación de datos
- Sanitización de inputs
- Prevención de SQL Injection (ORM)

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=app --cov-report=html

# Tests específicos
pytest app/tests/unit/
pytest app/tests/integration/
```

## 📡 Endpoints Principales

### Autenticación
- `POST /api/v1/auth/register` - Registrar usuario
- `POST /api/v1/auth/login` - Iniciar sesión
- `POST /api/v1/auth/refresh` - Renovar token
- `GET /api/v1/auth/me` - Obtener usuario actual

### Proyectos
- `GET /api/v1/projects` - Listar proyectos
- `GET /api/v1/projects/featured` - Proyectos destacados
- `GET /api/v1/projects/{id}` - Obtener proyecto
- `POST /api/v1/projects` - Crear proyecto (admin)
- `PUT /api/v1/projects/{id}` - Actualizar proyecto (admin)
- `DELETE /api/v1/projects/{id}` - Eliminar proyecto (admin)

### CTFs
- `GET /api/v1/ctfs` - Listar CTFs
- `GET /api/v1/ctfs/{id}` - Obtener CTF
- `POST /api/v1/ctfs/{id}/submit` - Enviar flag
- `POST /api/v1/ctfs` - Crear CTF (admin)

### Writeups
- `GET /api/v1/writeups` - Listar writeups
- `GET /api/v1/writeups/popular` - Más populares
- `GET /api/v1/writeups/{id}` - Obtener writeup
- `POST /api/v1/writeups` - Crear writeup (admin)

Ver documentación completa en `/docs`

## 🌐 Despliegue

### Con Docker

```bash
# Build
docker build -t portfolio-backend .

# Run
docker run -p 8000:8000 --env-file .env portfolio-backend
```

### Con Gunicorn (Producción)

```bash
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🛠️ Desarrollo

### Agregar nuevas dependencias

```bash
pip install nombre-paquete
pip freeze > requirements.txt
```

### Crear nueva migración

```bash
alembic revision --autogenerate -m "descripción del cambio"
alembic upgrade head
```

## 📝 Changelog

### v1.0.0 (Actual)
- ✅ Sistema de autenticación completo
- ✅ CRUD de proyectos, CTFs y writeups
- ✅ Rate limiting implementado
- ✅ Security headers configurados
- ✅ Documentación API completa

## 👥 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -m 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

## 📄 Licencia

[Especificar licencia]

## 📧 Contacto

[Tu información de contacto]
