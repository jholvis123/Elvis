import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IconComponent } from '../../icons/icon.component';

@Component({
  selector: 'app-confirm-dialog',
  standalone: true,
  imports: [CommonModule, IconComponent],
  template: `
    <div
      *ngIf="open"
      class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      [attr.aria-labelledby]="titleId">
      <div class="card max-w-md w-full shadow-card">
        <div class="flex items-start gap-3 mb-4">
          <app-icon name="exclamation-triangle" cssClass="w-6 h-6 text-warning flex-shrink-0 mt-0.5"></app-icon>
          <h3 [id]="titleId" class="text-xl font-bold text-textPrimary">{{ title }}</h3>
        </div>
        <p class="text-textSecondary mb-2">{{ message }}</p>
        <p *ngIf="warning" class="text-danger text-sm mb-6">{{ warning }}</p>
        <ng-content></ng-content>
        <div class="flex gap-3 justify-end mt-6">
          <button type="button" class="btn-outline" (click)="cancelled.emit()">
            {{ cancelLabel }}
          </button>
          <button
            type="button"
            class="px-6 py-2 rounded font-semibold bg-danger text-white hover:bg-red-600 transition-all duration-300"
            (click)="confirmed.emit()">
            {{ confirmLabel }}
          </button>
        </div>
      </div>
    </div>
  `
})
export class ConfirmDialogComponent {
  @Input() open = false;
  @Input() title = 'Confirmar acción';
  @Input() message = '¿Deseas continuar?';
  @Input() warning = 'Esta acción no se puede deshacer.';
  @Input() confirmLabel = 'Eliminar';
  @Input() cancelLabel = 'Cancelar';
  @Output() confirmed = new EventEmitter<void>();
  @Output() cancelled = new EventEmitter<void>();

  readonly titleId = `confirm-title-${Math.random().toString(36).slice(2, 8)}`;
}
