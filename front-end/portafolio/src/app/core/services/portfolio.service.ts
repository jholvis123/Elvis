import { Injectable, inject } from '@angular/core';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Project, Technology, Highlight } from '../models';
import { ApiService } from './api.service';
import { ApiAvailabilityService } from './api-availability.service';

interface PortfolioProfileResponse {
  name: string;
  title: string;
  bio?: string;
  avatar_url?: string;
  roles: string[];
  stack_items: string[];
  about_points: string[];
  highlights: { label: string; value: string; icon?: string }[];
  social_links: Record<string, string>;
}

@Injectable({
  providedIn: 'root'
})
export class PortfolioService {
  private readonly api = inject(ApiService);
  private readonly apiAvailability = inject(ApiAvailabilityService);

  /**
   * Obtiene el perfil completo desde la API
   */
  getProfile(): Observable<PortfolioProfileResponse> {
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
    return this.api.get<PortfolioProfileResponse>('/portfolio/profile').pipe(
      catchError(err => {
        this.apiAvailability.noteRequestFailure(err);
        throw err;
      })
    );
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

  // DEPRECADO: Los proyectos ahora se cargan desde ProjectsService
  getProjects(): Project[] {
    console.warn('PortfolioService.getProjects() está deprecado. Usar ProjectsService.getFeaturedProjects()');
    return [];
  }

  getProjectById(_id: string): Project | undefined {
    console.warn('PortfolioService.getProjectById() está deprecado. Usar ProjectsService.getProjectById()');
    return undefined;
  }

  getProjectsByCategory(_category: Project['category']): Project[] {
    console.warn('PortfolioService.getProjectsByCategory() está deprecado.');
    return [];
  }

  getRoles(): string[] {
    return [];
  }

  getStackItems(): string[] {
    return [];
  }
}
