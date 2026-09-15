# Admin auth: cookies (same-origin) + Bearer (Pages → Render)

## Problema
FE en `https://jholvis123.github.io` y API en `https://elvis-api-zr51.onrender.com`
no pueden usar cookies CSRF/SameSite de forma fiable cross-origin.

## Diseño
1. **Login** `POST /api/v1/auth/login` con body:
   ```json
   { "email": "...", "password": "...", "token_in_body": true }
   ```
   Respuesta incluye `access_token`, `refresh_token`, `token_type: "bearer"` además de
   seguir seteando cookies (útiles en local/docker same-origin).

2. **Requests admin**: `Authorization: Bearer <access_token>`
   (`get_current_user` / `get_current_admin` aceptan Bearer **o** cookie; Bearer tiene prioridad).

3. **CSRF**: no se exige si hay header `Authorization: Bearer ...`.
   El flujo cookie sigue exigiendo `X-CSRF-Token` + cookie `csrf_token`.

4. **Refresh** `POST /api/v1/auth/refresh`:
   ```json
   { "refresh_token": "<token>", "token_in_body": true }
   ```
   o cookie `refresh_token` (same-origin).

5. **Logout**: limpia cookies; el cliente Bearer descarta el token en memoria/storage.

`is_admin` no se debilita.

## Nota JSON
Login/refresh serializan con `exclude_none`: si `token_in_body` es false, no se emiten `access_token`/`refresh_token`/`token_type` como null.
