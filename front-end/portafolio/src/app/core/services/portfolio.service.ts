import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { Project, Technology, Highlight } from '../models';
import { ApiService } from './api.service';

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

  private readonly fallbackProjects: Project[] = [
    {
      id: 'gestion-segura',
      title: 'Plataforma de Gestión Segura',
      description: 'Suite modular para operaciones internas con monitoreo y trazabilidad.',
      tags: ['Angular', '.NET', 'Azure'],
      cta: 'Ver caso',
      year: 2024,
      category: 'web'
    },
    {
      id: 'dashboard-security',
      title: 'Dashboard de Ciberseguridad',
      description: 'Alertas en tiempo real, hardening y flujos de respuesta.',
      tags: ['Node.js', 'SIEM', 'DevSecOps'],
      cta: 'Ver demo',
      year: 2024,
      category: 'security'
    },
    {
      id: 'lab-ctf',
      title: 'Laboratorio CTF',
      description: 'Retos propios, writeups y automatización de pruebas ofensivas.',
      tags: ['CTF', 'Pentesting', 'Automation'],
      cta: 'Explorar',
      year: 2024,
      category: 'ctf'
    }
  ];

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
  getProfile(): Observable<PortfolioProfileResponse> {
    return this.api.get<PortfolioProfileResponse>('/portfolio/profile');
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

  getProjects(): Project[] {
    return [...this.fallbackProjects];
  }

  getProjectById(id: string): Project | undefined {
    return this.fallbackProjects.find(p => p.id === id);
  }

  getProjectsByCategory(category: Project['category']): Project[] {
    return this.fallbackProjects.filter(p => p.category === category);
  }

  getRoles(): string[] {
    return [...this.fallbackRoles];
  }

  getStackItems(): string[] {
    return [...this.fallbackStackItems];
  }
}
