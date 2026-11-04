# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Portafolio personal de Elvis con plataforma de retos CTF. Monorepo: API FastAPI en `back-end/` y SPA Angular 16 en `front-end/portafolio/`. El código, los comentarios, los mensajes de error y los commits están en español.

## Comandos

### Backend (`cd back-end`)

```bash
pip install -r requirements-dev.txt          # incluye requirements.txt + moto (mock S3)
pip install pytest pytest-asyncio httpx ruff # CI los instala aparte; no están pineados
SECRET_KEY=dev pytest app/tests -q           # SECRET_KEY es obligatorio (Settings falla sin él)
SECRET_KEY=dev pytest app/tests/api/test_ctf_solve_integrity.py -q          # un archivo
SECRET_KEY=dev pytest app/tests/api/test_ctf_solve_integrity.py -k nombre   # un test
ruff check app/                              # lint obligatorio en CI (config: ruff.toml)
SECRET_KEY=dev DEBUG=true DATABASE_URL=sqlite:///./dev.db uvicorn app.main:app --reload
alembic upgrade head                         # migraciones (usa settings.DATABASE_URL)
alembic revision --autogenerate -m "desc"
ADMIN_EMAIL=... ADMIN_USERNAME=... ADMIN_PASSWORD=... python create_admin.py   # único modo de crear admin
SEED_PORTFOLIO=1 DATABASE_URL=... python seed_portfolio.py                     # seed idempotente de proyectos
```

- Los tests usan SQLite (`sqlite:///./test.db`) vía `app/tests/conftest.py`; no necesitan MySQL aunque CI levante uno. Se ejecutan desde `back-end/` (imports relativos `app.tests`).
- Fixtures clave: `client` (TestClient con `get_db` sobrescrito, `ALLOW_PUBLIC_REGISTER=True` y rate limiter reseteado), `admin_headers` / `user_headers` (Bearer JWT de un usuario insertado directamente).
- `psycopg2-binary` está pineado y no compila en Python ≥3.13; usar Python 3.10–3.12 (CI y Docker usan 3.10).
- Con `DEBUG=true` la app hace `create_all` al arrancar y expone `/docs`; en producción solo Alembic y sin docs.
- En CI son obligatorios `ruff` y `pytest`; black/isort/mypy son informativos (`continue-on-error`).

### Frontend (`cd front-end/portafolio`)

```bash
npm ci
npm start                                    # ng serve → http://localhost:4200, API en http://localhost:8000/api/v1
npx ng lint                                  # obligatorio en CI
npm run build -- --configuration production
npx ng build --configuration=github-pages --base-href=/Elvis/
npm test -- --no-watch --browsers=ChromeHeadless   # Karma; en CI es soft-fail
npx ng test --include='src/app/core/services/auth.service.spec.ts' --no-watch --browsers=ChromeHeadless
```

### Stack completo

`docker compose up -d --build` (necesita `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD`, `SECRET_KEY` en `.env`). nginx (`front-end/nginx.conf`) sirve la SPA y hace proxy de `/api/` y `/uploads/` a `backend:8000`, así que FE y API son same-origin.

## Arquitectura del backend

Clean Architecture / hexagonal en `back-end/app/`:

- `domain/entities/` — dataclasses puras con la lógica de negocio (p. ej. `CTF.verify_flag`, `mark_as_solved`, `increment_solved_count`).
- `domain/repositories/` — interfaces ABC. `domain/services/` — servicios de dominio que reciben repos por constructor.
- `application/use_cases/` — solo para CTF, writeups y adjuntos; el resto de routers llama directamente a servicios/repos. `application/dto/` son los modelos Pydantic de request/response. `application/dependencies.py` es legado; **la DI real está en `api/dependencies.py`**.
- `infrastructure/persistence/` — modelos SQLAlchemy y `*SqlRepository`, que mapean modelo ↔ entidad a mano (listas como `skills`/`hints` se guardan como JSON en texto) y **hacen `commit()` dentro de cada `save`/`delete`**. No hay unidad de trabajo.
- `api/routers/` — un router por recurso, montados bajo `/api/v1` en `main.py`. Health en `/health` y `/api/v1/health` (Render usa el segundo).

Gotchas:
- Hay **dos `declarative_base()`**: `core/database.py` y `infrastructure/persistence/base.py`. Los modelos, Alembic y los tests usan el de `infrastructure/persistence/base.py`. Un modelo nuevo debe heredar de ese y añadirse a `infrastructure/persistence/models/__init__.py`, al import de `main.py`, `alembic/env.py` y `conftest.py`.
- Las migraciones deben funcionar en MySQL (Docker/local), PostgreSQL (Render; `postgres://` se normaliza a `postgresql+psycopg2://`) y SQLite (tests).
- Storage: adjuntos e imágenes de writeups **siempre** van a disco local (`FileSystemStorage`, `UPLOAD_DIR`). Solo el avatar del portfolio usa S3/R2 cuando `STORAGE_TYPE=s3`. Las descargas de adjuntos pasan por `FileResponse` con control de acceso (no hay `StaticFiles` montado).
- El perfil de portfolio cae a un `DEFAULT_PROFILE` si no hay fila en BD; hay tests que impiden reintroducir datos inventados (tecnologías, CTFs, writeups). No inventar contenido de ejemplo.

### Autenticación (dos modos, ver `back-end/docs/BEARER_ADMIN_AUTH.md`)

1. **Same-origin (local/Docker)**: login emite cookies HttpOnly `access_token`, `refresh_token` (path `/api/v1/auth`) y `csrf_token` legible. Las mutaciones exigen double-submit: header `X-CSRF-Token` igual a la cookie (`csrf_protect_middleware`).
2. **Cross-origin (GitHub Pages → Render)**: login/refresh con `token_in_body: true` devuelven los JWT en el JSON; el FE los guarda en `sessionStorage` y envía `Authorization: Bearer`. Un Bearer **válido** salta CSRF.

Reglas que los tests de seguridad protegen: si llega un header `Authorization: Bearer` (aunque vacío o inválido) no se cae a la cookie → 401. `get_current_admin` comprueba `is_admin`. `POST /auth/register` está cerrado salvo `ALLOW_PUBLIC_REGISTER=true`. Los jugadores del CTF se registran con `POST /auth/register-player` (solo alias + contraseña, `email` NULL, nunca admin; requiere `ALLOW_PLAYER_REGISTER=true`) y hacen login con `username` en lugar de `email`. Los alias son únicos sin distinguir mayúsculas y hay alias reservados (`RESERVED_ALIASES` en `user_dto.py`). Rate limiting con slowapi en memoria (`RATE_LIMITS` en `core/security_middleware.py`), con clave hash IP+User-Agent. Los errores no controlados devuelven un 500 genérico en español.

### Dominio CTF

- Flags: estáticas se guardan como SHA-256 en `flag_hash`; con `is_flag_regex=True` se guarda el patrón y se evalúa con timeout. El formato exigido es `flag{...}` y los intentos se guardan hasheados.
- `solved`/`solved_at` = lo resolvió el owner (admin). `solved_count` = aciertos de visitantes, deduplicados por `user_id` o por IP si es anónimo, y sin IP no cuenta. Lo cubre `test_ctf_solve_integrity.py` y la migración `c8a41e0b7d22`.
- Tablero estilo CTFd: `GET /ctfs/board` (retos por categoría + `solved_by_me`), `GET /ctfs/{id}/solves` (primera sangre = primero) y `/ctfs/leaderboard/*`, todo calculado en `domain/services/scoreboard_service.py` a partir del primer acierto por (jugador, CTF) en `flag_submissions`. Puntuación = puntos de CTFs publicados − coste de pistas; excluye admins e inactivos; empate → quien llegó antes.
- Pistas con coste: `ctfs.hint_costs` (JSON alineado con `hints`) y tabla `hint_unlocks` (coste copiado al desbloquear, único por usuario+CTF+índice). Las respuestas públicas devuelven `None` en las pistas de pago no desbloqueadas (`_apply_hint_visibility` en `api/routers/ctf.py`); se desbloquean con `POST /ctfs/{id}/hints/{index}/unlock`.
- CTFs no `PUBLISHED` responden 404 a quien no es admin (no se filtra su existencia). La misma idea de IDOR aplica a proyectos (`test_idor_projects_ctfs.py`).

## Arquitectura del frontend

Angular 16 con **standalone components** (no hay NgModules): `main.ts` → `app.config.ts` (router, `provideHttpClient` con interceptores funcionales `authInterceptor` + `errorInterceptor`, ngx-markdown). Rutas lazy por feature en `features/*/…routes.ts`; `/admin` está protegido con `AuthGuard` + `AdminGuard` (solo UX; la autorización real es del backend). Tailwind 3 + SCSS por componente.

- `core/services/api.service.ts` envuelve `HttpClient` sobre `environment.apiUrl`.
- `ApiAvailabilityService` decide dos cosas: si la API está configurada (un `apiUrl` placeholder como `YOUR-API-HOST` → la UI muestra estados vacíos honestos, sin datos falsos) y si es cross-origin (→ `AuthService.usesBearerAuth()` cambia al modo Bearer/sessionStorage; si no, cookies + CSRF).
- Entornos: `environment.ts` (localhost:8000), `environment.prod.ts` (`/api/v1` relativo, Docker), `environment.github-pages.ts` (el workflow `github-pages.yml` sustituye el placeholder por `vars.API_URL`).
- Los modelos TS en `core/models/` siguen los DTO snake_case del backend.

## Despliegue

- **GitHub Pages** (`github-pages.yml`, push a `main`): build `github-pages` con base-href `/Elvis/` y `404.html` como fallback de la SPA.
- **Render** (`render.yaml`): `rootDir: back-end`, `alembic upgrade head && uvicorn …`, Postgres gestionado, `CORS_ORIGINS` limitado a `https://jholvis123.github.io`. Más detalles en `back-end/DEPLOYMENT_RENDER.md`.
- **VPS con Docker** (`deploy.yml` por SSH + `DEPLOYMENT.md`, scripts en `scripts/`).
- Seguridad en CI: CodeQL, `security.yml`, gitleaks (`.gitleaks.toml`). Dependabot abre muchas PRs; los saltos mayores de Angular (16→21) no se pueden fusionar sueltos.
