import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { distinctUntilChanged, skip } from 'rxjs/operators';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { BoardCategory, BoardChallenge, BoardResponse, CtfService } from '@core/services/ctf.service';
import { AuthService } from '@core/services/auth.service';
import { ApiAvailabilityService } from '@core/services/api-availability.service';
import { CTF_CATEGORIES, CTF_DIFFICULTIES } from '@core/models/ctf.model';
import { IconComponent } from '@shared/icons/icon.component';
import { SkeletonLoaderComponent } from '@shared/components/skeleton-loader/skeleton-loader.component';
import { ChallengeModalComponent } from '../../components/challenge-modal/challenge-modal.component';

/**
 * Tablero de retos estilo CTFd: casillas agrupadas por categoría y una
 * ventana modal por reto. `?reto=<id>` abre la modal (enlace compartible).
 */
@Component({
  selector: 'app-ctf-board',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, IconComponent, SkeletonLoaderComponent, ChallengeModalComponent],
  templateUrl: './ctf-board.component.html',
  styleUrls: ['./ctf-board.component.scss']
})
export class CtfBoardComponent implements OnInit {
  private readonly ctfService = inject(CtfService);
  private readonly authService = inject(AuthService);
  private readonly apiAvailability = inject(ApiAvailabilityService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  board: BoardResponse | null = null;
  loading = true;
  apiUnavailable = false;
  hideSolved = false;
  openId: string | null = null;

  get isAuthenticated(): boolean {
    return this.authService.isAuthenticated;
  }

  get isAdmin(): boolean {
    return this.authService.isAdmin;
  }

  get username(): string | null {
    return this.authService.currentUser?.username ?? null;
  }

  get visibleCategories(): BoardCategory[] {
    if (!this.board) return [];
    if (!this.hideSolved) return this.board.categories;
    return this.board.categories
      .map(cat => ({ ...cat, challenges: cat.challenges.filter(c => !c.solved_by_me) }))
      .filter(cat => cat.challenges.length > 0);
  }

  get openChallenge(): BoardChallenge | null {
    if (!this.board || !this.openId) return null;
    for (const cat of this.board.categories) {
      const found = cat.challenges.find(c => c.id === this.openId);
      if (found) return found;
    }
    return null;
  }

  ngOnInit(): void {
    if (!this.apiAvailability.isApiConfigured()) {
      this.apiUnavailable = true;
      this.loading = false;
      return;
    }
    this.route.queryParamMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(params => {
      this.openId = params.get('reto');
    });
    // Recargar al iniciar/cerrar sesión o tras un refresh de token (puntos y "resuelto por mí")
    this.authService.currentUser$
      .pipe(
        // Cada login, logout, /auth/me o refresh emite un objeto nuevo: recargar con esa sesión
        distinctUntilChanged(),
        skip(1),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe(() => this.load());
    this.load();
  }

  load(): void {
    this.ctfService.getBoard().subscribe({
      next: board => {
        this.board = board;
        this.loading = false;
      },
      error: err => {
        this.apiAvailability.noteRequestFailure(err);
        this.apiUnavailable = !this.apiAvailability.isApiAvailable();
        this.loading = false;
      }
    });
  }

  categoryLabel(value: string): string {
    return CTF_CATEGORIES.find(c => c.value === value)?.label ?? value;
  }

  levelLabel(value: string): string {
    return CTF_DIFFICULTIES.find(d => d.value === value)?.label ?? value;
  }

  solvedIn(cat: BoardCategory): number {
    return cat.challenges.filter(c => c.solved_by_me).length;
  }

  totalIn(category: string): number {
    return this.board?.categories.find(c => c.category === category)?.challenges.length ?? 0;
  }

  tileLabel(ch: BoardChallenge): string {
    const state = ch.solved_by_me ? 'resuelto' : `${ch.solves} resoluciones`;
    return `${ch.title}, ${ch.points} puntos, ${this.levelLabel(ch.level)}, ${state}`;
  }

  open(id: string): void {
    this.router.navigate([], { relativeTo: this.route, queryParams: { reto: id }, queryParamsHandling: 'merge' });
  }

  close(): void {
    this.router.navigate([], { relativeTo: this.route, queryParams: { reto: null }, queryParamsHandling: 'merge' });
  }

  onSolved(): void {
    this.load();
  }

  trackById(_: number, item: BoardChallenge): string {
    return item.id;
  }

  trackByCategory(_: number, item: BoardCategory): string {
    return item.category;
  }
}
