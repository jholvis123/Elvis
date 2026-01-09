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
    // Solo llamar a la carga inicial desde API
    this.loadDataFromApi();
  }

  /**
   * Carga datos desde la API
   */
  loadDataFromApi(): void {
    this.isLoading = true;

    // Cargar challenges desde API
    this.ctfService.getChallengesFromApi(this.filter).subscribe({
      next: (challenges) => {
        this.challenges = challenges; // El backend ya filtra si se le pasan params, o el frontend filtra si la API devuelve todo.
        // Nota: getChallengesFromApi ya soporta filtros en CtfService.
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error loading challenges:', err);
        this.challenges = []; // No mock data
        this.isLoading = false;
      }
    });

    // Cargar stats desde API
    this.ctfService.getStatsFromApi().subscribe({
      next: (stats) => {
        this.stats = stats;
      },
      error: (err) => console.error('Error loading stats:', err)
    });
  }

  onFilterChange(): void {
    this.loadDataFromApi();
  }

  clearFilters(): void {
    this.filter = {
      category: 'all',
      difficulty: 'all',
      search: '',
      showSolved: true
    };
    this.loadDataFromApi();
  }

  isSolved(challengeId: string): boolean {
    return this.ctfService.isSolved(challengeId);
  }

  get progressPercentage(): number {
    if (this.stats.totalChallenges === 0) return 0;
    return Math.round((this.stats.solvedChallenges / this.stats.totalChallenges) * 100);
  }
}
