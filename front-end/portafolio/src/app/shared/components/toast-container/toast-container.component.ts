import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NotificationService, Notification } from '../../../core/services/notification.service';

@Component({
    selector: 'app-toast-container',
    standalone: true,
    imports: [CommonModule],
    template: `
    <div class="fixed top-4 right-4 z-50 space-y-2">
      <div
        *ngFor="let notification of notifications"
        class="toast-notification animate-slide-in-right"
        [ngClass]="getToastClass(notification.type)"
        [@slideIn]
      >
        <div class="flex items-start gap-3">
          <span class="text-2xl flex-shrink-0">{{ getIcon(notification.type) }}</span>
          <p class="flex-1 text-sm font-medium">{{ notification.message }}</p>
          <button
            (click)="removeNotification(notification.id)"
            class="text-white/70 hover:text-white transition"
          >
            ✕
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
      border-radius: 0.75rem;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      animation: slideInRight 0.3s ease-out;
    }

    .toast-success {
      background: linear-gradient(135deg, rgba(16, 185, 129, 0.9), rgba(5, 150, 105, 0.9));
    }

    .toast-error {
      background: linear-gradient(135deg, rgba(239, 68, 68, 0.9), rgba(220, 38, 38, 0.9));
    }

    .toast-warning {
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.9), rgba(217, 119, 6, 0.9));
    }

    .toast-info {
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.9), rgba(124, 58, 237, 0.9));
    }

    @keyframes slideInRight {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }

    .animate-slide-in-right {
      animation: slideInRight 0.3s ease-out;
    }
  `]
})
export class ToastContainerComponent implements OnInit {
    notifications: Notification[] = [];

    constructor(private notificationService: NotificationService) { }

    ngOnInit(): void {
        this.notificationService.notifications$.subscribe(notification => {
            this.notifications.push(notification);

            // Auto-remove después de la duración especificada
            if (notification.duration) {
                setTimeout(() => {
                    this.removeNotification(notification.id);
                }, notification.duration);
            }
        });
    }

    removeNotification(id: string): void {
        this.notifications = this.notifications.filter(n => n.id !== id);
    }

    getToastClass(type: Notification['type']): string {
        return `toast-${type}`;
    }

    getIcon(type: Notification['type']): string {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type];
    }
}
