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
    template: `
    <div class="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      <div class="max-w-7xl mx-auto">
        <!-- Header -->
        <div class="flex justify-between items-center mb-8">
          <div>
            <h1 class="text-3xl font-bold text-white mb-2">Gestión de Proyectos</h1>
            <p class="text-gray-400">Administra todos los proyectos del portafolio</p>
          </div>
          <div class="flex gap-3">
            <a routerLink="/admin/dashboard" class="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition">
              ← Volver
            </a>
            <a routerLink="/projects/new" class="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition font-medium">
              + Nuevo Proyecto
            </a>
          </div>
        </div>

        <!-- Filters -->
        <div class="bg-white/5 backdrop-blur-lg rounded-xl border border-white/10 p-4 mb-6">
          <div class="flex flex-wrap gap-4 items-center">
            <div class="flex-1 min-w-[200px]">
              <input
                type="text"
                [(ngModel)]="searchTerm"
                (input)="onSearch()"
                placeholder="Buscar por título..."
                class="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500"
              />
            </div>
            <select
              [(ngModel)]="filterStatus"
              (change)="loadProjects()"
              class="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-500"
            >
              <option value="">Todos los estados</option>
              <option value="draft">Borrador</option>
              <option value="published">Publicado</option>
              <option value="archived">Archivado</option>
            </select>
          </div>
        </div>

        <!-- Stats Summary -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div class="bg-white/5 backdrop-blur-lg rounded-xl border border-white/10 p-4 text-center">
            <p class="text-3xl font-bold text-white">{{ totalProjects }}</p>
            <p class="text-gray-400 text-sm">Total Proyectos</p>
          </div>
          <div class="bg-green-500/10 backdrop-blur-lg rounded-xl border border-green-500/30 p-4 text-center">
            <p class="text-3xl font-bold text-green-400">{{ publishedCount }}</p>
            <p class="text-gray-400 text-sm">Publicados</p>
          </div>
          <div class="bg-yellow-500/10 backdrop-blur-lg rounded-xl border border-yellow-500/30 p-4 text-center">
            <p class="text-3xl font-bold text-yellow-400">{{ draftCount }}</p>
            <p class="text-gray-400 text-sm">Borradores</p>
          </div>
          <div class="bg-purple-500/10 backdrop-blur-lg rounded-xl border border-purple-500/30 p-4 text-center">
            <p class="text-3xl font-bold text-purple-400">{{ featuredCount }}</p>
            <p class="text-gray-400 text-sm">Destacados</p>
          </div>
        </div>

        <!-- Loading State -->
        <div *ngIf="loading" class="flex justify-center py-12">
          <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
        </div>

        <!-- Projects Table -->
        <div *ngIf="!loading" class="bg-white/5 backdrop-blur-lg rounded-xl border border-white/10 overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead class="bg-white/10">
                <tr>
                  <th class="text-left px-6 py-4 text-white font-semibold">Título</th>
                  <th class="text-left px-4 py-4 text-white font-semibold">Tecnologías</th>
                  <th class="text-center px-4 py-4 text-white font-semibold">Estado</th>
                  <th class="text-center px-4 py-4 text-white font-semibold">Destacado</th>
                  <th class="text-center px-4 py-4 text-white font-semibold">Acciones</th>
                </tr>
              </thead>
              <tbody>
                <tr *ngFor="let project of filteredProjects" class="border-t border-white/10 hover:bg-white/5 transition">
                  <td class="px-6 py-4">
                    <div>
                      <p class="text-white font-medium">{{ project.title }}</p>
                      <p class="text-gray-400 text-sm line-clamp-1">{{ project.short_description }}</p>
                    </div>
                  </td>
                  <td class="px-4 py-4">
                    <div class="flex flex-wrap gap-1">
                      <span *ngFor="let tech of project.technologies.slice(0, 3)" class="px-2 py-1 bg-purple-500/20 text-purple-300 rounded text-xs">
                        {{ tech }}
                      </span>
                      <span *ngIf="project.technologies.length > 3" class="text-gray-500 text-xs">
                        +{{ project.technologies.length - 3 }}
                      </span>
                    </div>
                  </td>
                  <td class="px-4 py-4 text-center">
                    <span [class]="getStatusClass(project.status)" class="px-2 py-1 rounded text-xs font-medium">
                      {{ getStatusLabel(project.status) }}
                    </span>
                  </td>
                  <td class="px-4 py-4 text-center">
                    <button
                      (click)="toggleFeatured(project)"
                      [class]="project.featured ? 'text-yellow-400 hover:text-yellow-300' : 'text-gray-500 hover:text-gray-400'"
                      [title]="project.featured ? 'Quitar de destacados' : 'Destacar'"
                    >
                      <span *ngIf="project.featured">⭐</span>
                      <span *ngIf="!project.featured">☆</span>
                    </button>
                  </td>
                  <td class="px-4 py-4">
                    <div class="flex justify-center gap-2">
                      <a [routerLink]="['/projects', project.id]" class="p-2 text-blue-400 hover:text-blue-300" title="Ver">
                        👁️
                      </a>
                      <a [routerLink]="['/projects', project.id, 'edit']" class="p-2 text-purple-400 hover:text-purple-300" title="Editar">
                        ✏️
                      </a>
                      <button
                        *ngIf="project.status === 'draft'"
                        (click)="publishProject(project)"
                        class="p-2 text-green-400 hover:text-green-300"
                        title="Publicar"
                      >
                        🚀
                      </button>
                      <button
                        *ngIf="project.status === 'published'"
                        (click)="archiveProject(project)"
                        class="p-2 text-orange-400 hover:text-orange-300"
                        title="Archivar"
                      >
                        📦
                      </button>
                      <button
                        (click)="confirmDelete(project)"
                        class="p-2 text-red-400 hover:text-red-300"
                        title="Eliminar"
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
                <tr *ngIf="filteredProjects.length === 0">
                  <td colspan="5" class="px-6 py-12 text-center text-gray-500">
                    <div class="flex flex-col items-center gap-4">
                      <span class="text-4xl">📁</span>
                      <p>No hay proyectos creados aún</p>
                      <a routerLink="/projects/new" class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition">
                        Crear primer proyecto
                      </a>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div *ngIf="showDeleteModal" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div class="bg-slate-800 rounded-xl border border-white/10 p-6 max-w-md w-full">
        <h3 class="text-xl font-bold text-white mb-4">⚠️ Confirmar eliminación</h3>
        <p class="text-gray-300 mb-2">
          ¿Estás seguro de que deseas eliminar el proyecto <strong class="text-white">{{ projectToDelete?.title }}</strong>?
        </p>
        <p class="text-red-400 text-sm mb-6">Esta acción no se puede deshacer.</p>

        <div class="flex gap-3 justify-end">
          <button
            (click)="cancelDelete()"
            class="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition"
          >
            Cancelar
          </button>
          <button
            (click)="executeDelete()"
            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
          >
            Eliminar
          </button>
        </div>
      </div>
    </div>
  `,
    styles: [`
      select option {
        background-color: #1e293b;
        color: white;
      }
    `]
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
