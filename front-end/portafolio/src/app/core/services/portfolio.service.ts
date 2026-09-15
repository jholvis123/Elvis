import { Injectable, inject } from '@angular/core';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import {
  Technology,
  Highlight,
  PortfolioProfile,
  ExperienceItem,
  ExperienceListResponse,
  ExperienceLinks,
  CapabilityChip,
  CapabilitiesResponse,
  CapabilitySkill
} from '../models';
import { ApiService } from './api.service';
import { ApiAvailabilityService } from './api-availability.service';

export type { PortfolioProfile };

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
