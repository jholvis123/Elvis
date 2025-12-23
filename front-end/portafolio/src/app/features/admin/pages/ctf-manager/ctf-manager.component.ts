import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
    selector: 'app-ctf-manager',
    standalone: true,
    imports: [CommonModule, RouterLink],
    template: `
    <div class="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      <div class="max-w-7xl mx-auto">
        <!-- Header -->
        <div class="flex justify-between items-center mb-8">
          <div>
            <h1 class="text-3xl font-bold text-white mb-2">Gestión de CTFs</h1>
            <p class="text-gray-400">Administra todos los challenges CTF</p>
          </div>
          <div class="flex gap-3">
            <a routerLink="/admin/dashboard" class="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition">
              ← Volver
            </a>
            <a routerLink="/ctf/admin/new" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium">
              + Nuevo CTF
            </a>
          </div>
        </div>

        <!-- Info Message -->
        <div class="bg-blue-500/10 border border-blue-500/30 rounded-lg p-6 text-center">
          <p class="text-blue-200">
            La gestión de CTFs se realiza desde <a routerLink="/ctf" class="text-blue-400 hover:text-blue-300 underline">la sección de CTF</a>
          </p>
        </div>
      </div>
    </div>
  `,
    styles: []
})
export class CtfManagerComponent { }
