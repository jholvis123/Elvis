import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ExperienceItem, CapabilityChip, ExperienceKind } from '@core/models';
import { TechBadgeComponent } from '@shared/components';
import { IconComponent } from '@shared/icons/icon.component';

@Component({
  selector: 'app-experience-section',
  standalone: true,
  imports: [CommonModule, TechBadgeComponent, IconComponent],
  templateUrl: './experience-section.component.html',
  styleUrls: ['./experience-section.component.scss']
})
export class ExperienceSectionComponent {
  @Input() items: ExperienceItem[] = [];
  @Input() capabilities: CapabilityChip[] = [];
  @Input() loading = false;
  @Input() loadingCapabilities = false;
  @Input() apiUnavailable = false;
  @Input() experienceError = false;
  @Input() capabilitiesError = false;

  get roleChips(): CapabilityChip[] {
    return this.capabilities.filter(c => c.kind === 'role');
  }

  get skillChips(): CapabilityChip[] {
    return this.capabilities.filter(c => c.kind === 'skill');
  }

  formatDateRange(item: ExperienceItem): string {
    const start = this.formatDate(item.start_date);
    const end = item.current || !item.end_date
      ? 'Actualidad'
      : this.formatDate(item.end_date);
    if (!start) {
      return item.current ? 'Actualidad' : end !== 'Actualidad' ? end : '';
    }
    return `${start} — ${end}`;
  }

  kindLabel(kind: ExperienceKind): string {
    switch (kind) {
      case 'project':
        return 'Proyecto';
      case 'training':
        return 'Formación';
      case 'security':
        return 'Seguridad';
      default:
        return String(kind || '');
    }
  }

  private formatDate(value: string | null | undefined): string {
    if (!value) {
      return '';
    }
    const trimmed = value.trim();
    const match = /^(\d{4})-(\d{2})(?:-(\d{2}))?$/.exec(trimmed);
    if (match) {
      const year = Number(match[1]);
      const month = Number(match[2]) - 1;
      const day = match[3] ? Number(match[3]) : 1;
      const date = new Date(year, month, day);
      if (!Number.isNaN(date.getTime())) {
        return date.toLocaleDateString('es', { month: 'short', year: 'numeric' });
      }
    }
    return trimmed;
  }

  trackByExperience(_: number, item: ExperienceItem): string {
    return item.id;
  }

  trackByCapability(_: number, chip: CapabilityChip): string {
    return `${chip.kind}:${chip.category ?? ''}:${chip.label}`;
  }
}
