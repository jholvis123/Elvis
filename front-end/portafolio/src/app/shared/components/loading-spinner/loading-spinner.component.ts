import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

export type LoadingSpinnerSize = 'md' | 'lg';

@Component({
    selector: 'app-loading-spinner',
    standalone: true,
    imports: [CommonModule],
    template: `
    <div
      class="flex flex-col justify-center items-center py-12 gap-3"
      role="status"
      aria-live="polite"
      [attr.aria-label]="label">
      <div
        class="motion-safe-spin rounded-full border-primary"
        [ngClass]="size === 'lg'
          ? 'h-16 w-16 border-t-4 border-b-4'
          : 'h-12 w-12 border-t-2 border-b-2'"
        aria-hidden="true"></div>
      <span class="sr-only">{{ label }}</span>
      <p *ngIf="showLabel" class="text-textSecondary text-sm m-0">{{ label }}</p>
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
        border-style: dashed;
      }
    }
  `]
})
export class LoadingSpinnerComponent {
    /** Visible/SR label for the loading state. */
    @Input() label = 'Cargando…';
    /** Page loaders use md; leaderboard-style emphasis uses lg. */
    @Input() size: LoadingSpinnerSize = 'md';
    /** When true, also show the label under the ring (not only sr-only). */
    @Input() showLabel = false;
}
