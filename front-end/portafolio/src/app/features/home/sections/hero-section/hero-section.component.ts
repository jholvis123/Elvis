import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { Highlight } from '@core/models';
import { TechBadgeComponent } from '@shared/components';
import { StatCardComponent } from '@shared/components/stat-card/stat-card.component';
import { CodeBlockComponent } from '@shared/components/code-block/code-block.component';

@Component({
  selector: 'app-hero-section',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    TechBadgeComponent,
    StatCardComponent,
    CodeBlockComponent
  ],
  templateUrl: './hero-section.component.html',
  styleUrls: ['./hero-section.component.scss']
})
export class HeroSectionComponent implements OnInit, OnDestroy {
  @Input() highlights: Highlight[] = [];
  @Input() technologies: string[] = [];
  @Input() roles: string[] = [];

  currentRole = '';
  private roleIndex = 0;
  private charIndex = 0;
  private isDeleting = false;
  private readonly typingSpeed = 100;
  private typingInterval: ReturnType<typeof setTimeout> | null = null;

  ngOnInit(): void {
    if (this.roles.length > 0) {
      this.startTyping();
    }
  }

  ngOnDestroy(): void {
    if (this.typingInterval) {
      clearTimeout(this.typingInterval);
    }
  }

  private startTyping(): void {
    const type = (): void => {
      const currentText = this.roles[this.roleIndex];
      
      if (this.isDeleting) {
        this.currentRole = currentText.substring(0, this.charIndex - 1);
        this.charIndex--;
      } else {
        this.currentRole = currentText.substring(0, this.charIndex + 1);
        this.charIndex++;
      }

      let speed = this.isDeleting ? 50 : this.typingSpeed;

      if (!this.isDeleting && this.charIndex === currentText.length) {
        speed = 2000;
        this.isDeleting = true;
      } else if (this.isDeleting && this.charIndex === 0) {
        this.isDeleting = false;
        this.roleIndex = (this.roleIndex + 1) % this.roles.length;
        speed = 500;
      }

      this.typingInterval = setTimeout(type, speed);
    };

    type();
  }
}
