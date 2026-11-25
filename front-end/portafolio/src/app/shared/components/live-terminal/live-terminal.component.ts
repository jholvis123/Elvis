import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  Input,
  NgZone,
  OnChanges,
  OnDestroy,
  inject
} from '@angular/core';
import { CommonModule } from '@angular/common';

/** Una orden de la sesión: lo que se teclea y las líneas que devuelve. */
export interface TerminalStep {
  cmd: string;
  out: { text: string; tone?: 'default' | 'muted' | 'accent' | 'ok' | 'warn' }[];
}

interface RenderedLine {
  kind: 'cmd' | 'out';
  text: string;
  tone: string;
}

const MAX_LINES = 12;

/**
 * Terminal "en uso": teclea cada orden a ritmo humano, muestra su salida y repite.
 *
 * Criterio de movimiento:
 * - Solo corre mientras está en pantalla y la pestaña está visible (no gasta CPU ni distrae).
 * - Con prefers-reduced-motion muestra la sesión ya escrita, sin teclear.
 * - Altura fija: la página no salta mientras escribe.
 * - El texto que escribe es decorativo: aria-hidden; los datos reales van en sr-only.
 */
@Component({
  selector: 'app-live-terminal',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="term">
      <div class="term__bar">
        <span class="term__dots" aria-hidden="true"><span></span><span></span><span></span></span>
        <span class="term__title">{{ host }}: ~ — zsh</span>
        <span class="term__live" aria-hidden="true"><span class="term__pulse"></span>{{ running ? 'en vivo' : 'en pausa' }}</span>
      </div>
      <p class="sr-only">{{ summary }}</p>
      <div class="term__body" aria-hidden="true">
        <div *ngFor="let line of lines; trackBy: trackByIndex" class="term__line" [ngClass]="'tone-' + line.tone">
          <ng-container *ngIf="line.kind === 'cmd'; else out">
            <span class="term__prompt">{{ prompt }}</span>{{ line.text }}
          </ng-container>
          <ng-template #out>{{ line.text }}</ng-template>
        </div>
        <div class="term__line">
          <span class="term__prompt">{{ prompt }}</span>{{ typing }}<span class="term__cursor"></span>
        </div>
      </div>
    </div>
  `,
  styleUrls: ['./live-terminal.component.scss']
})
export class LiveTerminalComponent implements AfterViewInit, OnChanges, OnDestroy {
  private readonly host$ = inject(ElementRef<HTMLElement>);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly zone = inject(NgZone);

  @Input() steps: TerminalStep[] = [];
  @Input() host = 'elvis@lab';
  /** Retraso antes de empezar a teclear (deja terminar la entrada de la tarjeta). */
  @Input() startDelay = 700;

  lines: RenderedLine[] = [];
  typing = '';
  running = false;

  private timer: ReturnType<typeof setTimeout> | null = null;
  private visible = false;
  private io?: IntersectionObserver;
  /** Se decide antes del primer render: con reduced motion la sesión sale ya escrita. */
  private readonly reducedMotion =
    typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches;
  private step = 0;
  private char = 0;
  private outIndex = 0;
  private phase: 'type' | 'enter' | 'out' | 'rest' = 'type';
  private started = false;
  private stepsKey = '';

  get prompt(): string {
    return `${this.host}:~$ `;
  }

  /** Versión textual para lectores de pantalla (la animación es decorativa). */
  get summary(): string {
    return this.steps
      .map(s => `${s.cmd}: ${s.out.map(o => o.text).join(' ')}`)
      .join('. ');
  }

  ngAfterViewInit(): void {
    if (this.reducedMotion) {
      return; // ngOnChanges ya pintó la sesión completa
    }
    document.addEventListener('visibilitychange', this.onVisibility);
    if (typeof IntersectionObserver === 'undefined') {
      this.visible = true;
      this.resume(this.startDelay);
      return;
    }
    this.io = new IntersectionObserver(([entry]) => {
      this.visible = entry.isIntersecting;
      if (this.visible) {
        this.resume(this.started ? 0 : this.startDelay);
      } else {
        this.pause();
      }
    }, { threshold: 0.2 });
    this.io.observe(this.host$.nativeElement);
  }

  ngOnChanges(): void {
    // Reiniciar solo si la sesión cambió de verdad (p. ej. llegan los conteos de la API)
    const key = JSON.stringify(this.steps);
    if (key === this.stepsKey) {
      return;
    }
    this.stepsKey = key;
    if (this.reducedMotion) {
      this.renderFinal();
      return;
    }
    if (this.started) {
      this.reset();
      if (this.visible && !document.hidden) {
        this.resume(300);
      }
    }
  }

  ngOnDestroy(): void {
    this.pause();
    this.io?.disconnect();
    document.removeEventListener('visibilitychange', this.onVisibility);
  }

  trackByIndex(index: number): number {
    return index;
  }

  private readonly onVisibility = (): void => {
    if (document.hidden) {
      this.pause();
    } else if (this.visible) {
      this.resume(200);
    }
  };

  private resume(delay: number): void {
    if (this.timer || !this.steps.length) {
      return;
    }
    this.started = true;
    this.running = true;
    this.cdr.markForCheck();
    this.schedule(delay);
  }

  private pause(): void {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    if (this.running) {
      this.running = false;
      this.cdr.markForCheck();
    }
  }

  private reset(): void {
    this.pause();
    this.lines = [];
    this.typing = '';
    this.step = 0;
    this.char = 0;
    this.outIndex = 0;
    this.phase = 'type';
    this.cdr.markForCheck();
  }

  private schedule(delay: number): void {
    // Fuera de la zona de Angular: un setTimeout por tecla no debe disparar
    // detección de cambios en toda la app; solo marcamos este componente.
    this.zone.runOutsideAngular(() => {
      this.timer = setTimeout(() => {
        this.timer = null;
        this.zone.run(() => this.tick());
      }, delay);
    });
  }

  private push(line: RenderedLine): void {
    this.lines = [...this.lines, line].slice(-MAX_LINES);
  }

  private tick(): void {
    if (!this.running) {
      return;
    }
    const current = this.steps[this.step];
    if (!current) {
      // Fin de la sesión: pausa, limpiar pantalla y volver a empezar
      if (this.phase !== 'rest') {
        this.phase = 'rest';
        this.cdr.markForCheck();
        this.schedule(2800);
        return;
      }
      this.lines = [];
      this.step = 0;
      this.char = 0;
      this.phase = 'type';
      this.cdr.markForCheck();
      this.schedule(500);
      return;
    }

    switch (this.phase) {
      case 'type':
        if (this.char < current.cmd.length) {
          this.char++;
          this.typing = current.cmd.slice(0, this.char);
          this.cdr.markForCheck();
          // Ritmo humano: irregular, más rápido en letras que en símbolos
          const symbol = /[^a-z0-9]/i.test(current.cmd[this.char - 1] ?? '');
          this.schedule((symbol ? 90 : 45) + Math.random() * 70);
          return;
        }
        this.phase = 'enter';
        this.schedule(320);
        return;
      case 'enter':
        this.push({ kind: 'cmd', text: current.cmd, tone: 'default' });
        this.typing = '';
        this.outIndex = 0;
        this.phase = 'out';
        this.cdr.markForCheck();
        this.schedule(180);
        return;
      case 'out':
        if (this.outIndex < current.out.length) {
          const o = current.out[this.outIndex++];
          this.push({ kind: 'out', text: o.text, tone: o.tone ?? 'default' });
          this.cdr.markForCheck();
          this.schedule(110);
          return;
        }
        this.step++;
        this.char = 0;
        this.phase = 'type';
        this.schedule(1000);
        return;
      default:
        return;
    }
  }

  private renderFinal(): void {
    const lines: RenderedLine[] = [];
    this.steps.forEach(s => {
      lines.push({ kind: 'cmd', text: s.cmd, tone: 'default' });
      s.out.forEach(o => lines.push({ kind: 'out', text: o.text, tone: o.tone ?? 'default' }));
    });
    this.lines = lines.slice(-MAX_LINES);
    this.typing = '';
    this.running = false;
    this.cdr.markForCheck();
  }
}
