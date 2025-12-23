import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-skeleton-loader',
    standalone: true,
    imports: [CommonModule],
    template: `
    <div class="skeleton-loader" [ngClass]="getSkeletonClass()">
      <div class="skeleton-shimmer"></div>
    </div>
  `,
    styles: [`
    .skeleton-loader {
      position: relative;
      overflow: hidden;
      background: linear-gradient(
        90deg,
        rgba(255, 255, 255, 0.05) 25%,
        rgba(255, 255, 255, 0.1) 50%,
        rgba(255, 255, 255, 0.05) 75%
      );
      background-size: 200% 100%;
      border-radius: 0.5rem;
    }

    .skeleton-shimmer {
      position: absolute;
      top: 0;
      left: -100%;
      height: 100%;
      width: 100%;
      background: linear-gradient(
        90deg,
        transparent,
        rgba(255, 255, 255, 0.1),
        transparent
      );
      animation: shimmer 1.5s infinite;
    }

    @keyframes shimmer {
      0% {
        left: -100%;
      }
      100% {
        left: 100%;
      }
    }

    /* Variantes predefinidas */
    .skeleton-text {
      height: 1rem;
      width: 100%;
    }

    .skeleton-title {
      height: 2rem;
      width: 60%;
    }

    .skeleton-avatar {
      width: 3rem;
      height: 3rem;
      border-radius: 50%;
    }

    .skeleton-card {
      height: 12rem;
      width: 100%;
    }

    .skeleton-button {
      height: 2.5rem;
      width: 8rem;
    }
  `]
})
export class SkeletonLoaderComponent {
    @Input() type: 'text' | 'title' | 'avatar' | 'card' | 'button' | 'custom' = 'text';
    @Input() width?: string;
    @Input() height?: string;

    getSkeletonClass(): string {
        if (this.type === 'custom') {
            return '';
        }
        return `skeleton-${this.type}`;
    }
}
