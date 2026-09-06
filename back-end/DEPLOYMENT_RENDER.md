# Deploy backend on Render (Postgres)

Code-only guide. **Do not commit real secrets.** No live deploy is performed by this PR.

## Architecture choice

| Environment | Database | Driver |
|-------------|----------|--------|
| Local / Docker compose | MySQL | `pymysql` (`mysql+pymysql://…`) |
| Render (production) | Postgres | `psycopg2` (`postgresql+psycopg2://…`) |

SQLAlchemy is **URL-driven**. The app normalizes Render’s `postgres://` / `postgresql://` URLs to `postgresql+psycopg2://`.

ORM models use portable types (`String`, `Text`, `Boolean`, `CHAR(36)`, `DateTime`). Migration `e2f72b1ae5f3` no longer imports `mysql.*`. Fresh Postgres DBs get tables via idempotent revision `a9b8c7d6e5f4` (no-op if tables already exist).

## Blueprint

Repo root `render.yaml`:

- Web service `rootDir: back-end`
- Build: `pip install -r requirements.txt`
- Start: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health: `GET /api/v1/health` (alias of `/health`)
- Free Postgres database linked as `DATABASE_URL`

## Required env vars (dashboard)

| Variable | Example / notes |
|----------|-----------------|
| `SECRET_KEY` | Generate in Render (never commit) |
| `DATABASE_URL` | From Render Postgres (`sslmode=require` recommended) |
| `CORS_ORIGINS` | `["https://jholvis123.github.io"]` (explicit list; credentials enabled) |
| `COOKIE_SECURE` | `true` on HTTPS |
| `COOKIE_SAMESITE` | `lax` (default) |
| `ALLOW_PUBLIC_REGISTER` | `false` |
| `DEBUG` | `false` |

Optional later: `COOKIE_SAMESITE=none` **only** with `COOKIE_SECURE=true` and a FE that can do CSRF cross-origin. Admin cookie auth from GitHub Pages remains **limited** with `lax` (third-party cookie / CSRF-cookie readability). Prefer public read APIs from Pages until same-site or Bearer is designed.

## Local MySQL

Keep using `.env` with `DATABASE_URL=mysql+pymysql://…` as in `.env.example`. Tests continue on SQLite via `conftest.py`.

## After first deploy

1. Confirm `GET https://<your-render-host>/api/v1/health` → `{"status":"healthy","db":"ok"}`.
2. Run `create_admin.py` against the Render DB (one-shot, with env vars) — do not re-enable public register.
3. Point Pages `apiUrl` at the Render HTTPS origin + `/api/v1` when FE is ready.

## Out of scope here

- Live Render provisioning / DNS
- Forcing `SameSite=None`
- Frontend code changes
