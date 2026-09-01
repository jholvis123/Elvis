import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { IconComponent } from '@shared/icons/icon.component';

@Component({
  selector: 'app-not-found',
  standalone: true,
  imports: [CommonModule, RouterLink, IconComponent],
  template: `
    <section class="section min-h-[60vh] flex items-center">
      <div class="max-w-xl mx-auto px-6 text-center space-y-6">
        <p class="eyebrow">Error 404</p>
        <h1 class="section-heading">Página no encontrada</h1>
        <p class="muted-text">
          La ruta que buscas no existe o fue movida. Vuelve al inicio para continuar navegando.
        </p>
        <div class="flex justify-center">
          <a routerLink="/" class="btn-primary inline-flex items-center gap-2">
            <app-icon name="chevron-left" cssClass="w-4 h-4"></app-icon>
            Volver al inicio
          </a>
        </div>
      </div>
    </section>
  `
})
export class NotFoundComponent {}
