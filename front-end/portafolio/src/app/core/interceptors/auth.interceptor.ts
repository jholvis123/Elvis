import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

/**
 * Métodos HTTP que modifican estado y requieren protección CSRF
 */
const CSRF_PROTECTED_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];

/**
 * Interceptor que:
 * 1. Añade el token CSRF a peticiones que modifican estado (POST, PUT, PATCH, DELETE)
 * 2. Las cookies de autenticación se envían automáticamente con withCredentials: true
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
    const authService = inject(AuthService);
    
    // Verificar si la petición necesita protección CSRF
    const needsCsrf = CSRF_PROTECTED_METHODS.includes(req.method.toUpperCase());
    
    if (needsCsrf) {
        // Obtener token CSRF desde la cookie
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

    // Continuar sin modificar para peticiones GET u otras sin CSRF token
    return next(req);
};
