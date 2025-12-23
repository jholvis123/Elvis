import { Injectable } from '@angular/core';

@Injectable({
    providedIn: 'root'
})
export class ErrorHandlerService {
    /**
     * Maneja errores y extrae mensajes legibles
     */
    handleError(error: any): string {
        // Error de red
        if (error.status === 0) {
            return 'Error de conexión. Verifica tu internet.';
        }

        // Error HTTP con detalle del servidor
        if (error.error?.detail) {
            if (typeof error.error.detail === 'string') {
                return error.error.detail;
            }

            // Array de errores de validación de Pydantic
            if (Array.isArray(error.error.detail)) {
                return error.error.detail.map((e: any) => e.msg || e.message).join(', ');
            }
        }

        // Errores HTTP estándar
        switch (error.status) {
            case 400:
                return 'Solicitud inválida. Verifica los dados.';
            case 401:
                return 'No autorizado. Inicia sesión nuevamente.';
            case 403:
                return 'No tienes permisos para esta acción.';
            case 404:
                return 'Recurso no encontrado.';
            case 409:
                return 'Conflicto. El recurso ya existe.';
            case 422:
                return 'Datos de validación incorrectos.';
            case 429:
                return 'Demasiadas solicitudes. Intenta más tarde.';
            case 500:
                return 'Error del servidor. Intenta más tarde.';
            case 503:
                return 'Servicio no disponible temporalmente.';
            default:
                return error.message || 'Ha ocurrido un error inesperado.';
        }
    }

    /**
     * Registra el error en consola (en producción podría enviarse a un servicio de logging)
     */
    logError(error: any, context?: string): void {
        const timestamp = new Date().toISOString();
        console.error(`[${timestamp}]${context ? ` [${context}]` : ''}`, error);

        // En producción, aquí se podría enviar a Sentry, LogRocket, etc.
        // this.sentryService.captureException(error);
    }
}
