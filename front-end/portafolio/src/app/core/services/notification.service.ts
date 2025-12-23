import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

export interface Notification {
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    message: string;
    duration?: number;
}

@Injectable({
    providedIn: 'root'
})
export class NotificationService {
    private notificationSubject = new Subject<Notification>();
    public notifications$ = this.notificationSubject.asObservable();

    private generateId(): string {
        return `notif-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Muestra una notificación de éxito
     */
    success(message: string, duration: number = 3000): void {
        this.show({ type: 'success', message, duration });
    }

    /**
     * Muestra una notificación de error
     */
    error(message: string, duration: number = 5000): void {
        this.show({ type: 'error', message, duration });
    }

    /**
     * Muestra una notificación de advertencia
     */
    warning(message: string, duration: number = 4000): void {
        this.show({ type: 'warning', message, duration });
    }

    /**
     * Muestra una notificación informativa
     */
    info(message: string, duration: number = 3000): void {
        this.show({ type: 'info', message, duration });
    }

    /**
     * Muestra una notificación personalizada
     */
    private show(notification: Omit<Notification, 'id'>): void {
        const fullNotification: Notification = {
            ...notification,
            id: this.generateId()
        };

        this.notificationSubject.next(fullNotification);
    }
}
