import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { TechBadgeComponent } from '@shared/components';
import { IconComponent } from '@shared/icons/icon.component';

const AREAS: { area: string; match: RegExp }[] = [
  { area: 'Backend', match: /^(python|fastapi|django|flask|sqlalchemy|alembic|node|express|java|spring|go)/i },
  { area: 'Frontend', match: /^(typescript|javascript|angular|react|vue|tailwind|html|css|scss|rxjs)/i },
  { area: 'Datos', match: /^(postgres|mysql|sql ?server|sqlite|redis|mongo|sqlmodel)/i },
  { area: 'Seguridad y operación', match: /^(docker|jwt|devsecops|ci\/?cd|owasp|nginx|linux|kubernetes|github actions|security)/i }
];

export interface StackGroup {
  area: string;
  items: string[];
}

/** Agrupa el stack plano del perfil por áreas; lo que no encaja va a "Otros". */
export function groupStack(items: string[]): StackGroup[] {
  const groups = new Map<string, string[]>();
  items.forEach(item => {
    const area = AREAS.find(a => a.match.test(item.trim()))?.area ?? 'Otros';
    groups.set(area, [...(groups.get(area) ?? []), item]);
  });
  return [...AREAS.map(a => a.area), 'Otros']
    .filter(area => groups.has(area))
    .map(area => ({ area, items: groups.get(area) ?? [] }));
}

@Component({
  selector: 'app-about-section',
  standalone: true,
  imports: [CommonModule, RouterLink, TechBadgeComponent, IconComponent],
  templateUrl: './about-section.component.html',
  styleUrls: ['./about-section.component.scss']
})
export class AboutSectionComponent implements OnChanges {
  @Input() aboutPoints: string[] = [];
  @Input() stackItems: string[] = [];
  /** Absolute resolved avatar URL (or null). */
  @Input() avatarUrl: string | null = null;
  /** Optional honest subtitle (e.g. roles joined) — omit when empty. */
  @Input() stackLine: string | null = null;
  @Input() showCtfLink = false;

  avatarBroken = false;
  /** Campo calculado en ngOnChanges (un getter crearía arrays nuevos en cada ciclo). */
  stackGroups: StackGroup[] = [];

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['avatarUrl']) {
      this.avatarBroken = false;
    }
    if (changes['stackItems']) {
      this.stackGroups = groupStack(this.stackItems);
    }
  }

  trackByArea(_: number, group: StackGroup): string {
    return group.area;
  }

  onAvatarError(): void {
    this.avatarBroken = true;
  }
}
