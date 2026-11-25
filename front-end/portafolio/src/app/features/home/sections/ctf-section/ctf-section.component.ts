import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { BoardChallenge, CtfService, LeaderboardEntry } from '@core/services/ctf.service';
import { CTF_CATEGORIES } from '@core/models/ctf.model';

/** Adelanto del CTF Lab en la portada: 3 retos reales y el top 3 del ranking. */
@Component({
  selector: 'app-ctf-section',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './ctf-section.component.html',
  styleUrls: ['./ctf-section.component.scss']
})
export class CtfSectionComponent implements OnInit {
  private readonly ctf = inject(CtfService);
  private readonly destroyRef = inject(DestroyRef);

  challenges: (BoardChallenge & { categoryLabel: string })[] = [];
  top: LeaderboardEntry[] = [];
  total = 0;
  players = 0;
  loaded = false;

  ngOnInit(): void {
    this.ctf.getBoard().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: board => {
        this.total = board.total;
        // Un reto por categoría, empezando por los más accesibles
        this.challenges = board.categories
          .map(cat => ({
            ...cat.challenges[0],
            categoryLabel: CTF_CATEGORIES.find(c => c.value === cat.category)?.label ?? cat.category
          }))
          .filter(ch => !!ch.id)
          .slice(0, 3);
        this.loaded = true;
      },
      error: () => (this.loaded = true)
    });
    this.ctf.getLeaderboard(3).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: res => {
        this.top = res.entries;
        this.players = res.total_players;
      },
      error: () => (this.top = [])
    });
  }

  trackById(_: number, item: { id: string }): string {
    return item.id;
  }

  trackByUser(_: number, item: LeaderboardEntry): string {
    return item.user_id;
  }
}
