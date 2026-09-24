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

Clears `avatar_url` and deletes the stored object (local file or S3/R2 key) when it was an upload via this API.

```json
{ "avatar_url": null, "message": "Avatar eliminado" }
```

## GET profile

`GET /api/v1/portfolio/profile` → `avatar_url` is either:

- Uploaded: `/api/v1/portfolio/avatar/file/{uuid}.{ext}` (relative to API origin), or
- External HTTPS set via `PUT /portfolio/profile`.

## Storage backends

Controlled by `STORAGE_TYPE` — **avatar uploads only**:

| Value | Behavior |
|-------|----------|
| `local` (default) | Avatar files under `UPLOAD_DIR` (e.g. `uploads/avatars/`) |
| `s3` | Avatar objects in an S3-compatible bucket (Cloudflare R2 recommended on Render) |

**Important:** `STORAGE_TYPE=s3` does **not** move attachments or writeup images to S3. Those keep using local filesystem storage (`UPLOAD_DIR` / `/uploads/...`) via `get_storage_service()`. Only the three avatar endpoints use `get_avatar_storage_service()`.

In both avatar modes the public contract is unchanged: `avatar_url` stays the relative path `/api/v1/portfolio/avatar/file/{id}`. The GET endpoint **proxies/streams bytes** from disk or the bucket (no redirect), so the frontend needs no change. Responses include a reasonable `Cache-Control` (`public, max-age=86400`). Missing objects → `404`. `file_id` is validated with a UUID+ext regex (no path traversal).

### GET tradeoff (proxy vs alternatives)

| Approach | Pros | Cons |
|----------|------|------|
| **Proxy via API (chosen)** | Same relative URL; private bucket OK; FE unchanged; authz flexible later | Extra bandwidth/CPU on the API |
| Public bucket URL in `avatar_url` | Offloads bytes to R2/CDN | FE/CORS/cache changes; bucket must be public; breaks relative-path contract |
| Signed redirect (`302` + presigned URL) | Offloads bytes; bucket can stay private | FE must follow redirects; URL shape changes; short-lived links |

See `DEPLOYMENT_RENDER.md` for R2 env vars on Render.

## Render note

With `STORAGE_TYPE=local`, files live on ephemeral disk — see `DEPLOYMENT_RENDER.md`. Prefer `STORAGE_TYPE=s3` (R2) or an HTTPS `avatar_url` for durable production logos.
