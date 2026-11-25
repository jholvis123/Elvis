import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { IconComponent } from '@shared/icons/icon.component';
import {
  LiveTerminalComponent,
  TerminalStep
} from '@shared/components/live-terminal/live-terminal.component';

interface HeroStat {
  value: number;
  label: string;
}

/** Nombre de carpeta legible a partir del título de un proyecto ("Global — Sistema…" → "global/"). */
function folderName(title: string): string {
  const base = title.split(/[—–:(]/)[0].trim().toLowerCase();
  const slug = base
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return slug ? `${slug}/` : '';
}

@Component({
  selector: 'app-hero-section',
  standalone: true,
  imports: [CommonModule, RouterLink, IconComponent, LiveTerminalComponent],
  templateUrl: './hero-section.component.html',
  styleUrls: ['./hero-section.component.scss']
})
export class HeroSectionComponent implements OnChanges {
  @Input() roles: string[] = [];
  @Input() technologies: string[] = [];
  /** Absolute resolved avatar URL (or null). */
  @Input() avatarUrl: string | null = null;
  @Input() githubUrl: string | null = null;
  @Input() linkedinUrl: string | null = null;
  /** Títulos de proyectos publicados (para `ls proyectos/`). */
  @Input() projectTitles: string[] = [];
  /** Conteos reales de la API (SectionVisibilityService). 0 = se oculta. */
  @Input() projectsCount = 0;
  @Input() ctfCount = 0;
  @Input() writeupsCount = 0;
  /** Gate hero CTAs by live section counts. */
  @Input() showProjectsCta = false;
  @Input() showCtfCta = false;

  avatarBroken = false;
  terminalSteps: TerminalStep[] = [];

  /** Subtítulo corto de la tarjeta (los roles completos salen en `whoami`). */
  readonly cardRole = 'Fullstack · Ciberseguridad';

  get roleLine(): string {
    return this.roles.length ? this.roles.slice(0, 2).join(' · ') : this.cardRole;
  }

  /**
   * Solo datos reales: una estadística en 0 no se muestra.
   * Campo (no getter): un array nuevo por ciclo haría que *ngFor recreara el DOM,
   * el MutationObserver de la portada lo detectaría y dispararía otro ciclo.
   */
  stats: HeroStat[] = [];

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['avatarUrl']) {
      this.avatarBroken = false;
    }
    this.stats = [
      { value: this.projectsCount, label: 'proyectos públicos' },
      { value: this.ctfCount, label: 'retos en el lab' },
      { value: this.writeupsCount, label: 'writeups' }
    ].filter(stat => stat.value > 0);
    this.terminalSteps = this.buildSteps();
  }

  trackByLabel(_: number, stat: HeroStat): string {
    return stat.label;
  }

  onAvatarError(): void {
    this.avatarBroken = true;
  }

  /** La sesión de la terminal se arma con datos reales del perfil y de la API. */
  private buildSteps(): TerminalStep[] {
    const steps: TerminalStep[] = [
      {
        cmd: 'whoami',
        out: [
          { text: 'Yhon Elvis Siñani · Ingeniero de Sistemas' },
          { text: this.roleLine, tone: 'muted' }
        ]
      }
    ];
    if (this.technologies.length) {
      steps.push({
        cmd: 'cat stack.txt',
        out: [{ text: this.technologies.slice(0, 8).join('  ').toLowerCase(), tone: 'accent' }]
      });
    }
    const folders = this.projectTitles.map(folderName).filter(Boolean).slice(0, 4);
    if (folders.length) {
      steps.push({ cmd: 'ls proyectos/', out: [{ text: folders.join('  '), tone: 'accent' }] });
    }
    if (this.ctfCount > 0) {
      steps.push({
        cmd: './ctf-lab --estado',
        out: [
          { text: `${this.ctfCount} retos publicados · ranking abierto`, tone: 'ok' },
          { text: 'crea un alias y envía tu primera flag', tone: 'muted' }
        ]
      });
    }
    steps.push({ cmd: 'echo $DISPONIBLE', out: [{ text: 'true — hablemos', tone: 'warn' }] });
    return steps;
  }
}
