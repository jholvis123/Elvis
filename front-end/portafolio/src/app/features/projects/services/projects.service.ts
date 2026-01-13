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
    status: 'draft' | 'published' | 'archived';
    featured: boolean;
    order: number;
    created_at: string;
    updated_at: string;
}

/**
 * Resumen de proyecto para cards del Home
 */
export interface ProjectSummary {
    id: string;
    title: string;
    short_description: string;
    image_url: string;
    technologies: string[];
    featured: boolean;
    created_at: string;
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
    status?: 'draft' | 'published' | 'archived';
}

@Injectable({
    providedIn: 'root'
})
export class ProjectsService {
    constructor(private api: ApiService) { }

    /**
     * Obtiene lista de proyectos públicos (solo publicados)
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
     * Obtiene TODOS los proyectos para admin (incluye drafts)
     */
    getAllProjectsAdmin(params?: {
        page?: number;
        size?: number;
        status?: string;
    }): Observable<ProjectListResponse> {
        const queryParams: Record<string, string | number> = {
            page: params?.page || 1,
            size: params?.size || 100
        };
        if (params?.status) {
            queryParams['status'] = params.status;
        }
        return this.api.get<ProjectListResponse>('/projects/admin/all', queryParams);
    }

    /**
     * Obtiene proyectos destacados para el Home
     */
    getFeaturedProjects(limit: number = 5): Observable<ProjectSummary[]> {
        return this.api.get<ProjectSummary[]>('/projects/featured', { limit }).pipe(
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
     * Cambia el estado de un proyecto
     */
    updateProjectStatus(id: string, status: 'draft' | 'published' | 'archived'): Observable<Project> {
        return this.api.put<Project>(`/projects/${id}`, { status });
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
