import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

import { Project } from '@core/models';
import { ProjectCardComponent } from '@shared/components';

@Component({
  selector: 'app-projects-section',
  standalone: true,
  imports: [CommonModule, ProjectCardComponent],
  templateUrl: './projects-section.component.html',
  styleUrls: ['./projects-section.component.scss']
})
export class ProjectsSectionComponent {
  @Input() projects: Project[] = [];
  @Input() loading = false;
}
