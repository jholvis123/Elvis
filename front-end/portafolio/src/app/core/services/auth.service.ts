import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { map, tap, catchError, switchMap } from 'rxjs/operators';
import { ApiService } from './api.service';
import { ApiAvailabilityService } from './api-availability.service';

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
 * AuthStatusDTO (snake_case) from BE login/refresh.
 * Tokens only present when client requested token_in_body: true (Bearer / Pages).
 */
export interface AuthStatus {
    authenticated: boolean;
    user: User | null;
    expires_in: number | null;
    access_token?: string | null;
    refresh_token?: string | null;
    token_type?: string | null;
}

@Injectable({
    providedIn: 'root'
})
export class AuthService {
    /**
     * Same-origin (local/docker): cookies HttpOnly + CSRF double-submit.
     * Cross-origin (GitHub Pages → Render): Bearer tokens in sessionStorage
     * (not localStorage — reduces persistent XSS token theft).
     * User UX fields may remain in localStorage.
     */
    private readonly USER_KEY = 'current_user';
    private readonly CSRF_COOKIE = 'csrf_token';
    private readonly ACCESS_TOKEN_KEY = 'access_token';
    private readonly REFRESH_TOKEN_KEY = 'refresh_token';

    private currentUserSubject = new BehaviorSubject<User | null>(this.getUserFromStorage());
    public currentUser$ = this.currentUserSubject.asObservable();

    private tokenExpiresAt: number | null = null;
    private refreshTimeout: ReturnType<typeof setTimeout> | null = null;

    constructor(
        private api: ApiService,
        private apiAvailability: ApiAvailabilityService
    ) {
        // Verificar autenticación al iniciar SOLO si hay sesión previa (user y/o Bearer tokens)
        if (this.getUserFromStorage() || (this.usesBearerAuth() && this.getAccessToken())) {
            this.checkAuthStatus().subscribe();
        }
    }

    /**
     * Cross-origin Pages → API: use Bearer + sessionStorage.
     * Same-origin: cookies + CSRF (existing flow).
     */
    usesBearerAuth(): boolean {
        return this.apiAvailability.isCrossOriginApi();
    }

    private getUserFromStorage(): User | null {
        try {
            const userJson = localStorage.getItem(this.USER_KEY);
            return userJson ? JSON.parse(userJson) : null;
        } catch {
            return null;
        }
    }

    get currentUser(): User | null {
        return this.currentUserSubject.value;
    }

    get isAuthenticated(): boolean {
        return !!this.currentUser;
    }

    /**
     * UI-only hint. Real authorization is always enforced by the backend.
     */
    get isAdmin(): boolean {
        return this.currentUser?.is_admin || false;
    }

    /**
     * CSRF cookie (readable; not HttpOnly). Only used in same-origin cookie mode.
     */
    getCsrfToken(): string | null {
        const matches = document.cookie.match(new RegExp(
            '(?:^|; )' + this.CSRF_COOKIE + '=([^;]*)'
        ));
        return matches ? decodeURIComponent(matches[1]) : null;
    }

    /** Access JWT from sessionStorage (Bearer mode only). */
    getAccessToken(): string | null {
        try {
            return sessionStorage.getItem(this.ACCESS_TOKEN_KEY);
        } catch {
            return null;
        }
    }

    /** Refresh JWT from sessionStorage (Bearer mode only). */
    getRefreshToken(): string | null {
        try {
            return sessionStorage.getItem(this.REFRESH_TOKEN_KEY);
        } catch {
            return null;
        }
    }

    private persistTokens(access: string, refresh: string): void {
        try {
            sessionStorage.setItem(this.ACCESS_TOKEN_KEY, access);
            sessionStorage.setItem(this.REFRESH_TOKEN_KEY, refresh);
        } catch {
            // sessionStorage may be unavailable (private mode); fail closed
            this.clearTokens();
        }
    }

    private clearTokens(): void {
        try {
            sessionStorage.removeItem(this.ACCESS_TOKEN_KEY);
            sessionStorage.removeItem(this.REFRESH_TOKEN_KEY);
        } catch {
            // ignore
        }
    }

    private applyAuthResponse(response: AuthStatus): void {
        if (response.authenticated && response.user) {
            this.setCurrentUser(response.user);
            this.scheduleTokenRefresh(response.expires_in);
        }
        if (this.usesBearerAuth()) {
            if (response.access_token && response.refresh_token) {
                this.persistTokens(response.access_token, response.refresh_token);
            }
        } else {
            // Same-origin: never keep Bearer leftovers
            this.clearTokens();
        }
    }

    /**
     * Login. Cross-origin sends token_in_body: true and expects snake_case
     * access_token / refresh_token / token_type in AuthStatusDTO.
     */
    login(credentials: LoginCredentials): Observable<User> {
        const body = this.usesBearerAuth()
            ? { ...credentials, token_in_body: true }
            : credentials;

        return this.api.post<AuthStatus>('/auth/login', body, { withCredentials: true }).pipe(
            map(response => {
                if (!response.authenticated || !response.user) {
                    throw new Error('Login failed');
                }
                if (this.usesBearerAuth()) {
                    if (!response.access_token || !response.refresh_token) {
                        // Old API without #50: cookies cannot auth cross-origin
                        this.clearLocalAuth();
                        throw new Error(
                            'El API no devolvió tokens Bearer (access_token/refresh_token). ' +
                            'Necesita el soporte token_in_body desplegado en el backend.'
                        );
                    }
                }
                this.applyAuthResponse(response);
                return response.user;
            })
        );
    }

    register(data: RegisterData): Observable<User> {
        return this.api.post<User>('/auth/register', data, { withCredentials: true }).pipe(
            switchMap(() =>
                this.login({
                    email: data.email,
                    password: data.password
                })
            )
        );
    }

    /**
     * Logout: BE clears cookies; FE discards sessionStorage tokens.
     */
    logout(): Observable<void> {
        return this.api.post<void>('/auth/logout', {}, { withCredentials: true }).pipe(
            tap(() => {
                this.clearLocalAuth();
            }),
            catchError(() => {
                this.clearLocalAuth();
                return of(undefined);
            })
        );
    }

    /** Clears UX user + Bearer tokens + refresh timer. */
    clearLocalAuth(): void {
        localStorage.removeItem(this.USER_KEY);
        this.clearTokens();
        this.currentUserSubject.next(null);
        this.tokenExpiresAt = null;
        if (this.refreshTimeout) {
            clearTimeout(this.refreshTimeout);
            this.refreshTimeout = null;
        }
    }

    /**
     * Refresh access token.
     * Bearer/cross-origin: POST { refresh_token, token_in_body: true }.
     * Same-origin: empty body + refresh cookie.
     */
    refreshToken(): Observable<AuthStatus> {
        const body = this.usesBearerAuth()
            ? {
                refresh_token: this.getRefreshToken(),
                token_in_body: true
            }
            : {};

        if (this.usesBearerAuth() && !this.getRefreshToken()) {
            this.clearLocalAuth();
            return of({ authenticated: false, user: null, expires_in: null });
        }

        return this.api.post<AuthStatus>('/auth/refresh', body, { withCredentials: true }).pipe(
            tap(response => {
                if (response.authenticated && response.user) {
                    this.applyAuthResponse(response);
                }
            }),
            catchError(() => {
                this.clearLocalAuth();
                return of({ authenticated: false, user: null, expires_in: null });
            })
        );
    }

    checkAuthStatus(): Observable<AuthStatus> {
        return this.api.get<User>('/auth/me', { withCredentials: true }).pipe(
            map(user => ({
                authenticated: true,
                user,
                expires_in: null as number | null
            })),
            tap(response => {
                if (response.authenticated && response.user) {
                    this.setCurrentUser(response.user);
                }
            }),
            catchError(() => {
                this.clearLocalAuth();
                return of({ authenticated: false, user: null, expires_in: null });
            })
        );
    }

    getCurrentUser(): Observable<User> {
        return this.api.get<User>('/auth/me', { withCredentials: true }).pipe(
            tap(user => this.setCurrentUser(user))
        );
    }

    private setCurrentUser(user: User): void {
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
        this.currentUserSubject.next(user);
    }

    private scheduleTokenRefresh(expiresIn: number | null): void {
        if (this.refreshTimeout) {
            clearTimeout(this.refreshTimeout);
        }

        if (!expiresIn) return;

        this.tokenExpiresAt = Date.now() + (expiresIn * 1000);

        const refreshIn = (expiresIn - 60) * 1000;

        if (refreshIn > 0) {
            this.refreshTimeout = setTimeout(() => {
                this.refreshToken().subscribe();
            }, refreshIn);
        }
    }

    isTokenExpiringSoon(): boolean {
        if (!this.tokenExpiresAt) return false;
        return (this.tokenExpiresAt - Date.now()) < 120000;
    }
}
