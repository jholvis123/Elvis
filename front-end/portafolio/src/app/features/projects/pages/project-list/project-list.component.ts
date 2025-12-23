import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ProjectsService, Project } from '../../services/projects.service';

@Component({
    selector: 'app-project-list',
    standalone: true,
    imports: [CommonModule, RouterLink],
    templateUrl: './project-list.component.html',
    styleUrls: ['./project-list.component.scss']
})
export class ProjectListComponent implements OnInit {
    projects: Project[] = [];
    loading = false;
    error = '';

    // Paginación
    currentPage = 1;
    pageSize = 9;
    totalPages = 1;
    total = 0;

    // Filtros
    selectedTechnology: string | null = null;
    technologies: { technology: string; count: number }[] = [];

    constructor(private projectsService: ProjectsService) { }

    ngOnInit(): void {
        this.loadProjects();
        this.loadTechnologies();
    }

    loadProjects(): void {
        this.loading = true;
        this.error = '';

        const params = {
            page: this.currentPage,
            size: this.pageSize,
            ...(this.selectedTechnology && { technology: this.selectedTechnology })
        };

        this.projectsService.getProjects(params).subscribe({
            next: (response) => {
                this.projects = response.items;
                this.total = response.total;
                this.totalPages = response.pages;
                this.loading = false;
            },
            error: (err) => {
                this.error = 'Error al cargar los proyectos';
                this.loading = false;
            }
        });
    }

    loadTechnologies(): void {
        this.projectsService.getTechnologies().subscribe({
            next: (techs) => {
                this.technologies = techs;
            },
            error: () => {
                // Silent fail for technologies
            }
        });
    }

    filterByTechnology(tech: string | null): void {
        this.selectedTechnology = tech;
        this.currentPage = 1;
        this.loadProjects();
    }

    goToPage(page: number): void {
        if (page >= 1 && page <= this.totalPages) {
            this.currentPage = page;
            this.loadProjects();
        }
    }

    get pages(): number[] {
        return Array.from({ length: this.totalPages }, (_, i) => i + 1);
    }
}
