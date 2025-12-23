import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { CTFChallenge, CTF_CATEGORIES, CTF_DIFFICULTIES, AttachmentType } from '@core/models/ctf.model';

@Component({
  selector: 'app-ctf-card',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './ctf-card.component.html',
  styleUrls: ['./ctf-card.component.scss']
})
export class CtfCardComponent {
  @Input({ required: true }) challenge!: CTFChallenge;
  @Input() isSolved = false;
  @Input() showDetails = true;
  
  @Output() solve = new EventEmitter<string>();

  get categoryInfo() {
    return CTF_CATEGORIES.find(c => c.value === this.challenge.category);
  }

  get difficultyInfo() {
    return CTF_DIFFICULTIES.find(d => d.value === this.challenge.difficulty);
  }

  get difficultyColorClass(): string {
    const colors: Record<string, string> = {
      easy: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      medium: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      hard: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
      insane: 'bg-red-500/20 text-red-400 border-red-500/30'
    };
    return colors[this.challenge.difficulty] || colors['easy'];
  }

  // Attachment helpers
  getAttachmentIcon(type: AttachmentType): string {
    const icons: Record<AttachmentType, string> = {
      file: '📎',
      url: '🔗',
      docker: '🐳'
    };
    return icons[type] || '📎';
  }

  getAttachmentLabel(type: AttachmentType): string {
    const labels: Record<AttachmentType, string> = {
      file: 'Archivo',
      url: 'URL',
      docker: 'Docker'
    };
    return labels[type] || 'Recurso';
  }

  getAttachmentClass(type: AttachmentType): string {
    const classes: Record<AttachmentType, string> = {
      file: 'ctf-card__attachment--file',
      url: 'ctf-card__attachment--url',
      docker: 'ctf-card__attachment--docker'
    };
    return classes[type] || '';
  }

  onSolveClick(): void {
    this.solve.emit(this.challenge.id);
  }
}
