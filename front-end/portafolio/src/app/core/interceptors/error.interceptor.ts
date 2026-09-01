import { HttpInterceptorFn, HttpErrorResponse, HttpRequest } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { NotificationService } from '../services/notification.service';
import { ApiError } from '../services/api.service';

function humanMessage(error: HttpErrorResponse, url: string): string {
    if (error.status === 0) {
        return 'No se puede conectar al servidor';
    }

    if (error.error instanceof ErrorEvent) {
        return 'Ha ocurrido un error inesperado';
    }

    const detail = error.error?.detail;

    switch (error.status) {
        case 400:
            if (typeof detail === 'string') return detail;
            return 'Solicitud inválida. Verifica los datos.';
        case 401:
            if (url.includes('/auth/login')) {
                if (typeof detail === 'string') return detail;
                return 'Credenciales inválidas. Verifica tu correo y contraseña.';
            }
            return 'Sesión expirada. Por favor, inicia sesión nuevamente.';
        case 403:
            return 'No tienes permisos para realizar esta acción.';
        case 404:
            return 'El recurso solicitado no fue encontrado.';
        case 409:
            if (typeof detail === 'string') return detail;
            return 'Conflicto. El recurso ya existe.';
        case 422:
            if (Array.isArray(detail)) {
                return detail.map((e: { msg?: string }) => e.msg).filter(Boolean).join(', ') || 'Datos de validación incorrectos.';
            }
            if (typeof detail === 'string') return detail;
            return 'Datos de validación incorrectos.';
        case 429:
            return 'Demasiadas solicitudes. Intenta de nuevo en unos minutos.';
        default:
            if (error.status >= 500) {
                return 'Error interno del servidor. Por favor, intenta más tarde.';
            }
            if (typeof detail === 'string') {
                return detail;
            }
            return 'Ha ocurrido un error. Inténtalo de nuevo.';
    }
}

function isSilentAuthUrl(req: HttpRequest<unknown>): boolean {
    return req.url.includes('/auth/me')
        || req.url.includes('/auth/refresh')
        || req.url.includes('/auth/login')
        || req.url.includes('/auth/logout')
        || req.url.includes('/auth/register');
}

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
    const router = inject(Router);
    const authService = inject(AuthService);
    const notificationService = inject(NotificationService);

    return next(req).pipe(
        catchError((error: HttpErrorResponse) => {
            if (error.status === 0 && error.error instanceof ProgressEvent) {
                return throwError(() => new ApiError('No se puede conectar al servidor', 0));
            }

            const message = humanMessage(error, req.url);
            const apiError = new ApiError(message, error.status);

            if (error.status === 401) {
                if (isSilentAuthUrl(req)) {
                    return throwError(() => apiError);
                }

                authService.logout().subscribe(() => {
                    router.navigate(['/auth/login']);
                });
                notificationService.error(message);
                return throwError(() => apiError);
            }

            const skipToast = error.status === 404 || isSilentAuthUrl(req);
            if (!skipToast) {
                notificationService.error(message);
            }

            return throwError(() => apiError);
        })
    );
};
