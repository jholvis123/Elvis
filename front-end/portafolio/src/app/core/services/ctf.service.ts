import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';
import {
  CTFChallenge,
  CTFFilter,
  CTFStats,
  CTFChallengeForm,
  CTFCategory,
  CTFDifficulty
} from '../models/ctf.model';
import { ApiService } from './api.service';

// Interfaces para respuestas de la API
interface CTFApiResponse {
  id: string;
  title: string;
  level: string;
  category: string;
  platform: string;
  description?: string;
  points: number;
  solved: boolean;
  solved_at?: string;
  machine_os?: string;
  skills: string[];
  hints: string[];
  author?: string;
  solved_count: number;
  is_active: boolean;
  status: string;
  created_at: string;
  updated_at?: string;
  attachments?: {
    id: string;
    filename: string;
    attachment_type: string;
    url?: string;
  }[];
}

interface CTFListResponse {
  items: CTFApiResponse[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

interface FlagSubmitResponse {
  is_correct: boolean;
  message: string;
  attempts_remaining?: number;
}

// Respuesta normalizada para el frontend
export interface FlagSubmitResult {
  success: boolean;
  message: string;
}

// DTO para actualización de CTF
export interface CTFUpdateDTO {
  title?: string;
  level?: string;
  category?: string;
  platform?: string;
  description?: string;
  points?: number;
  machine_os?: string;
  skills?: string[];
  hints?: string[];
  flag?: string;
  is_flag_regex?: boolean;
  author?: string;
  is_active?: boolean;
  solved?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class CtfService {

  constructor(private api: ApiService) { }

  // Retos resueltos por el usuario (local cache opcional, pero mejor confiar en API)
  private solvedChallenges: Set<string> = new Set();

  // ==================== API METHODS ====================

  /**
   * Obtiene los CTFs desde la API
   */
  getChallengesFromApi(filter?: CTFFilter): Observable<CTFChallenge[]> {
    const params: Record<string, string | number> = {
      page: 1,
      size: 100
    };

    if (filter?.category && filter.category !== 'all') {
      params['category'] = filter.category;
    }
    if (filter?.difficulty && filter.difficulty !== 'all') {
      params['level'] = filter.difficulty;
    }
    if (filter?.search) {
      params['search'] = filter.search;
    }

    return this.api.get<CTFListResponse>('/ctfs', params).pipe(
      map(response => response.items.map(this.mapApiToChallenge))
    );
  }

  /**
   * Obtiene un CTF por ID desde la API
   */
  getChallengeByIdFromApi(id: string): Observable<CTFChallenge | null> {
    return this.api.get<CTFApiResponse>(`/ctfs/${id}`).pipe(
      map(this.mapApiToChallenge),
      catchError(err => {
        console.error('Error fetching challenge:', err);
        return of(null);
      })
    );
  }

  /**
   * Envía una flag a la API para verificación
   */
  submitFlagToApi(challengeId: string, flag: string): Observable<FlagSubmitResult> {
    return this.api.post<FlagSubmitResponse>(`/ctfs/${challengeId}/submit`, { flag }).pipe(
      map(response => ({
        success: response.is_correct,
        message: response.message
      })),
      tap(result => {
        if (result.success) {
          this.solvedChallenges.add(challengeId);
        }
      })
    );
  }

  /**
   * Obtiene estadísticas desde la API
   */
  getStatsFromApi(): Observable<CTFStats> {
    return this.api.get<any>('/ctfs/statistics').pipe(
      map(data => ({
        totalChallenges: data.total || 0,
        solvedChallenges: data.solved || 0,
        totalPoints: data.total_points || 0,
        earnedPoints: data.earned_points || 0
      }))
    );
  }

  /**
   * Crear challenge en la API
   */
  createChallenge(form: CTFChallengeForm): Promise<CTFChallenge> {
    // Adaptador para mantener compatibilidad si el componente espera promesa
    // pero redirigiendo a createChallengeInApi
    return this.createChallengeInApi(form).toPromise().then(res => res!);
  }

  /**
   * Crear challenge en la API (Observable implementation)
   */
  createChallengeInApi(form: CTFChallengeForm): Observable<CTFChallenge> {
    const payload = {
      title: form.title,
      description: form.description,
      category: form.category,
      level: form.difficulty,
      platform: form.platform,
      points: form.points,
      flag: form.flag,
      skills: form.skills || [],
      hints: form.hints || [],
      is_active: form.isActive ?? true,
      attachments: form.attachments || [] // IDs or objects, backend handles mapping
    };

    return this.api.post<CTFApiResponse>('/ctfs', payload).pipe(
      map(response => this.mapApiToChallenge(response)),
      catchError(err => {
        console.error('Error creating challenge in API:', err);
        throw err;
      })
    );
  }

  isSolved(challengeId: string): boolean {
    return this.solvedChallenges.has(challengeId);
  }

  // ==================== ADMIN METHODS ====================

  /**
   * Obtiene TODOS los CTFs para el panel de administración (incluye drafts)
   */
  getAllChallengesAdmin(filter?: CTFFilter & { status?: string }): Observable<{
    items: CTFChallengeAdmin[];
    total: number;
    page: number;
    size: number;
    pages: number;
  }> {
    const params: Record<string, string | number> = {
      page: 1,
      size: 100
    };

    if (filter?.category && filter.category !== 'all') {
      params['category'] = filter.category;
    }
    if (filter?.difficulty && filter.difficulty !== 'all') {
      params['level'] = filter.difficulty;
    }
    if (filter?.status) {
      params['status'] = filter.status;
    }
    if (filter?.search) {
      params['search'] = filter.search;
    }

    return this.api.get<CTFListResponse>('/ctfs/admin/all', params).pipe(
      map(response => ({
        items: response.items.map(this.mapApiToAdminChallenge),
        total: response.total,
        page: response.page,
        size: response.size,
        pages: response.pages
      }))
    );
  }

  /**
   * Actualiza un CTF existente
   */
  updateChallenge(id: string, data: CTFUpdateDTO): Observable<CTFChallenge> {
    return this.api.put<CTFApiResponse>(`/ctfs/${id}`, data).pipe(
      map(response => this.mapApiToChallenge(response)),
      catchError(err => {
        console.error('Error updating challenge:', err);
        throw err;
      })
    );
  }

  /**
   * Activa o desactiva un CTF
   */
  toggleChallengeActive(id: string, isActive: boolean): Observable<CTFChallenge> {
    return this.updateChallenge(id, { is_active: isActive });
  }

  /**
   * Publica un CTF (cambia status de draft a published)
   */
  publishChallenge(id: string): Observable<CTFChallenge> {
    return this.api.post<CTFApiResponse>(`/ctfs/${id}/publish`, {}).pipe(
      map(response => this.mapApiToChallenge(response)),
      catchError(err => {
        console.error('Error publishing challenge:', err);
        throw err;
      })
    );
  }

  /**
   * Elimina un CTF
   */
  deleteChallenge(id: string, force: boolean = false): Observable<void> {
    const params: Record<string, string | number | boolean> | undefined = force ? { force: 'true' } : undefined;
    return this.api.delete<void>(`/ctfs/${id}`, params).pipe(
      catchError(err => {
        console.error('Error deleting challenge:', err);
        throw err;
      })
    );
  }

  // ==================== HELPER METHODS ====================

  /**
   * Mapea respuesta de API a modelo del frontend
   */
  private mapApiToChallenge = (api: CTFApiResponse): CTFChallenge => ({
    id: api.id,
    title: api.title,
    description: api.description || '',
    category: api.category as CTFCategory,
    difficulty: this.mapLevelToDifficulty(api.level),
    points: api.points,
    skills: api.skills || [],
    hints: api.hints || [],
    author: api.author || 'Unknown',
    createdAt: new Date(api.created_at),
    solvedCount: api.solved_count || 0,
    isActive: api.is_active,
    attachments: (api.attachments || []).map(att => ({
      id: att.id,
      name: att.filename,
      type: att.attachment_type as 'file' | 'url' | 'docker',
      url: att.url || ''
    }))
  });

  /**
   * Mapea respuesta de API a modelo admin (incluye más campos)
   */
  private mapApiToAdminChallenge = (api: CTFApiResponse): CTFChallengeAdmin => ({
    id: api.id,
    title: api.title,
    description: api.description || '',
    category: api.category as CTFCategory,
    difficulty: this.mapLevelToDifficulty(api.level),
    level: api.level,
    points: api.points,
    skills: api.skills || [],
    hints: api.hints || [],
    author: api.author || 'Unknown',
    createdAt: new Date(api.created_at),
    updatedAt: api.updated_at ? new Date(api.updated_at) : undefined,
    solvedCount: api.solved_count || 0,
    isActive: api.is_active,
    status: api.status as 'draft' | 'published' | 'archived',
    platform: api.platform,
    solved: api.solved,
    attachments: (api.attachments || []).map(att => ({
      id: att.id,
      name: att.filename,
      type: att.attachment_type as 'file' | 'url' | 'docker',
      url: att.url || ''
    }))
  });

  /**
   * Mapea level del backend a difficulty del frontend
   */
  private mapLevelToDifficulty(level: string): CTFDifficulty {
    const mapping: Record<string, CTFDifficulty> = {
      'easy': 'easy',
      'medium': 'medium',
      'hard': 'hard',
      'insane': 'hard'
    };
    return mapping[level] || 'medium';
  }
}

// Interface extendida para admin
export interface CTFChallengeAdmin extends CTFChallenge {
  level: string;
  status: 'draft' | 'published' | 'archived';
  platform: string;
  solved: boolean;
  updatedAt?: Date;
}
