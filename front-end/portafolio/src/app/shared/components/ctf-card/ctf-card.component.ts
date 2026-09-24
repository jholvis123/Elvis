import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { CTFChallenge, CTF_CATEGORIES, CTF_DIFFICULTIES, AttachmentType } from '@core/models/ctf.model';
import { IconComponent, IconName } from '@shared/icons/icon.component';

@Component({
  selector: 'app-ctf-card',
  standalone: true,
  imports: [CommonModule, RouterLink, IconComponent],
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

  /** Plain-text preview: strip markdown fences/markers so long n/c never widen the card. */
  get descriptionPreview(): string {
    return stripMarkdownToPlain(this.challenge?.description || '');
  }

  getAttachmentIconName(type: AttachmentType): IconName {
    const icons: Record<AttachmentType, IconName> = {
      file: 'paper-clip',
      url: 'link',
      docker: 'cube'
    };
    return icons[type] || 'paper-clip';
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

/** Exported for unit tests. */
export function stripMarkdownToPlain(md: string): string {
  if (!md) {
    return '';
  }
  let text = md;
  // Fenced code blocks → drop contents (params live in detail)
  text = text.replace(/```[\s\S]*?```/g, ' ');
  // Inline code
  text = text.replace(/`([^`]+)`/g, '$1');
  // Images / links
  text = text.replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1');
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
  // Headings / emphasis / lists
  text = text.replace(/^#{1,6}\s+/gm, '');
  text = text.replace(/(\*\*|__)(.*?)\1/g, '$2');
  text = text.replace(/(\*|_)(.*?)\1/g, '$2');
  text = text.replace(/^\s*[-*+]\s+/gm, '');
  text = text.replace(/^\s*\d+\.\s+/gm, '');
  // Collapse whitespace
  text = text.replace(/\s+/g, ' ').trim();
  return text;
}
