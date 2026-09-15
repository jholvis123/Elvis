import { Injectable, inject } from '@angular/core';
import { Observable, of, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import {
  Technology,
  Highlight,
  PortfolioProfile,
  AvatarUploadResponse,
  AvatarDeleteResponse,
  ExperienceItem,
  ExperienceListResponse,
  ExperienceLinks,
  CapabilityChip,
  CapabilitiesResponse,
  CapabilitySkill
} from '../models';
import { ApiService, ApiError } from './api.service';
import { ApiAvailabilityService } from './api-availability.service';
import { environment } from '../../../environments/environment';
import { resolveApiMediaUrl } from '../utils/media-url';

/** Client-side avatar upload constraints (aligned with BE). */
export const AVATAR_MAX_BYTES = 2 * 1024 * 1024;
export const AVATAR_ACCEPT_MIME = ['image/jpeg', 'image/png', 'image/webp'] as const;
export const AVATAR_ACCEPT_ATTR = 'image/jpeg,image/png,image/webp';

export type { PortfolioProfile, AvatarUploadResponse, AvatarDeleteResponse };

@Injectable({
  providedIn: 'root'
})
export class PortfolioService {
  private readonly api = inject(ApiService);
  private readonly apiAvailability = inject(ApiAvailabilityService);

  /**
   * Obtiene el perfil completo desde la API.
   * Sin API: perfil vacío (UX honesta, sin datos inventados).
   */
  getProfile(): Observable<PortfolioProfile> {
    if (!this.apiAvailability.isApiConfigured()) {
      return of({
        name: '',
        title: '',
        roles: [],
        stack_items: [],
        about_points: [],
        highlights: [],
        social_links: {}
      });
    }
    return this.api.get<PortfolioProfile>('/portfolio/profile').pipe(
      catchError(err => {
        this.apiAvailability.noteRequestFailure(err);
        throw err;
      })
    );
  }

  /**
   * Reemplazo completo del perfil (admin). PUT, no PATCH.
   * CSRF lo añade el interceptor. social_links es un dict; twitter opcional se persiste si va en el PUT.
   */
  updateProfile(profile: PortfolioProfile): Observable<PortfolioProfile> {
    const social = profile.social_links || { email: '' };
    const body: PortfolioProfile = {
      name: profile.name,
      title: profile.title,
      bio: profile.bio ?? null,
      avatar_url: profile.avatar_url ?? null,
      roles: profile.roles ?? [],
      stack_items: profile.stack_items ?? [],
      about_points: profile.about_points ?? [],
      highlights: (profile.highlights ?? []).map((h) => ({
        label: h.label,
        value: h.value,
        icon: h.icon || undefined
      })),
      social_links: {
        email: social.email || '',
        github: social.github || '',
        linkedin: social.linkedin || '',
        twitter: social.twitter || '',
      }
    };
    return this.api.put<PortfolioProfile>('/portfolio/profile', body, { withCredentials: true });
  }

  /**
   * Absolute URL for <img src> from profile.avatar_url (may be relative to API host).
   */
  resolveAvatarUrl(avatarUrl: string | null | undefined): string | null {
    return resolveApiMediaUrl(avatarUrl, environment.apiUrl);
  }

  /**
   * POST /portfolio/avatar — multipart field `file`.
   * 201 body: { avatar_url, id, filename, content_type, size } (NOT PortfolioProfileDTO).
   * avatar_url e.g. /api/v1/portfolio/avatar/file/{uuid}.webp
   */
  uploadAvatar(file: File): Observable<AvatarUploadResponse> {
    const validationError = this.validateAvatarFile(file);
    if (validationError) {
      return throwError(() => new ApiError(validationError, 400));
    }
    const formData = new FormData();
    formData.append('file', file);
    return this.api.upload<AvatarUploadResponse>('/portfolio/avatar', formData, {
      withCredentials: true
    });
  }

  /**
   * DELETE /portfolio/avatar → { avatar_url: null, message }.
   * On 404/405, fallback: PUT profile with avatar_url=null
   * (requires current profile snapshot so other fields are not wiped).
   */
  deleteAvatar(currentProfile: PortfolioProfile): Observable<AvatarDeleteResponse> {
    const cleared: PortfolioProfile = { ...currentProfile, avatar_url: null };
    const deleted: AvatarDeleteResponse = { avatar_url: null, message: 'Avatar eliminado' };
    return this.api.delete<AvatarDeleteResponse | null>('/portfolio/avatar', { withCredentials: true }).pipe(
      map((res) => {
        if (res && typeof res === 'object' && 'avatar_url' in res) {
          return {
            avatar_url: null,
            message: typeof (res as AvatarDeleteResponse).message === 'string'
              ? (res as AvatarDeleteResponse).message
              : deleted.message
          };
        }
        return deleted;
      }),
      catchError((err: unknown) => {
        const status = err instanceof ApiError
          ? err.status
          : (err && typeof err === 'object' && 'status' in err
            ? Number((err as { status?: number }).status)
            : undefined);
        if (status === 404 || status === 405) {
          return this.updateProfile(cleared).pipe(map(() => deleted));
        }
        return throwError(() => err);
      })
    );
  }

  validateAvatarFile(file: File | null | undefined): string | null {
    if (!file) {
      return 'Selecciona una imagen.';
    }
    const mime = (file.type || '').toLowerCase();
    const okMime =
      AVATAR_ACCEPT_MIME.includes(mime as (typeof AVATAR_ACCEPT_MIME)[number]) ||
      // some browsers omit type; allow by extension
      /\.(jpe?g|png|webp)$/i.test(file.name || '');
    if (!okMime) {
      return 'Formato no permitido. Usa JPG, PNG o WebP.';
    }
    if (file.size > AVATAR_MAX_BYTES) {
      return 'La imagen supera el máximo de 2 MB.';
    }
    return null;
  }

  /**
   * Experiencia pública — GET /portfolio/experience → { items: ExperienceItemDTO[] }.
   * Orden UI: order ASC, luego start_date DESC (también confía en orden del API).
   * Sin mock: vacío hasta que el BE (PR #48) + seed estén desplegados.
   */
  getExperience(): Observable<ExperienceItem[]> {
    if (!this.apiAvailability.isApiConfigured()) {
      return of([]);
    }
    return this.api.get<ExperienceListResponse>('/portfolio/experience').pipe(
      map(raw => this.normalizeExperienceResponse(raw)),
      catchError(err => {
        this.apiAvailability.noteRequestFailure(err);
        throw err;
      })
    );
  }

  /**
   * Capacidades públicas — GET /portfolio/capabilities → { roles, skills:[{name,category}] }.
   * Preferir este endpoint. No inventar skills desde profile.stack_items (legacy aparte).
   * Sin endpoint / error: lista vacía honesta.
   */
  getCapabilities(): Observable<CapabilityChip[]> {
    if (!this.apiAvailability.isApiConfigured()) {
      return of([]);
    }
    return this.api.get<CapabilitiesResponse>('/portfolio/capabilities').pipe(
      map(raw => this.mapCapabilitiesResponse(raw)),
      catchError(err => {
        this.apiAvailability.noteRequestFailure(err);
        throw err;
      })
    );
  }

  /** Capa de mapping única: CapabilitiesDTO → chips (roles + skills). */
  mapCapabilitiesResponse(raw: CapabilitiesResponse | null | undefined): CapabilityChip[] {
    if (!raw || typeof raw !== 'object') {
      return [];
    }
    const roles = (raw.roles ?? [])
      .map(r => String(r ?? '').trim())
      .filter(Boolean)
      .map(label => ({ label, kind: 'role' as const }));

    const skills = (raw.skills ?? [])
      .map(s => this.normalizeSkill(s))
      .filter((s): s is CapabilitySkill => s !== null)
      .map(s => ({
        label: s.name,
        kind: 'skill' as const,
        category: s.category
      }));

    return [...roles, ...skills];
  }

  normalizeExperienceResponse(raw: ExperienceListResponse | ExperienceItem[] | null | undefined): ExperienceItem[] {
    let list: ExperienceItem[] = [];
    if (Array.isArray(raw)) {
      list = raw;
    } else if (raw && Array.isArray(raw.items)) {
      list = raw.items;
    }
    return list
      .map((item, index) => this.normalizeExperienceItem(item, index))
      .filter((item): item is ExperienceItem => item !== null)
      .sort((a, b) => {
        const orderDiff = (a.order ?? 0) - (b.order ?? 0);
        if (orderDiff !== 0) return orderDiff;
        return this.compareStartDateDesc(a.start_date, b.start_date);
      });
  }

  private normalizeSkill(skill: CapabilitySkill | null | undefined): CapabilitySkill | null {
    if (!skill || typeof skill !== 'object') return null;
    const name = String(skill.name ?? '').trim();
    if (!name) return null;
    return {
      name,
      category: String(skill.category ?? '').trim() || 'general'
    };
  }

  private normalizeExperienceItem(
    item: Partial<ExperienceItem> | null | undefined,
    index: number
  ): ExperienceItem | null {
    if (!item || typeof item !== 'object') return null;
    const title = String(item.title ?? '').trim();
    const summary = String(item.summary ?? '').trim();
    if (!title && !summary) return null;

    const linksRaw = (item.links ?? {}) as ExperienceLinks;
    const links: ExperienceLinks = {
      github: linksRaw.github ? String(linksRaw.github).trim() || null : null,
      demo: linksRaw.demo ? String(linksRaw.demo).trim() || null : null
    };

    return {
      id: String(item.id ?? index),
      title: title || 'Experiencia',
      organization: item.organization ?? null,
      kind: (item.kind as ExperienceItem['kind']) || 'project',
      location: item.location ?? null,
      start_date: String(item.start_date ?? ''),
      end_date: item.end_date ?? null,
      current: Boolean(item.current),
      summary,
      highlights: Array.isArray(item.highlights)
        ? item.highlights.map(h => String(h).trim()).filter(Boolean)
        : [],
      technologies: Array.isArray(item.technologies)
        ? item.technologies.map(t => String(t).trim()).filter(Boolean)
        : [],
      links,
      order: typeof item.order === 'number' ? item.order : index
    };
  }

  private compareStartDateDesc(a: string, b: string): number {
    const av = a || '';
    const bv = b || '';
    if (av === bv) return 0;
    return av < bv ? 1 : -1;
  }

  /**
   * Obtiene los roles desde la API.
   * Sin API: lista vacía (no inventar roles).
   */
  getRolesFromApi(): Observable<string[]> {
    if (!this.apiAvailability.isApiConfigured()) {
      return of([]);
    }
    return this.api.get<string[]>('/portfolio/roles').pipe(
      catchError(err => {
        this.apiAvailability.noteRequestFailure(err);
        return of([]);
      })
    );
  }

  /**
   * Obtiene el stack desde la API.
   * Sin API: lista vacía (no inventar stack).
   */
  getStackFromApi(): Observable<string[]> {
    if (!this.apiAvailability.isApiConfigured()) {
      return of([]);
    }
    return this.api.get<string[]>('/portfolio/stack').pipe(
      catchError(err => {
        this.apiAvailability.noteRequestFailure(err);
        return of([]);
      })
    );
  }

  /**
   * Obtiene los about points desde la API.
   * Sin API: lista vacía.
   */
  getAboutPointsFromApi(): Observable<string[]> {
    if (!this.apiAvailability.isApiConfigured()) {
      return of([]);
    }
    return this.api.get<string[]>('/portfolio/about').pipe(
      catchError(err => {
        this.apiAvailability.noteRequestFailure(err);
        return of([]);
      })
    );
  }

  /**
   * Obtiene los highlights desde la API.
   * Sin API: no mostrar stats inventados (05+ / 25+ / 60+).
   */
  getHighlightsFromApi(): Observable<Highlight[]> {
    if (!this.apiAvailability.isApiConfigured()) {
      return of([]);
    }
    return this.api.get<Highlight[]>('/portfolio/highlights').pipe(
      catchError(err => {
        this.apiAvailability.noteRequestFailure(err);
        return of([]);
      })
    );
  }

  // Métodos síncronos: vacíos cuando no hay datos de API (honest UX)
  getTechnologies(): Technology[] {
    return [];
  }

  getHighlights(): Highlight[] {
    // No inventar métricas; solo API / perfil admin.
    return [];
  }

  getAboutPoints(): string[] {
    return [];
  }

  getRoles(): string[] {
    return [];
  }

  getStackItems(): string[] {
    return [];
  }
}
