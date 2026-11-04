import {
  AfterViewInit,
  Component,
  ElementRef,
  EventEmitter,
  HostListener,
  Input,
  OnDestroy,
  OnInit,
  Output,
  ViewChild,
  inject
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';

import { CtfService, CTFSolve, FlagSubmitResult } from '@core/services/ctf.service';
import { AuthService } from '@core/services/auth.service';
import { CTFChallenge, CTF_CATEGORIES, CTF_DIFFICULTIES } from '@core/models/ctf.model';
import { IconComponent } from '@shared/icons/icon.component';
import { MarkdownViewerComponent } from '@shared/components/markdown-viewer/markdown-viewer.component';

type Tab = 'challenge' | 'solves';

/** Formato que exige el backend (FlagService._validate_flag_format). */
const FLAG_FORMAT = /^flag\{.+\}$/;

/**
 * Ventana modal de un reto (estilo CTFd): pestañas Reto / Resoluciones,
 * pistas con coste, envío de flag en línea y validación de formato en vivo.
 */
@Component({
  selector: 'app-challenge-modal',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, IconComponent, MarkdownViewerComponent],
  templateUrl: './challenge-modal.component.html',
  styleUrls: ['./challenge-modal.component.scss']
})
export class ChallengeModalComponent implements OnInit, AfterViewInit, OnDestroy {
  private readonly ctfService = inject(CtfService);
  private readonly authService = inject(AuthService);

  @Input({ required: true }) challengeId!: string;
  @Input() solvedByMe = false;
  @Output() closed = new EventEmitter<void>();
  @Output() solved = new EventEmitter<string>();
  @Output() scoreChanged = new EventEmitter<void>();

  @ViewChild('closeBtn') closeBtn?: ElementRef<HTMLButtonElement>;

  challenge: CTFChallenge | null = null;
  loading = true;
  loadError = false;

  tab: Tab = 'challenge';
  solves: CTFSolve[] = [];
  solvesLoaded = false;
  solvesLoading = false;

  flagInput = '';
  submitting = false;
  result: FlagSubmitResult | null = null;

  /** Pistas gratis que el jugador decidió mostrar (no cuestan nada). */
  revealedFree = new Set<number>();
  unlocking: number | null = null;
  hintError = '';

  private previousFocus: HTMLElement | null = null;

  get isAuthenticated(): boolean {
    return this.authService.isAuthenticated;
  }

  get isAdmin(): boolean {
    return this.authService.isAdmin;
  }

  get categoryLabel(): string {
    return CTF_CATEGORIES.find(c => c.value === this.challenge?.category)?.label ?? '';
  }

  get difficulty() {
    return CTF_DIFFICULTIES.find(d => d.value === this.challenge?.difficulty);
  }

  get flagFormatState(): 'empty' | 'ok' | 'bad' {
    const value = this.flagInput.trim();
    if (!value) return 'empty';
    return FLAG_FORMAT.test(value) ? 'ok' : 'bad';
  }

  ngOnInit(): void {
    this.previousFocus = document.activeElement as HTMLElement | null;
    document.body.style.overflow = 'hidden';
    this.load();
  }

  ngAfterViewInit(): void {
    setTimeout(() => this.closeBtn?.nativeElement.focus());
  }

  ngOnDestroy(): void {
    document.body.style.overflow = '';
    this.previousFocus?.focus?.();
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.close();
  }

  close(): void {
    this.closed.emit();
  }

  onBackdrop(event: MouseEvent): void {
    if (event.target === event.currentTarget) {
      this.close();
    }
  }

  selectTab(tab: Tab): void {
    this.tab = tab;
    if (tab === 'solves' && !this.solvesLoaded) {
      this.loadSolves();
    }
  }

  private load(): void {
    this.loading = true;
    this.ctfService.getChallengeByIdFromApi(this.challengeId).subscribe({
      next: challenge => {
        this.challenge = challenge;
        this.loadError = !challenge;
        this.loading = false;
      },
      error: () => {
        this.loadError = true;
        this.loading = false;
      }
    });
  }

  private loadSolves(): void {
    this.solvesLoading = true;
    this.ctfService.getSolves(this.challengeId).subscribe({
      next: response => {
        // El backend guarda UTC sin zona ("2026-11-04T17:20:00"): marcarlo como UTC
        this.solves = response.items.map(s => ({
          ...s,
          solved_at: /[zZ]|[+-]\d\d:?\d\d$/.test(s.solved_at) ? s.solved_at : `${s.solved_at}Z`
        }));
        this.solvesLoaded = true;
        this.solvesLoading = false;
      },
      error: () => {
        this.solvesLoading = false;
      }
    });
  }

  // ---------------------------------------------------------------- pistas

  hintCost(index: number): number {
    return this.challenge?.hintCosts?.[index] ?? 0;
  }

  isHintVisible(index: number): boolean {
    const text = this.challenge?.hints?.[index];
    if (text === null || text === undefined) return false;
    // Pistas de pago ya desbloqueadas se muestran directamente; las gratis tras pulsar
    return this.hintCost(index) > 0 || this.revealedFree.has(index);
  }

  isHintLocked(index: number): boolean {
    return this.challenge?.hints?.[index] === null;
  }

  revealFree(index: number): void {
    this.revealedFree.add(index);
  }

  unlockHint(index: number): void {
    if (!this.challenge || this.unlocking !== null) return;
    this.unlocking = index;
    this.hintError = '';
    this.ctfService.unlockHint(this.challenge.id, index).subscribe({
      next: response => {
        if (this.challenge?.hints) {
          const hints = [...this.challenge.hints];
          hints[index] = response.hint;
          this.challenge = { ...this.challenge, hints };
        }
        this.unlocking = null;
        if (response.cost > 0 && !response.already_unlocked) {
          this.scoreChanged.emit();
        }
      },
      error: (err: HttpErrorResponse) => {
        this.unlocking = null;
        this.hintError = err.status === 401
          ? 'Inicia sesión con tu alias para desbloquear pistas.'
          : 'No se pudo desbloquear la pista. Inténtalo de nuevo.';
      }
    });
  }

  // ---------------------------------------------------------------- flag

  submit(): void {
    if (!this.challenge || this.submitting || this.solvedByMe) return;
    if (this.flagFormatState !== 'ok') {
      this.result = { success: false, message: 'Formato esperado: flag{...}' };
      return;
    }
    const challengeId = this.challenge.id;
    this.submitting = true;
    this.result = null;
    this.ctfService.submitFlagToApi(challengeId, this.flagInput.trim()).subscribe({
      next: result => {
        this.result = result;
        this.submitting = false;
        if (result.success) {
          this.flagInput = '';
          this.solvedByMe = true;
          this.solvesLoaded = false;
          this.solved.emit(challengeId);
        }
      },
      error: (err: HttpErrorResponse) => {
        this.submitting = false;
        this.result = {
          success: false,
          message: err.status === 429
            ? 'Demasiados intentos. Espera un minuto.'
            : (err.error?.detail || 'No se pudo enviar la flag.')
        };
      }
    });
  }
}
