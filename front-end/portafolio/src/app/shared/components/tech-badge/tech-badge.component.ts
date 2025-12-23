import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-tech-badge',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './tech-badge.component.html',
  styleUrls: ['./tech-badge.component.scss']
})
export class TechBadgeComponent {
  @Input({ required: true }) name!: string;
  @Input() variant: 'default' | 'primary' | 'outline' = 'default';
  @Input() size: 'sm' | 'md' = 'md';
}
