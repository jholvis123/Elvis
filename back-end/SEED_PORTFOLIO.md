# Seed de proyectos del portafolio (one-shot Render)

Script: `back-end/seed_portfolio.py`.

## Qué hace

- Inserta **solo proyectos reales** de GitHub `jholvis123` (Elvis, CTFd fork, Global-, fastapi-product fork, Trabajo-Final-De-Seguridad).
- Marca todos como `status=published`.
- `featured=true` en Elvis, CTFd y Trabajo Final de Seguridad (orden 1–3).
- **No** crea CTFs ni writeups (sin contenido inventado / sin flags).
- Idempotente por `github_url` (re-ejecutar actualiza, no duplica).
- Solo corre si `SEED_PORTFOLIO=1` (o `true`/`yes`).

## Render — arranque one-shot

1. Dashboard del servicio `elvis-api` → Environment → añade:
   - `SEED_PORTFOLIO` = `1`
2. Settings → Build & Deploy → **Start Command** temporal:
   ```bash
   alembic upgrade head && python seed_portfolio.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
3. Manual Deploy / reinicia el servicio.
4. Verifica:
   ```bash
   curl -s 'https://elvis-api-zr51.onrender.com/api/v1/projects?size=20' | jq '.total,.items|length'
   ```
   Éxito: `total >= 4` y todos `status` published (el listado público solo muestra published).
5. **Quita** `SEED_PORTFOLIO` del Environment.
6. Restaura Start Command normal:
   ```bash
   alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

## Local

```bash
cd back-end
SEED_PORTFOLIO=1 DATABASE_URL='sqlite:///./seed_local.db' python seed_portfolio.py
pytest app/tests/api/test_seed_portfolio.py -v
```

## Honestidad de fuentes

- Descripciones tomadas de GitHub description / README públicos.
- CTFd y fastapi-product se etiquetan como **forks** (parents CTFd/CTFd y henrytaby/fastapi-product).
- Trabajo-Final-De-Seguridad: árbol público limitado al momento del seed; no se inventa stack.
