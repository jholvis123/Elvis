import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { CtfService } from '@core/services/ctf.service';
import { AuthService } from '@core/services/auth.service';
import { CTFChallenge, CTFFilter, CTFStats, CTF_CATEGORIES, CTF_DIFFICULTIES } from '@core/models/ctf.model';
import { CtfCardComponent } from '@shared/components';

@Component({
  selector: 'app-ctf-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, CtfCardComponent],
  templateUrl: './ctf-list.component.html',
  styleUrls: ['./ctf-list.component.scss']
})
export class CtfListComponent implements OnInit {
  private readonly ctfService = inject(CtfService);
  private readonly authService = inject(AuthService);

  challenges: CTFChallenge[] = [];
  stats: CTFStats = { totalChallenges: 0, solvedChallenges: 0, totalPoints: 0, earnedPoints: 0 };
  isLoading = true;
  
  // Filtros
  filter: CTFFilter = {
    category: 'all',
    difficulty: 'all',
    search: '',
    showSolved: true
  };

  // Constantes para template
  readonly categories = CTF_CATEGORIES;
  readonly difficulties = CTF_DIFFICULTIES;

  /** Verifica si el usuario actual es admin */
  get isAdmin(): boolean {
    return this.authService.isAdmin;
  }

  ngOnInit(): void {
    this.loadChallenges();
    this.loadStats();
    this.loadDataFromApi();
  }

  loadChallenges(): void {
    this.challenges = this.ctfService.getChallenges(this.filter);
  }

  loadStats(): void {
    this.stats = this.ctfService.getStats();
  }

  /**
   * Carga datos desde la API
   */
  loadDataFromApi(): void {
    this.isLoading = true;
    
    // Cargar challenges desde API
    this.ctfService.getChallengesFromApi().subscribe({
      next: (challenges) => {
        if (challenges.length > 0) {
          this.challenges = this.applyFilters(challenges);
        }
        this.isLoading = false;
      },
      error: (err) => {
        console.log('Usando challenges locales:', err.message);
        this.isLoading = false;
      }
    });

    // Cargar stats desde API
    this.ctfService.getStatsFromApi().subscribe({
      next: (stats) => {
        if (stats) this.stats = stats;
      },
      error: (err) => console.log('Usando stats locales:', err.message)
    });
  }

  /**
   * Aplica los filtros actuales a los challenges
   */
  private applyFilters(challenges: CTFChallenge[]): CTFChallenge[] {
    return challenges.filter(challenge => {
      // Filtrar por categoría
      if (this.filter.category !== 'all' && challenge.category !== this.filter.category) {
        return false;
      }
      // Filtrar por dificultad
      if (this.filter.difficulty !== 'all' && challenge.difficulty !== this.filter.difficulty) {
        return false;
      }
      // Filtrar por búsqueda
      if (this.filter.search) {
        const searchLower = this.filter.search.toLowerCase();
        const matchesTitle = challenge.title.toLowerCase().includes(searchLower);
        const matchesDesc = challenge.description.toLowerCase().includes(searchLower);
        if (!matchesTitle && !matchesDesc) return false;
      }
      // Filtrar por resueltos
      if (!this.filter.showSolved && challenge.solved) {
        return false;
      }
      return true;
    });
  }

  onFilterChange(): void {
    // Primero intentar filtrar desde API
    this.ctfService.getChallengesFromApi().subscribe({
      next: (challenges) => {
        if (challenges.length > 0) {
          this.challenges = this.applyFilters(challenges);
        } else {
          this.loadChallenges(); // Fallback local
        }
      },
      error: () => this.loadChallenges() // Fallback local
    });
  }

  clearFilters(): void {
    this.filter = {
      category: 'all',
      difficulty: 'all',
      search: '',
      showSolved: true
    };
    this.onFilterChange();
  }

  isSolved(challengeId: string): boolean {
    return this.ctfService.isSolved(challengeId);
  }

  get progressPercentage(): number {
    if (this.stats.totalChallenges === 0) return 0;
    return Math.round((this.stats.solvedChallenges / this.stats.totalChallenges) * 100);
  }
}
