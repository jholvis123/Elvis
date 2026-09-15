# Avatar / logo upload (API contract)

Admin-only multipart upload for the portfolio profile avatar. Public file GET.

## Endpoints

| Method | Path | Auth |
|--------|------|------|
| `POST` | `/api/v1/portfolio/avatar` | Admin (Bearer o cookie+CSRF) |
| `DELETE` | `/api/v1/portfolio/avatar` | Admin |
| `GET` | `/api/v1/portfolio/avatar/file/{id}` | Público |
| `PUT` | `/api/v1/portfolio/profile` | Admin — sigue aceptando `avatar_url` HTTPS |

## POST multipart

- **Field name:** `file`
- **Allowed:** `.jpg`, `.jpeg`, `.png`, `.webp` only (~2MB max)
- **Validation:** extension + size + magic bytes (rejects exe/iso/pdf/etc.)

### Response `201`

```json
{
  "avatar_url": "/api/v1/portfolio/avatar/file/{uuid}.webp",
  "id": "{uuid}.webp",
  "filename": "{uuid}.webp",
  "content_type": "image/webp",
  "size": 12345
}
```

`avatar_url` is also persisted on the profile (same value as in `GET /api/v1/portfolio/profile`).

## DELETE

Clears `avatar_url` and deletes the local file when it was a local upload.

```json
{ "avatar_url": null, "message": "Avatar eliminado" }
```

## GET profile

`GET /api/v1/portfolio/profile` → `avatar_url` is either:

- Local: `/api/v1/portfolio/avatar/file/{uuid}.{ext}` (relative to API origin), or
- External HTTPS set via `PUT /portfolio/profile`.

## Render note

Local files live on ephemeral disk — see `DEPLOYMENT_RENDER.md`. Prefer HTTPS `avatar_url` for durable production logos until object storage is available.
