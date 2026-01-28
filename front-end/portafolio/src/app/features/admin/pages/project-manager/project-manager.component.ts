import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ProjectsService, Project } from '../../../projects/services/projects.service';
import { NotificationService } from '../../../../core/services/notification.service';

@Component({
    selector: 'app-project-manager',
    standalone: true,
    imports: [CommonModule, RouterLink, FormsModule],
    templateUrl: './project-manager.component.html',
    styleUrls: ['./project-manager.component.scss']
})
export class ProjectManagerComponent implements OnInit {
    projects: Project[] = [];
    filteredProjects: Project[] = [];
    loading = false;

    // Filters
    searchTerm = '';
    filterStatus = '';

    // Stats
    totalProjects = 0;
    publishedCount = 0;
    draftCount = 0;
    featuredCount = 0;

    // Delete modal
    showDeleteModal = false;
    projectToDelete: Project | null = null;

    private searchTimeout: any;

    constructor(
        private projectsService: ProjectsService,
        private notificationService: NotificationService
    ) { }

    ngOnInit(): void {
        this.loadProjects();
    }

    loadProjects(): void {
        this.loading = true;
        
        const params: { page: number; size: number; status?: string } = {
            page: 1,
            size: 100
        };
        if (this.filterStatus) {
            params.status = this.filterStatus;
        }

        this.projectsService.getAllProjectsAdmin(params).subscribe({
            next: (response) => {
                this.projects = response.items;
                this.totalProjects = response.total;
                this.applySearch();
                this.updateStats();
                this.loading = false;
            },
            error: (err) => {
                console.error('Error loading projects:', err);
                this.notificationService.error('Error al cargar los proyectos');
                this.loading = false;
            }
        });
    }

    applySearch(): void {
        if (!this.searchTerm.trim()) {
            this.filteredProjects = [...this.projects];
        } else {
            const term = this.searchTerm.toLowerCase();
            this.filteredProjects = this.projects.filter(p =>
                p.title.toLowerCase().includes(term) ||
                p.short_description?.toLowerCase().includes(term)
            );
        }
    }

    updateStats(): void {
        this.publishedCount = this.projects.filter(p => p.status === 'published').length;
        this.draftCount = this.projects.filter(p => p.status === 'draft').length;
        this.featuredCount = this.projects.filter(p => p.featured).length;
    }

    onSearch(): void {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.applySearch();
        }, 300);
    }

    toggleFeatured(project: Project): void {
        const newState = !project.featured;
        this.projectsService.updateProject(project.id, { featured: newState }).subscribe({
            next: () => {
                project.featured = newState;
                this.updateStats();
                this.notificationService.success(
                    newState ? 'Proyecto destacado' : 'Proyecto removido de destacados'
                );
            },
            error: () => {
                this.notificationService.error('Error al cambiar estado del proyecto');
            }
        });
    }

    publishProject(project: Project): void {
        this.projectsService.publishProject(project.id).subscribe({
            next: () => {
                project.status = 'published';
                this.updateStats();
                this.notificationService.success('Proyecto publicado exitosamente');
            },
            error: (err) => {
                const message = err.error?.detail || 'Error al publicar el proyecto';
                this.notificationService.error(message);
            }
        });
    }

    archiveProject(project: Project): void {
        this.projectsService.updateProjectStatus(project.id, 'archived').subscribe({
            next: () => {
                project.status = 'archived';
                this.updateStats();
                this.notificationService.success('Proyecto archivado');
            },
            error: () => {
                this.notificationService.error('Error al archivar el proyecto');
            }
        });
    }

    confirmDelete(project: Project): void {
        this.projectToDelete = project;
        this.showDeleteModal = true;
    }

    cancelDelete(): void {
        this.showDeleteModal = false;
        this.projectToDelete = null;
    }

    executeDelete(): void {
        if (!this.projectToDelete) return;

        this.projectsService.deleteProject(this.projectToDelete.id).subscribe({
            next: () => {
                this.notificationService.success('Proyecto eliminado exitosamente');
                this.showDeleteModal = false;
                this.projectToDelete = null;
                this.loadProjects();
            },
            error: () => {
                this.notificationService.error('Error al eliminar el proyecto');
            }
        });
    }

    // UI Helpers
    getStatusClass(status: string): string {
        const classes: Record<string, string> = {
            'draft': 'bg-yellow-500/20 text-yellow-300',
            'published': 'bg-green-500/20 text-green-300',
            'archived': 'bg-gray-500/20 text-gray-300'
        };
        return classes[status] || 'bg-gray-500/20 text-gray-300';
    }

    getStatusLabel(status: string): string {
        const labels: Record<string, string> = {
            'draft': 'Borrador',
            'published': 'Publicado',
            'archived': 'Archivado'
        };
        return labels[status] || status;
    }
}
