import { Injectable } from '@angular/core';
import { Observable, of, throwError } from 'rxjs';
import { tap, shareReplay } from 'rxjs/operators';

interface CacheEntry<T> {
    data: T;
    timestamp: number;
}

@Injectable({
    providedIn: 'root'
})
export class CacheService {
    private cache = new Map<string, CacheEntry<any>>();
    private defaultTTL = 5 * 60 * 1000; // 5 minutos por defecto

    /**
     * Obtiene datos del caché o ejecuta la función si no existe o expiró
     */
    get<T>(key: string, fetcher: () => Observable<T>, ttl: number = this.defaultTTL): Observable<T> {
        const cached = this.cache.get(key);

        if (cached && !this.isExpired(cached, ttl)) {
            return of(cached.data);
        }

        return fetcher().pipe(
            tap(data => this.set(key, data)),
            shareReplay(1)
        );
    }

    /**
     * Establece un valor en el caché
     */
    set<T>(key: string, data: T): void {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    /**
     * Invalida una entrada específica del caché
     */
    invalidate(key: string): void {
        this.cache.delete(key);
    }

    /**
     * Invalida todas las entradas que coincidan con un patrón
     */
    invalidatePattern(pattern: RegExp): void {
        const keysToDelete: string[] = [];

        this.cache.forEach((_, key) => {
            if (pattern.test(key)) {
                keysToDelete.push(key);
            }
        });

        keysToDelete.forEach(key => this.cache.delete(key));
    }

    /**
     * Limpia todo el caché
     */
    clear(): void {
        this.cache.clear();
    }

    /**
     * Verifica si una entrada del caché ha expirado
     */
    private isExpired<T>(entry: CacheEntry<T>, ttl: number): boolean {
        return Date.now() - entry.timestamp > ttl;
    }
}
