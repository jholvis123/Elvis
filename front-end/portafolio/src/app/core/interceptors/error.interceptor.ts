import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { NotificationService } from '../services/notification.service';

/**
 * Interceptor que maneja errores HTTP globalmente
 */
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
    const router = inject(Router);
    const authService = inject(AuthService);
    const notificationService = inject(NotificationService);

    return next(req).pipe(
        catchError((error: HttpErrorResponse) => {
            let errorMessage = 'Ha ocurrido un error';

            // Ignorar errores de conexión interrumpida intencionalmente o cancelaciones
            if (error.status === 0 && error.error instanceof ProgressEvent) {
                return throwError(() => error);
            }

            if (error.error instanceof ErrorEvent) {
                // Error del lado del cliente
                errorMessage = `Error: ${error.error.message}`;
            } else {
                // Error del lado del servidor
                switch (error.status) {
                    case 401:
                        // No autorizado
                        // Ignorar 401 de endpoints de verificación de auth (no mostrar notificación)
                        // Estos endpoints esperan 401 cuando no hay sesión activa
                        if (req.url.includes('/auth/me') || req.url.includes('/auth/refresh')) {
                            // Solo propagar el error sin notificación ni redirección
                            return throwError(() => error);
                        }
                        
                        // Para otros endpoints: cerrar sesión y redirigir al login
                        // Solo si no estamos ya en la página de login para evitar bucles
                        if (!req.url.includes('/auth/login') && !req.url.includes('/auth/logout')) {
                            // IMPORTANTE: Suscribirse para que el logout se ejecute
                            authService.logout().subscribe(() => {
                                router.navigate(['/']);
                            });
                            errorMessage = 'Sesión expirada. Por favor, inicia sesión nuevamente.';
                        }
                        break;
                    case 403:
                        errorMessage = 'No tienes permisos para realizar esta acción.';
                        // No redirigir forzosamente, solo notificar
                        break;
                    case 404:
                        errorMessage = 'El recurso solicitado no fue encontrado.';
                        break;
                    case 429:
                        errorMessage = 'Demasiadas solicitudes. Intenta de nuevo en unos minutos.';
                        break;
                    case 422:
                        // Error de validación (FastAPI/Pydantic)
                        if (error.error?.detail) {
                            if (Array.isArray(error.error.detail)) {
                                // Formato pydantic: [{"loc":..., "msg":...}]
                                errorMessage = error.error.detail.map((e: any) => e.msg).join(', ');
                            } else {
                                errorMessage = error.error.detail;
                            }
                        } else {
                            errorMessage = 'Error de validación de datos.';
                        }
                        break;
                    case 500:
                        errorMessage = 'Error interno del servidor. Por favor, intenta más tarde.';
                        break;
                    default:
                        if (error.error?.detail) {
                            errorMessage = typeof error.error.detail === 'string'
                                ? error.error.detail
                                : JSON.stringify(error.error.detail);
                        } else {
                            errorMessage = `Error ${error.status}: ${error.statusText || 'Desconocido'}`;
                        }
                }
            }

            console.error('HTTP Error:', errorMessage, error);

            // Mostrar notificación visual (Toast)
            notificationService.error(errorMessage);

            // Re-lanzar el error estandarizado
            return throwError(() => new Error(errorMessage));
        })
    );
};
