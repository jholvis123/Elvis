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

export interface AuthTokens {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
}

@Injectable({
    providedIn: 'root'
})
export class AuthService {
    private readonly TOKEN_KEY = 'access_token';
    private readonly REFRESH_TOKEN_KEY = 'refresh_token';
    private readonly USER_KEY = 'current_user';

    private currentUserSubject = new BehaviorSubject<User | null>(this.getUserFromStorage());
    public currentUser$ = this.currentUserSubject.asObservable();

    constructor(private api: ApiService) { }

    /**
     * Obtiene el usuario actual del almacenamiento
     */
    private getUserFromStorage(): User | null {
        const userJson = localStorage.getItem(this.USER_KEY);
        return userJson ? JSON.parse(userJson) : null;
    }

    /**
     * Usuario actualmente autenticado
     */
    get currentUser(): User | null {
        return this.currentUserSubject.value;
    }

    /**
     * Verifica si hay un usuario autenticado
     */
    get isAuthenticated(): boolean {
        return !!this.getAccessToken() && !!this.currentUser;
    }

    /**
     * Verifica si el usuario actual es administrador
     */
    get isAdmin(): boolean {
        return this.currentUser?.is_admin || false;
    }

    /**
     * Obtiene el access token almacenado
     */
    getAccessToken(): string | null {
        return localStorage.getItem(this.TOKEN_KEY);
    }

    /**
     * Obtiene el refresh token almacenado
     */
    getRefreshToken(): string | null {
        return localStorage.getItem(this.REFRESH_TOKEN_KEY);
    }

    /**
     * Inicia sesión con email y contraseña
     */
    login(credentials: LoginCredentials): Observable<User> {
        return this.api.post<AuthTokens>('/auth/login', credentials).pipe(
            tap(tokens => this.storeTokens(tokens)),
            // Después de guardar tokens, obtener datos del usuario desde backend
            switchMap(() => this.api.get<User>('/auth/me')),
            tap(user => this.setCurrentUser(user))
        );
    }

    /**
     * Registra un nuevo usuario
     */
    register(data: RegisterData): Observable<User> {
        return this.api.post<User>('/auth/register', data).pipe(
            tap(user => {
                // Después del registro, hacer login automático
                this.login({
                    email: data.email,
                    password: data.password
                }).subscribe();
            })
        );
    }

    /**
     * Cierra la sesión actual
     */
    logout(): void {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.REFRESH_TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
        this.currentUserSubject.next(null);
    }

    /**
     * Refresca el access token usando el refresh token
     */
    refreshToken(): Observable<AuthTokens> {
        const refreshToken = this.getRefreshToken();

        if (!refreshToken) {
            return of({} as AuthTokens);
        }

        return this.api.post<AuthTokens>('/auth/refresh', { refresh_token: refreshToken }).pipe(
            tap(tokens => this.storeTokens(tokens)),
            catchError(() => {
                this.logout();
                return of({} as AuthTokens);
            })
        );
    }

    /**
     * Obtiene el perfil del usuario autenticado
     */
    getCurrentUser(): Observable<User> {
        return this.api.get<User>('/auth/me').pipe(
            tap(user => this.setCurrentUser(user))
        );
    }

    /**
     * Almacena los tokens en localStorage
     */
    private storeTokens(tokens: AuthTokens): void {
        localStorage.setItem(this.TOKEN_KEY, tokens.access_token);
        localStorage.setItem(this.REFRESH_TOKEN_KEY, tokens.refresh_token);
    }

    /**
     * Establece el usuario actual
     */
    private setCurrentUser(user: User): void {
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
        this.currentUserSubject.next(user);
    }

    /**
     * Obtiene el usuario actual del backend
     */
    private fetchCurrentUser(): User {
        // Esto debería ser asíncrono, pero para simplificar el flujo de login
        // se maneja en otro método. Aquí retornamos lo que tenemos en storage.
        return this.getUserFromStorage()!;
    }

    /**
     * Verifica si el token está próximo a expirar
     */
    isTokenExpiringSoon(): boolean {
        // TODO: Implementar lógica de decodificación de JWT
        // y verificación de tiempo de expiración
        return false;
    }
}
