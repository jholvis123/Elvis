import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

/**
 * Métodos HTTP que modifican estado y requieren protección CSRF (solo same-origin).
 */
const CSRF_PROTECTED_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];

/**
 * Interceptor de autenticación:
 * - Cross-origin (Pages → API): Authorization: Bearer <access_token>, sin CSRF.
 * - Same-origin (local/docker): cookies via withCredentials + X-CSRF-Token double-submit.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
    const authService = inject(AuthService);

    if (authService.usesBearerAuth()) {
        const accessToken = authService.getAccessToken();
        if (accessToken) {
            return next(req.clone({
                setHeaders: {
                    Authorization: `Bearer ${accessToken}`
                }
            }));
        }
        // Cross-origin sin token: no enviar CSRF (cookies de auth no aplican)
        return next(req);
    }

    // Same-origin: CSRF double-submit en mutaciones
    const needsCsrf = CSRF_PROTECTED_METHODS.includes(req.method.toUpperCase());

    if (needsCsrf) {
        const csrfToken = authService.getCsrfToken();

        if (csrfToken) {
            const cloned = req.clone({
                setHeaders: {
                    'X-CSRF-Token': csrfToken
                }
            });
            return next(cloned);
        }
    }

    return next(req);
};
