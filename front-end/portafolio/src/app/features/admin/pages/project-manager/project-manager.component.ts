import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ProjectsService, Project } from '../../../projects/services/projects.service';
import { NotificationService } from '../../../../core/services/notification.service';

@Component({
    selector: 'app-project-manager',
    standalone: true,
    imports: [CommonModule, RouterLink],
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

        <!-- Projects Table -->
        <div class="bg-white/5 backdrop-blur-lg rounded-xl border border-white/10 overflow-hidden">
          <table class="w-full">
            <thead class="bg-white/10">
              <tr>
                <th class="text-left px-6 py-4 text-white font-semibold">Título</th>
                <th class="text-left px-6 py-4 text-white font-semibold">Tecnologías</th>
                <th class="text-center px-6 py-4 text-white font-semibold">Destacado</th>
                <th class="text-center px-6 py-4 text-white font-semibold">Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let project of projects" class="border-t border-white/10 hover:bg-white/5 transition">
                <td class="px-6 py-4">
                  <div>
                    <p class="text-white font-medium">{{ project.title }}</p>
                    <p class="text-gray-400 text-sm">{{ project.short_description }}</p>
                  </div>
                </td>
                <td class="px-6 py-4">
                  <div class="flex flex-wrap gap-1">
                    <span *ngFor="let tech of project.technologies.slice(0, 3)" class="px-2 py-1 bg-purple-500/20 text-purple-300 rounded text-xs">
                      {{ tech }}
                    </span>
                    <span *ngIf="project.technologies.length > 3" class="text-gray-500 text-xs">
                      +{{ project.technologies.length - 3 }}
                    </span>
                  </div>
                </td>
                <td class="px-6 py-4 text-center">
                  <span *ngIf="project.featured" class="text-yellow-400">⭐</span>
                  <span *ngIf="!project.featured" class="text-gray-600">-</span>
                </td>
                <td class="px-6 py-4">
                  <div class="flex justify-center gap-2">
                    <a [routerLink]="['/projects', project.id]" class="p-2 text-blue-400 hover:text-blue-300" title="Ver">
                      👁️
                    </a>
                    <a [routerLink]="['/projects', project.id, 'edit']" class="p-2 text-purple-400 hover:text-purple-300" title="Editar">
                      ✏️
                    </a>
                    <button (click)="deleteProject(project.id)" class="p-2 text-red-400 hover:text-red-300" title="Eliminar">
                      🗑️
                    </button>
                  </div>
                </td>
              </tr>
              <tr *ngIf="projects.length === 0">
                <td colspan="4" class="px-6 py-12 text-center text-gray-500">
                  No hay proyectos creados aún
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
    styles: []
})
export class ProjectManagerComponent implements OnInit {
    projects: Project[] = [];
    loading = false;

    constructor(
        private projectsService: ProjectsService,
        private notificationService: NotificationService
    ) { }

    ngOnInit(): void {
        this.loadProjects();
    }

    loadProjects(): void {
        this.loading = true;
        this.projectsService.getProjects({ page: 1, size: 100 }).subscribe({
            next: (response) => {
                this.projects = response.items;
                this.loading = false;
            },
            error: () => {
                this.notificationService.error('Error al cargar proyectos');
                this.loading = false;
            }
        });
    }

    deleteProject(id: string): void {
        if (!confirm('¿Estás seguro de eliminar este proyecto?')) return;

        this.projectsService.deleteProject(id).subscribe({
            next: () => {
                this.notificationService.success('Proyecto eliminado exitosamente');
                this.loadProjects();
            },
            error: () => {
                this.notificationService.error('Error al eliminar el proyecto');
            }
        });
    }
}
