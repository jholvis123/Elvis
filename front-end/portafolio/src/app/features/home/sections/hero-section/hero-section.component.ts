import { Component, Input, OnInit, OnDestroy, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { Highlight } from '@core/models';
import { TechBadgeComponent } from '@shared/components';
import { StatCardComponent } from '@shared/components/stat-card/stat-card.component';
import { CodeBlockComponent } from '@shared/components/code-block/code-block.component';
import { IconComponent } from '@shared/icons/icon.component';

@Component({
  selector: 'app-hero-section',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    TechBadgeComponent,
    StatCardComponent,
    CodeBlockComponent,
    IconComponent
  ],
  templateUrl: './hero-section.component.html',
  styleUrls: ['./hero-section.component.scss']
})
export class HeroSectionComponent implements OnInit, OnDestroy, OnChanges {
  @Input() highlights: Highlight[] = [];
  @Input() technologies: string[] = [];
  @Input() roles: string[] = [];

  currentRole = '';
  private roleIndex = 0;
  private charIndex = 0;
  private isDeleting = false;
  private readonly typingSpeed = 100;
  private typingInterval: ReturnType<typeof setTimeout> | null = null;
  private typingStarted = false;

  ngOnInit(): void {
    this.tryStartTyping();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['roles'] && !changes['roles'].firstChange) {
      this.resetTyping();
      this.tryStartTyping();
    }
  }

  ngOnDestroy(): void {
    this.clearTyping();
  }

  private tryStartTyping(): void {
    if (this.roles.length > 0 && !this.typingStarted) {
      this.typingStarted = true;
      this.startTyping();
    }
  }

  private resetTyping(): void {
    this.clearTyping();
    this.typingStarted = false;
    this.currentRole = '';
    this.roleIndex = 0;
    this.charIndex = 0;
    this.isDeleting = false;
  }

  private clearTyping(): void {
    if (this.typingInterval) {
      clearTimeout(this.typingInterval);
      this.typingInterval = null;
    }
  }

  private startTyping(): void {
    const type = (): void => {
      if (!this.roles.length) {
        return;
      }
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
