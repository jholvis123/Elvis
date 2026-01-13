import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { map, tap, catchError, switchMap } from 'rxjs/operators';
import { ApiService } from './api.service';

export interface User {
    id: string;
    email: string;
    username: string;
    is_active: boolean;
    is_admin: boolean;
    created_at: string;
}

export interface LoginCredentials {
    email: string;
    password: string;
}

export interface RegisterData {
    email: string;
    username: string;
    password: string;
}

/**
 * Respuesta de autenticación del backend.
 * Los tokens NO vienen en el body - se establecen en cookies HttpOnly.
 */
export interface AuthStatus {
    authenticated: boolean;
    user: User | null;
    expires_in: number | null;
}

@Injectable({
    providedIn: 'root'
})
export class AuthService {
    /**
     * NOTA DE SEGURIDAD:
     * Los tokens JWT ahora se manejan via cookies HttpOnly establecidas por el backend.
     * El frontend NO tiene acceso a los tokens - esto protege contra XSS.
     * Solo almacenamos datos de usuario (no sensibles) para UX.
     */
    private readonly USER_KEY = 'current_user';
    private readonly CSRF_COOKIE = 'csrf_token';

    private currentUserSubject = new BehaviorSubject<User | null>(this.getUserFromStorage());
    public currentUser$ = this.currentUserSubject.asObservable();
    
    // Tiempo de expiración del token (para refresh proactivo)
    private tokenExpiresAt: number | null = null;
    private refreshTimeout: ReturnType<typeof setTimeout> | null = null;

    constructor(private api: ApiService) {
        // Verificar autenticación al iniciar SOLO si hay usuario en localStorage
        // Esto evita peticiones innecesarias cuando no hay sesión previa
        if (this.getUserFromStorage()) {
            this.checkAuthStatus().subscribe();
        }
    }

    /**
     * Obtiene el usuario actual del almacenamiento local
     * Solo datos de UX, no tokens
     */
    private getUserFromStorage(): User | null {
        try {
            const userJson = localStorage.getItem(this.USER_KEY);
            return userJson ? JSON.parse(userJson) : null;
        } catch {
            return null;
        }
    }

    /**
     * Usuario actualmente autenticado
     */
    get currentUser(): User | null {
        return this.currentUserSubject.value;
    }

    /**
     * Verifica si hay un usuario autenticado
     * La verificación real se hace en el backend via cookies
     */
    get isAuthenticated(): boolean {
        return !!this.currentUser;
    }

    /**
     * Verifica si el usuario actual es administrador
     * IMPORTANTE: La autorización real siempre la hace el backend
     */
    get isAdmin(): boolean {
        return this.currentUser?.is_admin || false;
    }

    /**
     * Obtiene el token CSRF desde la cookie (accesible porque no es HttpOnly)
     */
    getCsrfToken(): string | null {
        const matches = document.cookie.match(new RegExp(
            '(?:^|; )' + this.CSRF_COOKIE + '=([^;]*)'
        ));
        return matches ? decodeURIComponent(matches[1]) : null;
    }

    /**
     * Inicia sesión con email y contraseña.
     * Los tokens se establecen automáticamente en cookies HttpOnly por el backend.
     */
    login(credentials: LoginCredentials): Observable<User> {
        return this.api.post<AuthStatus>('/auth/login', credentials, { withCredentials: true }).pipe(
            tap(response => {
                if (response.authenticated && response.user) {
                    this.setCurrentUser(response.user);
                    this.scheduleTokenRefresh(response.expires_in);
                }
            }),
            map(response => {
                if (!response.user) {
                    throw new Error('Login failed');
                }
                return response.user;
            })
        );
    }

    /**
     * Registra un nuevo usuario
     */
    register(data: RegisterData): Observable<User> {
        return this.api.post<User>('/auth/register', data, { withCredentials: true }).pipe(
            switchMap(user => {
                // Después del registro, hacer login automático
                return this.login({
                    email: data.email,
                    password: data.password
                });
            })
        );
    }

    /**
     * Cierra la sesión actual.
     * El backend elimina las cookies de autenticación.
     */
    logout(): Observable<void> {
        return this.api.post<void>('/auth/logout', {}, { withCredentials: true }).pipe(
            tap(() => {
                this.clearLocalAuth();
            }),
            catchError(() => {
                // Limpiar localmente incluso si falla la petición
                this.clearLocalAuth();
                return of(undefined);
            })
        );
    }

    /**
     * Limpia los datos de autenticación locales
     */
    private clearLocalAuth(): void {
        localStorage.removeItem(this.USER_KEY);
        this.currentUserSubject.next(null);
        this.tokenExpiresAt = null;
        if (this.refreshTimeout) {
            clearTimeout(this.refreshTimeout);
            this.refreshTimeout = null;
        }
    }

    /**
     * Refresca el access token usando el refresh token (vía cookies)
     */
    refreshToken(): Observable<AuthStatus> {
        return this.api.post<AuthStatus>('/auth/refresh', {}, { withCredentials: true }).pipe(
            tap(response => {
                if (response.authenticated && response.user) {
                    this.setCurrentUser(response.user);
                    this.scheduleTokenRefresh(response.expires_in);
                }
            }),
            catchError(error => {
                // Si falla el refresh, cerrar sesión
                this.clearLocalAuth();
                return of({ authenticated: false, user: null, expires_in: null });
            })
        );
    }

    /**
     * Verifica el estado de autenticación actual contra el backend
     */
    checkAuthStatus(): Observable<AuthStatus> {
        return this.api.get<User>('/auth/me', { withCredentials: true }).pipe(
            map(user => ({
                authenticated: true,
                user,
                expires_in: null
            })),
            tap(response => {
                if (response.authenticated && response.user) {
                    this.setCurrentUser(response.user);
                }
            }),
            catchError(() => {
                // No autenticado - limpiar estado local
                this.clearLocalAuth();
                return of({ authenticated: false, user: null, expires_in: null });
            })
        );
    }

    /**
     * Obtiene el perfil del usuario autenticado
     */
    getCurrentUser(): Observable<User> {
        return this.api.get<User>('/auth/me', { withCredentials: true }).pipe(
            tap(user => this.setCurrentUser(user))
        );
    }

    /**
     * Establece el usuario actual (solo datos de UX)
     */
    private setCurrentUser(user: User): void {
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
        this.currentUserSubject.next(user);
    }

    /**
     * Programa el refresh del token antes de que expire
     */
    private scheduleTokenRefresh(expiresIn: number | null): void {
        if (this.refreshTimeout) {
            clearTimeout(this.refreshTimeout);
        }

        if (!expiresIn) return;

        // Calcular cuándo expira el token
        this.tokenExpiresAt = Date.now() + (expiresIn * 1000);

        // Refrescar 1 minuto antes de que expire
        const refreshIn = (expiresIn - 60) * 1000;
        
        if (refreshIn > 0) {
            this.refreshTimeout = setTimeout(() => {
                this.refreshToken().subscribe();
            }, refreshIn);
        }
    }

    /**
     * Verifica si el token está próximo a expirar
     */
    isTokenExpiringSoon(): boolean {
        if (!this.tokenExpiresAt) return false;
        // Considerar "próximo a expirar" si quedan menos de 2 minutos
        return (this.tokenExpiresAt - Date.now()) < 120000;
    }
};
    