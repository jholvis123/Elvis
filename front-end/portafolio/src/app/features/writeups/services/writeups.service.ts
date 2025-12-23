import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { ApiService } from '../../../core/services/api.service';

export interface Writeup {
    id: string;
    title: string;
    ctf_id: string;
    content: string;
    summary: string;
    tools_used: string[];
    techniques: string[];
    attachments: string[];
    status: 'draft' | 'published';
    views: number;
    author_id: string;
    created_at: string;
    updated_at: string;
    published_at?: string;
    read_time?: number;
}

export interface WriteupListResponse {
    items: Writeup[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

export interface WriteupForm {
    title: string;
    ctf_id: string;
    content: string;
    summary: string;
    tools_used: string[];
    techniques: string[];
}

@Injectable({
    providedIn: 'root'
})
export class WriteupsService {
    constructor(private api: ApiService) { }

    /**
     * Obtiene lista de writeups con paginación
     */
    getWriteups(params?: {
        page?: number;
        size?: number;
        search?: string;
    }): Observable<WriteupListResponse> {
        return this.api.get<WriteupListResponse>('/writeups', {
            page: params?.page || 1,
            size: params?.size || 10,
            ...(params?.search && { search: params.search })
        });
    }

    /**
     * Obtiene writeups más populares
     */
    getPopularWriteups(limit: number = 10): Observable<Writeup[]> {
        return this.api.get<Writeup[]>('/writeups/popular', { limit }).pipe(
            catchError(() => of([]))
        );
    }

    /**
     * Obtiene writeup por ID
     */
    getWriteupById(id: string): Observable<Writeup> {
        return this.api.get<Writeup>(`/writeups/${id}`);
    }

    /**
     * Obtiene writeup de un CTF específico
     */
    getWriteupByCTF(ctfId: string): Observable<Writeup> {
        return this.api.get<Writeup>(`/writeups/ctf/${ctfId}`);
    }

    /**
     * Crea un nuevo writeup (admin)
     */
    createWriteup(data: WriteupForm): Observable<Writeup> {
        return this.api.post<Writeup>('/writeups', data);
    }

    /**
     * Actualiza un writeup existente (admin)
     */
    updateWriteup(id: string, data: Partial<WriteupForm>): Observable<Writeup> {
        return this.api.put<Writeup>(`/writeups/${id}`, data);
    }

    /**
     * Publica un writeup (admin)
     */
    publishWriteup(id: string): Observable<Writeup> {
        return this.api.post<Writeup>(`/writeups/${id}/publish`, {});
    }

    /**
     * Elimina un writeup (admin)
     */
    deleteWriteup(id: string): Observable<void> {
        return this.api.delete<void>(`/writeups/${id}`);
    }
}
