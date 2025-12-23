import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { ApiService } from '../../../core/services/api.service';

export interface Project {
    id: string;
    title: string;
    description: string;
    short_description: string;
    image_url: string;
    github_url?: string;
    demo_url?: string;
    technologies: string[];
    highlights: string[];
    status: 'draft' | 'published';
    featured: boolean;
    order: number;
    created_at: string;
    updated_at: string;
}

export interface ProjectListResponse {
    items: Project[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

export interface ProjectForm {
    title: string;
    description: string;
    short_description: string;
    image_url: string;
    github_url?: string;
    demo_url?: string;
    technologies: string[];
    highlights: string[];
    featured?: boolean;
    order?: number;
}

@Injectable({
    providedIn: 'root'
})
export class ProjectsService {
    constructor(private api: ApiService) { }

    /**
     * Obtiene lista de proyectos con paginación y filtros
     */
    getProjects(params?: {
        page?: number;
        size?: number;
        featured?: boolean;
        technology?: string;
    }): Observable<ProjectListResponse> {
        return this.api.get<ProjectListResponse>('/projects', {
            page: params?.page || 1,
            size: params?.size || 10,
            ...(params?.featured !== undefined && { featured: params.featured }),
            ...(params?.technology && { technology: params.technology })
        });
    }

    /**
     * Obtiene proyectos destacados
     */
    getFeaturedProjects(limit: number = 5): Observable<Project[]> {
        return this.api.get<Project[]>('/projects/featured', { limit }).pipe(
            catchError(() => of([]))
        );
    }

    /**
     * Obtiene un proyecto por ID
     */
    getProjectById(id: string): Observable<Project> {
        return this.api.get<Project>(`/projects/${id}`);
    }

    /**
     * Crea un nuevo proyecto (admin)
     */
    createProject(data: ProjectForm): Observable<Project> {
        return this.api.post<Project>('/projects', data);
    }

    /**
     * Actualiza un proyecto existente (admin)
     */
    updateProject(id: string, data: Partial<ProjectForm>): Observable<Project> {
        return this.api.put<Project>(`/projects/${id}`, data);
    }

    /**
     * Publica un proyecto (admin)
     */
    publishProject(id: string): Observable<Project> {
        return this.api.post<Project>(`/projects/${id}/publish`, {});
    }

    /**
     * Elimina un proyecto (admin)
     */
    deleteProject(id: string): Observable<void> {
        return this.api.delete<void>(`/projects/${id}`);
    }

    /**
     * Obtiene resumen de tecnologías
     */
    getTechnologies(): Observable<{ technology: string; count: number }[]> {
        return this.api.get<{ technology: string; count: number }[]>('/projects/technologies').pipe(
            catchError(() => of([]))
        );
    }
}
