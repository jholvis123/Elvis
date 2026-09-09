import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-loading-spinner',
    standalone: true,
    imports: [CommonModule],
    template: `
    <div class="flex justify-center items-center py-12" role="status" aria-live="polite">
      <div class="motion-safe-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      <span class="sr-only">Cargando…</span>
    </div>
  `,
    styles: [`
    .motion-safe-spin {
      animation: spin 1s linear infinite;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    @media (prefers-reduced-motion: reduce) {
      .motion-safe-spin {
        animation: none;
        opacity: 0.85;
      }
    }
  `]
})
export class LoadingSpinnerComponent { }
