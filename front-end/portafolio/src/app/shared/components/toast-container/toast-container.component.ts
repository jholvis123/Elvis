import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NotificationService, Notification } from '../../../core/services/notification.service';
import { IconComponent, IconName } from '../../icons/icon.component';

@Component({
    selector: 'app-toast-container',
    standalone: true,
    imports: [CommonModule, IconComponent],
    template: `
    <div class="fixed top-4 right-4 z-50 space-y-2">
      <div
        *ngFor="let notification of notifications"
        class="toast-notification animate-slide-in-right"
        [ngClass]="getToastClass(notification.type)"
      >
        <div class="flex items-start gap-3">
          <app-icon [name]="getIcon(notification.type)" cssClass="w-6 h-6 flex-shrink-0"></app-icon>
          <p class="flex-1 text-sm font-medium">{{ notification.message }}</p>
          <button
            type="button"
            (click)="removeNotification(notification.id)"
            class="text-white/70 hover:text-white transition"
            aria-label="Cerrar notificación"
          >
            <app-icon name="x-mark" cssClass="w-4 h-4"></app-icon>
          </button>
        </div>
      </div>
    </div>
  `,
    styles: [`
    .toast-notification {
      min-width: 300px;
      max-width: 400px;
      padding: 1rem;
      border-radius: var(--radius-lg, 0.75rem);
      box-shadow: var(--shadow-card, 0 10px 25px rgba(0, 0, 0, 0.3));
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      animation: slideInRight 0.3s ease-out;
      color: white;
    }

    .toast-success {
      background: linear-gradient(135deg, rgba(34, 197, 94, 0.9), rgba(5, 150, 105, 0.9));
    }

    .toast-error {
      background: linear-gradient(135deg, rgba(239, 68, 68, 0.9), rgba(220, 38, 38, 0.9));
    }

    .toast-warning {
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.9), rgba(217, 119, 6, 0.9));
    }

    .toast-info {
      background: linear-gradient(135deg, rgba(34, 211, 238, 0.9), rgba(6, 182, 212, 0.9));
    }

    @keyframes slideInRight {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }

    .animate-slide-in-right {
      animation: slideInRight 0.3s ease-out;
    }
  `]
})
export class ToastContainerComponent implements OnInit {
    private readonly notificationService = inject(NotificationService);
    private readonly destroyRef = inject(DestroyRef);
    notifications: Notification[] = [];

    ngOnInit(): void {
        this.notificationService.notifications$.pipe(
            takeUntilDestroyed(this.destroyRef)
        ).subscribe(notification => {
            this.notifications.push(notification);
            if (notification.duration) {
                setTimeout(() => this.removeNotification(notification.id), notification.duration);
            }
        });
    }

    removeNotification(id: string): void {
        this.notifications = this.notifications.filter(n => n.id !== id);
    }

    getToastClass(type: Notification['type']): string {
        return `toast-${type}`;
    }

    getIcon(type: Notification['type']): IconName {
        const icons: Record<Notification['type'], IconName> = {
            success: 'check-circle',
            error: 'x-circle',
            warning: 'exclamation-triangle',
            info: 'information-circle'
        };
        return icons[type];
    }
}
