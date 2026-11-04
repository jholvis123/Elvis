import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { CtfService, LeaderboardEntry, UserStats } from '../../../../core/services/ctf.service';
import { AuthService } from '../../../../core/services/auth.service';
import { IconComponent } from '@shared/icons/icon.component';
import { LoadingSpinnerComponent } from '@shared/components/loading-spinner/loading-spinner.component';

/** Ranking de jugadores: puntos de retos menos pistas, empate para quien llegó antes. */
@Component({
  selector: 'app-leaderboard',
  standalone: true,
  imports: [CommonModule, RouterLink, IconComponent, LoadingSpinnerComponent],
  templateUrl: './leaderboard.component.html',
  styleUrls: ['./leaderboard.component.scss']
})
export class LeaderboardComponent implements OnInit {
  private readonly ctfService = inject(CtfService);
  private readonly authService = inject(AuthService);

  leaderboard: LeaderboardEntry[] = [];
  totalPlayers = 0;
  myStats: UserStats | null = null;
  loading = true;
  loadError = false;

  get isAuthenticated(): boolean {
    return this.authService.isAuthenticated;
  }

  get podium(): LeaderboardEntry[] {
    return this.leaderboard.slice(0, 3);
  }

  get rest(): LeaderboardEntry[] {
    return this.leaderboard.slice(3);
  }

  /** True si el jugador actual está en el ranking pero fuera de la lista mostrada. */
  get meOutsideList(): boolean {
    return !!this.myStats?.rank && !this.leaderboard.some(e => this.isMe(e));
  }

  ngOnInit(): void {
    this.ctfService.getLeaderboard(50).subscribe({
      next: response => {
        this.leaderboard = response.entries;
        this.totalPlayers = response.total_players;
        this.loading = false;
      },
      error: () => {
        this.loadError = true;
        this.loading = false;
      }
    });

    if (this.authService.isAuthenticated && !this.authService.isAdmin) {
      this.ctfService.getMyStats().subscribe({
        next: stats => (this.myStats = stats),
        error: () => (this.myStats = null)
      });
    }
  }

  isMe(entry: LeaderboardEntry): boolean {
    return !!this.myStats && entry.user_id === this.myStats.user_id;
  }

  trackByUser(_: number, entry: LeaderboardEntry): string {
    return entry.user_id;
  }
}
