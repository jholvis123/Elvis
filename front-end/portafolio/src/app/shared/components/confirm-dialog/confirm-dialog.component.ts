import {
  Component,
  ElementRef,
  EventEmitter,
  HostListener,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
  ViewChild
} from '@angular/core';
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
      [attr.aria-labelledby]="titleId"
      [attr.aria-describedby]="messageId"
      (click)="onBackdrop()">
      <div
        #dialogPanel
        class="card max-w-md w-full shadow-card outline-none"
        tabindex="-1"
        (click)="$event.stopPropagation()">
        <div class="flex items-start gap-3 mb-4">
          <app-icon name="exclamation-triangle" cssClass="w-6 h-6 text-warning flex-shrink-0 mt-0.5"></app-icon>
          <h3 [id]="titleId" class="text-xl font-bold text-textPrimary">{{ title }}</h3>
        </div>
        <p [id]="messageId" class="text-textSecondary mb-2">{{ message }}</p>
        <p *ngIf="warning" class="text-danger text-sm mb-6">{{ warning }}</p>
        <ng-content></ng-content>
        <div class="flex flex-col-reverse sm:flex-row gap-3 justify-end mt-6">
          <button #cancelBtn type="button" class="btn-outline w-full sm:w-auto" (click)="cancelled.emit()">
            {{ cancelLabel }}
          </button>
          <button
            #confirmBtn
            type="button"
            class="w-full sm:w-auto px-6 py-2 rounded font-semibold bg-danger text-white hover:bg-red-600 transition-all duration-300 min-h-[44px] inline-flex items-center justify-center"
            (click)="confirmed.emit()">
            {{ confirmLabel }}
          </button>
        </div>
      </div>
    </div>
  `
})
export class ConfirmDialogComponent implements OnChanges {
  @Input() open = false;
  @Input() title = 'Confirmar acción';
  @Input() message = '¿Deseas continuar?';
  @Input() warning = 'Esta acción no se puede deshacer.';
  @Input() confirmLabel = 'Eliminar';
  @Input() cancelLabel = 'Cancelar';
  @Output() confirmed = new EventEmitter<void>();
  @Output() cancelled = new EventEmitter<void>();

  @ViewChild('dialogPanel') dialogPanel?: ElementRef<HTMLElement>;
  @ViewChild('cancelBtn') cancelBtn?: ElementRef<HTMLButtonElement>;

  readonly titleId = `confirm-title-${Math.random().toString(36).slice(2, 8)}`;
  readonly messageId = `confirm-message-${Math.random().toString(36).slice(2, 8)}`;

  private previouslyFocused: HTMLElement | null = null;

  ngOnChanges(changes: SimpleChanges): void {
    if (!changes['open']) {
      return;
    }

    if (this.open) {
      this.previouslyFocused = document.activeElement as HTMLElement | null;
      setTimeout(() => this.focusInitial(), 0);
    } else if (this.previouslyFocused) {
      this.previouslyFocused.focus();
      this.previouslyFocused = null;
    }
  }

  onBackdrop(): void {
    this.cancelled.emit();
  }

  @HostListener('document:keydown', ['$event'])
  onKeydown(event: KeyboardEvent): void {
    if (!this.open) {
      return;
    }

    if (event.key === 'Escape') {
      event.preventDefault();
      this.cancelled.emit();
      return;
    }

    if (event.key !== 'Tab') {
      return;
    }

    const focusable = this.getFocusable();
    if (focusable.length === 0) {
      event.preventDefault();
      this.dialogPanel?.nativeElement.focus();
      return;
    }

    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const active = document.activeElement;

    if (event.shiftKey && active === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && active === last) {
      event.preventDefault();
      first.focus();
    }
  }

  private focusInitial(): void {
    const target = this.cancelBtn?.nativeElement || this.getFocusable()[0] || this.dialogPanel?.nativeElement;
    target?.focus();
  }

  private getFocusable(): HTMLElement[] {
    const root = this.dialogPanel?.nativeElement;
    if (!root) {
      return [];
    }

    return Array.from(
      root.querySelectorAll<HTMLElement>(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      )
    ).filter(el => !el.hasAttribute('disabled'));
  }
}
