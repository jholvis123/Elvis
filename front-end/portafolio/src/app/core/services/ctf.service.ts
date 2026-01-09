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
