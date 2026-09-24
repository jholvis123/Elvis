import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { TechBadgeComponent } from '@shared/components';
import { IconComponent } from '@shared/icons/icon.component';

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

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['avatarUrl']) {
      this.avatarBroken = false;
    }
  }

  onAvatarError(): void {
    this.avatarBroken = true;
  }
}
