import { Injectable, inject } from '@angular/core';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Technology, Highlight, PortfolioProfile } from '../models';
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
