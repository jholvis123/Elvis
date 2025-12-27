import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';
import {
  CTFChallenge,
  CTFFilter,
  CTFSubmission,
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

  // Mock data - Fallback si la API no responde
  private readonly mockChallenges: CTFChallenge[] = [
    {
      id: 'web-001',
      title: 'Auth Bypass 01',
      description: 'Un sistema de login vulnerable. Encuentra la forma de acceder sin credenciales válidas.',
      category: 'web',
      difficulty: 'easy',
      points: 100,
      skills: ['SQL Injection', 'Cookies', 'Sessions'],
      hints: ['¿Has probado con comillas simples?', 'El error SQL puede darte pistas'],
      author: 'Elvis',
      createdAt: new Date('2024-01-15'),
      solvedCount: 45,
      isActive: true,
      attachments: [
        { id: 'att-1', name: 'Challenge Server', type: 'url', url: 'https://web-001.ctf.local/' }
      ]
    },
    {
      id: 'crypto-001',
      title: 'Caesar Salad',
      description: 'Un mensaje cifrado con una técnica clásica. Descifra el mensaje oculto para obtener la flag.',
      category: 'crypto',
      difficulty: 'easy',
      points: 100,
      skills: ['Caesar Cipher', 'Frequency Analysis'],
      hints: ['Es un cifrado por sustitución', 'Prueba diferentes rotaciones'],
      author: 'Elvis',
      createdAt: new Date('2024-01-10'),
      solvedCount: 67,
      isActive: true,
      attachments: [
        { id: 'att-3', name: 'message.enc', type: 'file', url: '/files/crypto-001/message.enc' }
      ]
    },
    {
      id: 'forensics-001',
      title: 'Hidden in Plain Sight',
      description: 'Una imagen aparentemente normal esconde un secreto. Usa técnicas de esteganografía.',
      category: 'forensics',
      difficulty: 'easy',
      points: 100,
      skills: ['Steganography', 'File Analysis', 'Metadata'],
      hints: ['Los strings pueden revelar secretos', 'Revisa los metadatos EXIF'],
      author: 'Elvis',
      createdAt: new Date('2024-02-01'),
      solvedCount: 52,
      isActive: true,
      attachments: [
        { id: 'att-6', name: 'secret_image.png', type: 'file', url: '/files/forensics-001/secret_image.png' }
      ]
    }
  ];

  // Retos resueltos por el usuario (local storage o API)
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
   * Retorna respuesta normalizada con success/message
   */
  submitFlagToApi(challengeId: string, flag: string): Observable<FlagSubmitResult> {
    // Validar si es un UUID válido para evitar error 422 del backend con IDs de mock
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(challengeId)) {
      // Si no es UUID, forzamos un error para que el componente use el fallback local
      return new Observable(observer => observer.error(new Error('Invalid UUID')));
    }

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
        solvedChallenges: data.solved || 0,  // ✅ Usar datos del backend
        totalPoints: data.total_points || 0,
        earnedPoints: data.earned_points || 0
      })),
      catchError(() => of(this.getStats()))
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

  // ==================== SYNC METHODS (FALLBACK) ====================

  getChallenges(filter?: CTFFilter): CTFChallenge[] {
    let result = [...this.mockChallenges].filter(c => c.isActive);

    if (filter) {
      if (filter.category && filter.category !== 'all') {
        result = result.filter(c => c.category === filter.category);
      }
      if (filter.difficulty && filter.difficulty !== 'all') {
        result = result.filter(c => c.difficulty === filter.difficulty);
      }
      if (filter.search) {
        const searchLower = filter.search.toLowerCase();
        result = result.filter(c =>
          c.title.toLowerCase().includes(searchLower) ||
          c.description.toLowerCase().includes(searchLower) ||
          c.skills.some(s => s.toLowerCase().includes(searchLower))
        );
      }
      if (filter.showSolved === false) {
        result = result.filter(c => !this.isSolved(c.id));
      }
    }

    return result;
  }

  getChallengeById(id: string): CTFChallenge | undefined {
    return this.mockChallenges.find(c => c.id === id);
  }

  getChallengesByCategory(category: CTFCategory): CTFChallenge[] {
    return this.mockChallenges.filter(c => c.category === category && c.isActive);
  }

  getChallengesByDifficulty(difficulty: CTFDifficulty): CTFChallenge[] {
    return this.mockChallenges.filter(c => c.difficulty === difficulty && c.isActive);
  }

  getStats(): CTFStats {
    const activeChallenges = this.mockChallenges.filter(c => c.isActive);
    const solvedList = activeChallenges.filter(c => this.solvedChallenges.has(c.id));

    return {
      totalChallenges: activeChallenges.length,
      solvedChallenges: solvedList.length,
      totalPoints: activeChallenges.reduce((sum, c) => sum + c.points, 0),
      earnedPoints: solvedList.reduce((sum, c) => sum + c.points, 0)
    };
  }

  getCategories(): { category: CTFCategory; count: number }[] {
    const categoryCount = new Map<CTFCategory, number>();

    this.mockChallenges.filter(c => c.isActive).forEach(c => {
      categoryCount.set(c.category, (categoryCount.get(c.category) || 0) + 1);
    });

    return Array.from(categoryCount.entries()).map(([category, count]) => ({
      category,
      count
    }));
  }

  isSolved(challengeId: string): boolean {
    return this.solvedChallenges.has(challengeId);
  }

  // ==================== LEGACY ASYNC METHODS ====================

  async submitFlag(submission: CTFSubmission): Promise<{ success: boolean; message: string }> {
    return new Promise((resolve) => {
      this.submitFlagToApi(submission.challengeId, submission.flag).subscribe({
        next: (response) => {
          // response ya tiene success y message mapeados
          resolve(response);
        },
        error: () => {
          // Fallback a verificación local mock
          const challenge = this.getChallengeById(submission.challengeId);
          if (!challenge) {
            resolve({ success: false, message: 'Reto no encontrado' });
            return;
          }
          const correctFlag = `flag{${submission.challengeId}}`;
          if (submission.flag.trim().toLowerCase() === correctFlag.toLowerCase()) {
            this.solvedChallenges.add(submission.challengeId);
            resolve({ success: true, message: `¡Correcto! +${challenge.points} puntos` });
          } else {
            resolve({ success: false, message: 'Flag incorrecta. Sigue intentando.' });
          }
        }
      });
    });
  }

  async createChallenge(form: CTFChallengeForm): Promise<CTFChallenge> {
    return new Promise((resolve, reject) => {
      // Intentar crear en API
      this.createChallengeInApi(form).subscribe({
        next: (challenge) => resolve(challenge),
        error: async () => {
          // Fallback: crear localmente
          console.log('Usando creación local de challenge');
          const newChallenge: CTFChallenge = {
            id: `${form.category}-${Date.now()}`,
            ...form,
            author: 'Admin',
            createdAt: new Date(),
            solvedCount: 0
          };
          resolve(newChallenge);
        }
      });
    });
  }

  /**
   * Crear challenge en la API
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
      attachments: form.attachments || []
    };

    return this.api.post<CTFApiResponse>('/ctfs', payload).pipe(
      map(response => this.mapApiToChallenge(response)),
      catchError(err => {
        console.error('Error creating challenge in API:', err);
        throw err;
      })
    );
  }

  async updateChallenge(id: string, form: Partial<CTFChallengeForm>): Promise<CTFChallenge | null> {
    // TODO: Implementar con API
    await new Promise(resolve => setTimeout(resolve, 500));
    return null;
  }

  async deleteChallenge(id: string): Promise<boolean> {
    // TODO: Implementar con API
    await new Promise(resolve => setTimeout(resolve, 500));
    return false;
  }
}
