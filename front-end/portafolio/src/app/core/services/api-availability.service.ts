import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

/**
 * Detects "API unavailable" mode for Pages / Docker honest UX:
 * - placeholder apiUrl (YOUR-API-HOST, empty, obvious stubs)
 * - network unreachable (status 0) when loading public data
 * - cross-origin API (Pages host ≠ API host) → Bearer auth mode
 */
@Injectable({
  providedIn: 'root'
})
export class ApiAvailabilityService {
  private readonly networkFailed$ = new BehaviorSubject<boolean>(false);

  /** True when environment.apiUrl looks like a real, usable API base. */
  isApiConfigured(): boolean {
    const url = (environment.apiUrl || '').trim();
    if (!url) {
      return false;
    }
    if (url.includes('YOUR-API-HOST')) {
      return false;
    }
    // Obvious placeholders — do not invent domains
    if (/placeholder|example\.com|changeme|TODO|api-host-here/i.test(url)) {
      return false;
    }
    return true;
  }

  /**
   * True when the API base URL is on a different origin than the page.
   * Relative apiUrl (e.g. `/api/v1`) is always same-origin (docker/nginx/local proxy).
   * Used to switch admin auth to Bearer + sessionStorage (cookies/CSRF fail cross-origin).
   */
  isCrossOriginApi(): boolean {
    const url = (environment.apiUrl || '').trim();
    if (!url || url.startsWith('/')) {
      return false;
    }
    try {
      const base =
        typeof window !== 'undefined' ? window.location.href : 'http://localhost/';
      const apiOrigin = new URL(url, base).origin;
      const pageOrigin =
        typeof window !== 'undefined' ? window.location.origin : 'http://localhost';
      return apiOrigin !== pageOrigin;
    } catch {
      return false;
    }
  }

  /** Configured and no known network outage. */
  isApiAvailable(): boolean {
    return this.isApiConfigured() && !this.networkFailed$.value;
  }

  /** Observable for templates (*ngIf="apiAvailable$ | async"). */
  get apiAvailable$(): Observable<boolean> {
    return this.networkFailed$.pipe(
      map(() => this.isApiAvailable())
    );
  }

  /** Alias used by templates that prefer "unavailable". */
  get apiUnavailable$(): Observable<boolean> {
    return this.apiAvailable$.pipe(map(ok => !ok));
  }

  markNetworkFailed(): void {
    if (!this.networkFailed$.value) {
      this.networkFailed$.next(true);
    }
  }

  /** Call when a public request succeeds (optional recovery). */
  markNetworkOk(): void {
    if (this.networkFailed$.value) {
      this.networkFailed$.next(false);
    }
  }

  /**
   * Inspect an error (HttpErrorResponse or ApiError) and mark unavailable on status 0.
   */
  noteRequestFailure(err: unknown): void {
    const status = this.extractStatus(err);
    if (status === 0) {
      this.markNetworkFailed();
    }
  }

  private extractStatus(err: unknown): number | undefined {
    if (!err || typeof err !== 'object') {
      return undefined;
    }
    const anyErr = err as { status?: number };
    return typeof anyErr.status === 'number' ? anyErr.status : undefined;
  }
}
