import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { 
  CtfService, 
  LeaderboardEntry, 
  LeaderboardResponse, 
  UserStats, 
  SolvedCTF 
} from '../../../../core/services/ctf.service';
import { AuthService } from '../../../../core/services/auth.service';

@Component({
  selector: 'app-leaderboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './leaderboard.component.html',
  styleUrls: ['./leaderboard.component.scss']
})
export class LeaderboardComponent implements OnInit {
  leaderboard: LeaderboardEntry[] = [];
  myStats: UserStats | null = null;
  loading = true;
  
  constructor(
    private ctfService: CtfService,
    private authService: AuthService
  ) {}
  
  ngOnInit(): void {
    this.loadLeaderboard();
    this.loadMyStats();
  }
  
  loadLeaderboard(): void {
    this.loading = true;
    this.ctfService.getLeaderboard(50).subscribe({
      next: (response) => {
        this.leaderboard = response.entries;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading leaderboard:', err);
        this.loading = false;
      }
    });
  }
  
  loadMyStats(): void {
    // Solo cargar si el usuario está autenticado
    if (!this.authService.isAuthenticated) {
      return;
    }
    
    this.ctfService.getMyStats().subscribe({
      next: (stats) => {
        this.myStats = stats;
      },
      error: (err) => {
        // Silenciar error si no está autenticado
        console.log('Could not load user stats:', err);
      }
    });
  }
}
