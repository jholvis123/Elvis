import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Technology, Highlight, PortfolioProfile } from '../models';
import { ApiService } from './api.service';

export type { PortfolioProfile };

@Injectable({
  providedIn: 'root'
})
export class PortfolioService {

  constructor(private api: ApiService) {}

  // Datos de respaldo (fallback)
  private readonly fallbackTechnologies: Technology[] = [
    { name: 'Angular', category: 'frontend' },
    { name: '.NET', category: 'backend' },
    { name: 'Node.js', category: 'backend' },
    { name: 'Ciberseguridad', category: 'security' },
    { name: 'Pentesting', category: 'security' },
    { name: 'CTF', category: 'security' }
  ];

  private readonly fallbackHighlights: Highlight[] = [
    { label: 'Años de experiencia', value: '05+' },
    { label: 'Proyectos entregados', value: '25+' },
    { label: 'CTF resueltos', value: '60+' }
  ];

  private readonly fallbackAboutPoints: string[] = [
    'Construyo aplicaciones seguras y mantenibles con foco en rendimiento.',
    'Integro prácticas de ciberseguridad desde el diseño hasta el despliegue.',
    'Disfruto escribir y compartir writeups y laboratorios prácticos.'
  ];

  // NOTA: Los proyectos se cargan dinámicamente desde la API
  // No existen datos hardcodeados para proyectos

  private readonly fallbackRoles: string[] = [
    'Desarrollador Fullstack',
    'Especialista en Ciberseguridad',
    'CTF Player',
    'DevSecOps Engineer'
  ];

  private readonly fallbackStackItems: string[] = [
    'Angular', 'Tailwind', '.NET', 'Node.js', 'Azure', 'DevSecOps'
  ];

  /**
   * Obtiene el perfil completo desde la API
   */
  getProfile(): Observable<PortfolioProfile> {
    return this.api.get<PortfolioProfile>('/portfolio/profile');
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
   * Obtiene los roles desde la API
   */
  getRolesFromApi(): Observable<string[]> {
    return this.api.get<string[]>('/portfolio/roles').pipe(
      catchError(() => of(this.fallbackRoles))
    );
  }

  /**
   * Obtiene el stack desde la API
   */
  getStackFromApi(): Observable<string[]> {
    return this.api.get<string[]>('/portfolio/stack').pipe(
      catchError(() => of(this.fallbackStackItems))
    );
  }

  /**
   * Obtiene los about points desde la API
   */
  getAboutPointsFromApi(): Observable<string[]> {
    return this.api.get<string[]>('/portfolio/about').pipe(
      catchError(() => of(this.fallbackAboutPoints))
    );
  }

  /**
   * Obtiene los highlights desde la API
   */
  getHighlightsFromApi(): Observable<Highlight[]> {
    return this.api.get<Highlight[]>('/portfolio/highlights').pipe(
      catchError(() => of(this.fallbackHighlights))
    );
  }

  // Métodos síncronos para compatibilidad
  getTechnologies(): Technology[] {
    return [...this.fallbackTechnologies];
  }

  getHighlights(): Highlight[] {
    return [...this.fallbackHighlights];
  }

  getAboutPoints(): string[] {
    return [...this.fallbackAboutPoints];
  }

  getRoles(): string[] {
    return [...this.fallbackRoles];
  }

  getStackItems(): string[] {
    return [...this.fallbackStackItems];
  }
}
