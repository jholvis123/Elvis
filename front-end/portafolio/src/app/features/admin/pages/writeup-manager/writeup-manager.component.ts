import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { WriteupsService, Writeup } from '../../../writeups/services/writeups.service';
import { NotificationService } from '../../../../core/services/notification.service';

@Component({
    selector: 'app-writeup-manager',
    standalone: true,
    imports: [CommonModule, RouterLink],
    template: `
    <div class="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      <div class="max-w-7xl mx-auto">
        <!-- Header -->
        <div class="flex justify-between items-center mb-8">
          <div>
            <h1 class="text-3xl font-bold text-white mb-2">Gestión de Writeups</h1>
            <p class="text-gray-400">Administra todos los writeups CTF</p>
          </div>
          <div class="flex gap-3">
            <a routerLink="/admin/dashboard" class="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition">
              ← Volver
            </a>
            <a routerLink="/writeups/new" class="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium">
              + Nuevo Writeup
            </a>
          </div>
        </div>

        <!-- Writeups Table -->
        <div class="bg-white/5 backdrop-blur-lg rounded-xl border border-white/10 overflow-hidden">
          <table class="w-full">
            <thead class="bg-white/10">
              <tr>
                <th class="text-left px-6 py-4 text-white font-semibold">Título</th>
                <th class="text-left px-6 py-4 text-white font-semibold">Herramientas</th>
                <th class="text-center px-6 py-4 text-white font-semibold">Vistas</th>
                <th class="text-center px-6 py-4 text-white font-semibold">Estado</th>
                <th class="text-center px-6 py-4 text-white font-semibold">Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let writeup of writeups" class="border-t border-white/10 hover:bg-white/5 transition">
                <td class="px-6 py-4">
                  <div>
                    <p class="text-white font-medium">{{ writeup.title }}</p>
                    <p class="text-gray-400 text-sm line-clamp-1">{{ writeup.summary }}</p>
                  </div>
                </td>
                <td class="px-6 py-4">
                  <div class="flex flex-wrap gap-1">
                    <span *ngFor="let tool of writeup.tools_used.slice(0, 3)" class="px-2 py-1 bg-blue-500/20 text-blue-300 rounded text-xs">
                      {{ tool }}
                    </span>
                    <span *ngIf="writeup.tools_used.length > 3" class="text-gray-500 text-xs">
                      +{{ writeup.tools_used.length - 3 }}
                    </span>
                  </div>
                </td>
                <td class="px-6 py-4 text-center text-gray-300">
                  {{ writeup.views }}
                </td>
                <td class="px-6 py-4 text-center">
                  <span *ngIf="writeup.status === 'published'" class="px-2 py-1 bg-green-500/20 text-green-300 rounded text-xs">
                    Publicado
                  </span>
                  <span *ngIf="writeup.status === 'draft'" class="px-2 py-1 bg-yellow-500/20 text-yellow-300 rounded text-xs">
                    Borrador
                  </span>
                </td>
                <td class="px-6 py-4">
                  <div class="flex justify-center gap-2">
                    <a [routerLink]="['/writeups', writeup.id]" class="p-2 text-blue-400 hover:text-blue-300" title="Ver">
                      👁️
                    </a>
                    <a [routerLink]="['/writeups', writeup.id, 'edit']" class="p-2 text-purple-400 hover:text-purple-300" title="Editar">
                      ✏️
                    </a>
                    <button *ngIf="writeup.status === 'draft'" (click)="publishWriteup(writeup.id)" class="p-2 text-green-400 hover:text-green-300" title="Publicar">
                      ✅
                    </button>
                    <button (click)="deleteWriteup(writeup.id)" class="p-2 text-red-400 hover:text-red-300" title="Eliminar">
                      🗑️
                    </button>
                  </div>
                </td>
              </tr>
              <tr *ngIf="writeups.length === 0">
                <td colspan="5" class="px-6 py-12 text-center text-gray-500">
                  No hay writeups creados aún
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
export class WriteupManagerComponent implements OnInit {
    writeups: Writeup[] = [];
    loading = false;

    constructor(
        private writeupsService: WriteupsService,
        private notificationService: NotificationService
    ) { }

    ngOnInit(): void {
        this.loadWriteups();
    }

    loadWriteups(): void {
        this.loading = true;
        this.writeupsService.getWriteups({ page: 1, size: 100 }).subscribe({
            next: (response) => {
                this.writeups = response.items;
                this.loading = false;
            },
            error: () => {
                this.notificationService.error('Error al cargar writeups');
                this.loading = false;
            }
        });
    }

    publishWriteup(id: string): void {
        this.writeupsService.publishWriteup(id).subscribe({
            next: () => {
                this.notificationService.success('Writeup publicado exitosamente');
                this.loadWriteups();
            },
            error: () => {
                this.notificationService.error('Error al publicar el writeup');
            }
        });
    }

    deleteWriteup(id: string): void {
        if (!confirm('¿Estás seguro de eliminar este writeup?')) return;

        this.writeupsService.deleteWriteup(id).subscribe({
            next: () => {
                this.notificationService.success('Writeup eliminado exitosamente');
                this.loadWriteups();
            },
            error: () => {
                this.notificationService.error('Error al eliminar el writeup');
            }
        });
    }
}
