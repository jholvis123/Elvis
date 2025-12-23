import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { TechBadgeComponent } from '@shared/components';

@Component({
  selector: 'app-about-section',
  standalone: true,
  imports: [CommonModule, RouterLink, TechBadgeComponent],
  templateUrl: './about-section.component.html',
  styleUrls: ['./about-section.component.scss']
})
export class AboutSectionComponent {
  @Input() aboutPoints: string[] = [];
  @Input() stackItems: string[] = [];
}
