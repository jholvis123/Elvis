import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ProjectsService } from '../../../projects/services/projects.service';
import { WriteupsService } from '../../../writeups/services/writeups.service';
import { CtfService } from '../../../../core/services/ctf.service';

interface DashboardStats {
    totalProjects: number;
    featuredProjects: number;
    totalWriteups: number;
    publishedWriteups: number;
    totalCTFs: number;
    publishedCTFs: number;
    totalViews: number;
}

@Component({
    selector: 'app-dashboard',
    standalone: true,
    imports: [CommonModule, RouterLink],
    templateUrl: './dashboard.component.html',
    styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
    stats: DashboardStats = {
        totalProjects: 0,
        featuredProjects: 0,
        totalWriteups: 0,
        publishedWriteups: 0,
        totalCTFs: 0,
        publishedCTFs: 0,
        totalViews: 0
    };

    loading = true;
    recentProjects: any[] = [];
    recentWriteups: any[] = [];
    recentCTFs: any[] = [];

    constructor(
        private projectsService: ProjectsService,
        private writeupsService: WriteupsService,
        private ctfService: CtfService
    ) { }

    ngOnInit(): void {
        this.loadStats();
        this.loadRecentContent();
    }

    loadStats(): void {
        // Cargar estadísticas de proyectos
        this.projectsService.getProjects({ page: 1, size: 1 }).subscribe({
            next: (response) => {
                this.stats.totalProjects = response.total;
            }
        });

        this.projectsService.getFeaturedProjects(100).subscribe({
            next: (projects) => {
                this.stats.featuredProjects = projects.length;
            }
        });

        // Cargar estadísticas de writeups
        this.writeupsService.getWriteups({ page: 1, size: 1 }).subscribe({
            next: (response) => {
                this.stats.totalWriteups = response.total;
            }
        });

        this.writeupsService.getPopularWriteups(100).subscribe({
            next: (writeups) => {
                this.stats.totalViews = writeups.reduce((sum, w) => sum + (w.views || 0), 0);
            }
        });

        // Cargar estadísticas de CTFs
        this.ctfService.getAllChallengesAdmin().subscribe({
            next: (response) => {
                this.stats.totalCTFs = response.total;
                this.stats.publishedCTFs = response.items.filter(c => c.status === 'published').length;
            },
            error: () => {
                // Si falla (no admin), usar endpoint público
                this.ctfService.getStatsFromApi().subscribe({
                    next: (stats) => {
                        this.stats.totalCTFs = stats.totalChallenges;
                    }
                });
            }
        });

        this.loading = false;
    }

    loadRecentContent(): void {
        // Cargar proyectos recientes
        this.projectsService.getProjects({ page: 1, size: 5 }).subscribe({
            next: (response) => {
                this.recentProjects = response.items;
            }
        });

        // Cargar writeups recientes
        this.writeupsService.getWriteups({ page: 1, size: 5 }).subscribe({
            next: (response) => {
                this.recentWriteups = response.items;
            }
        });

        // Cargar CTFs recientes
        this.ctfService.getAllChallengesAdmin().subscribe({
            next: (response) => {
                this.recentCTFs = response.items.slice(0, 5);
            }
        });
    }
}
