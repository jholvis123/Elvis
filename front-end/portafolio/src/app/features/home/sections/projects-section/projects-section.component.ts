import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProjectSummary } from '@core/models';
import { ProjectCardComponent } from '@shared/components';
import { IconComponent } from '@shared/icons/icon.component';

@Component({
  selector: 'app-projects-section',
  standalone: true,
  imports: [CommonModule, ProjectCardComponent, IconComponent],
  templateUrl: './projects-section.component.html',
  styleUrls: ['./projects-section.component.scss']
})
export class ProjectsSectionComponent {
  @Input() projects: ProjectSummary[] = [];
  @Input() loading = false;
}
