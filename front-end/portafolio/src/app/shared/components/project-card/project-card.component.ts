import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ProjectSummary } from '@core/models';

@Component({
  selector: 'app-project-card',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './project-card.component.html',
  styleUrls: ['./project-card.component.scss']
})
export class ProjectCardComponent {
  @Input({ required: true }) project!: ProjectSummary;
  @Input() index = 0;

  get year(): number {
    if (!this.project?.created_at) {
      return new Date().getFullYear();
    }
    const year = new Date(this.project.created_at).getFullYear();
    return Number.isFinite(year) ? year : new Date().getFullYear();
  }

  get tags(): string[] {
    return (this.project?.technologies ?? []).slice(0, 3);
  }

  get categoryLabel(): string {
    return this.project?.featured ? 'Destacado' : 'Proyecto';
  }
}
