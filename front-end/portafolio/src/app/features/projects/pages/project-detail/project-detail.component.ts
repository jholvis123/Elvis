import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ProjectsService, Project } from '../../services/projects.service';
import { AuthService } from '../../../../core/services/auth.service';

@Component({
    selector: 'app-project-detail',
    standalone: true,
    imports: [CommonModule, RouterLink],
    templateUrl: './project-detail.component.html',
    styleUrls: ['./project-detail.component.scss']
})
export class ProjectDetailComponent implements OnInit {
    project: Project | null = null;
    loading = false;
    error = '';

    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private projectsService: ProjectsService,
        public authService: AuthService
    ) { }

    ngOnInit(): void {
        const id = this.route.snapshot.paramMap.get('id');
        if (id) {
            this.loadProject(id);
        }
    }

    loadProject(id: string): void {
        this.loading = true;
        this.error = '';

        this.projectsService.getProjectById(id).subscribe({
            next: (project) => {
                this.project = project;
                this.loading = false;
            },
            error: (err) => {
                this.error = 'Proyecto no encontrado';
                this.loading = false;
            }
        });
    }

    deleteProject(): void {
        if (!this.project || !confirm('¿Estás seguro de eliminar este proyecto?')) {
            return;
        }

        this.projectsService.deleteProject(this.project.id).subscribe({
            next: () => {
                this.router.navigate(['/projects']);
            },
            error: (err) => {
                alert('Error al eliminar el proyecto');
            }
        });
    }
}
