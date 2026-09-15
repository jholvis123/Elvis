/**
 * Resolve portfolio/media URLs that may be relative to the API host.
 * BE may return paths like `/api/v1/portfolio/avatar/file/{uuid}.webp`.
 */
export function resolveApiMediaUrl(
  url: string | null | undefined,
  apiUrl: string
): string | null {
  const raw = (url || '').trim();
  if (!raw) {
    return null;
  }
  if (/^https?:\/\//i.test(raw)) {
    return raw;
  }

  const pageOrigin =
    typeof location !== 'undefined' && location?.origin
      ? location.origin
      : 'http://localhost';

  let apiOrigin: string;
  let apiPath: string;
  try {
    const api = new URL(apiUrl, pageOrigin);
    apiOrigin = api.origin;
    apiPath = api.pathname.replace(/\/$/, '');
  } catch {
    return raw.startsWith('/') ? raw : `/${raw}`;
  }

  if (raw.startsWith('/')) {
    return `${apiOrigin}${raw}`;
  }
  return `${apiOrigin}${apiPath}/${raw.replace(/^\//, '')}`;
}
