import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ProjectsService } from '../../../projects/services/projects.service';
import { WriteupsService } from '../../../writeups/services/writeups.service';
import { CtfService } from '../../../../core/services/ctf.service';
import { AdminService, AdminStats } from '../../../../core/services/admin.service';
import { IconComponent } from '@shared/icons/icon.component';
import { ApiError } from '@core/services/api.service';

@Component({
    selector: 'app-dashboard',
    standalone: true,
    imports: [CommonModule, RouterLink, IconComponent],
    templateUrl: './dashboard.component.html',
    styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
    private readonly adminService = inject(AdminService);
    private readonly projectsService = inject(ProjectsService);
    private readonly writeupsService = inject(WriteupsService);
    private readonly ctfService = inject(CtfService);
    private readonly destroyRef = inject(DestroyRef);

    stats: AdminStats = {
        projects: 0,
        writeups_published: 0,
        writeups_draft: 0,
        ctfs: 0,
        contact_pending: 0,
        contact_total: 0
    };

    loading = true;
    errorMessage = '';
    statsDegraded = false;
    recentProjects: { id: string; title: string; short_description?: string }[] = [];
    recentWriteups: { id: string; title: string; views?: number }[] = [];

    get totalWriteups(): number {
        return this.stats.writeups_published + this.stats.writeups_draft;
    }

    ngOnInit(): void {
        this.loadStats();
        this.loadRecentContent();
    }

    loadStats(): void {
        this.loading = true;
        this.errorMessage = '';
        this.statsDegraded = false;
        this.adminService.getStats().pipe(
            takeUntilDestroyed(this.destroyRef)
        ).subscribe({
            next: (stats) => {
                this.stats = stats;
                this.loading = false;
            },
            error: (err: unknown) => {
                this.loading = false;
                if (err instanceof ApiError && err.status === 404) {
                    this.statsDegraded = true;
                    this.degradeStats();
                    return;
                }
                this.errorMessage = err instanceof Error && err.message
                    ? err.message
                    : 'No se pudieron cargar las estadísticas.';
            }
        });
    }

    loadRecentContent(): void {
        this.projectsService.getProjects({ page: 1, size: 5 }).pipe(
            takeUntilDestroyed(this.destroyRef)
        ).subscribe({
            next: (response) => {
                this.recentProjects = response.items;
            }
        });

        this.writeupsService.getAdminAll({ page: 1, size: 5 }).pipe(
            takeUntilDestroyed(this.destroyRef)
        ).subscribe({
            next: (response) => {
                this.recentWriteups = response.items;
            }
        });
    }

    private degradeStats(): void {
        this.projectsService.getProjects({ page: 1, size: 1 }).pipe(
            takeUntilDestroyed(this.destroyRef)
        ).subscribe({
            next: (response) => {
                this.stats.projects = response.total;
            }
        });

        this.writeupsService.getWriteups({ page: 1, size: 1 }).pipe(
            takeUntilDestroyed(this.destroyRef)
        ).subscribe({
            next: (response) => {
                this.stats.writeups_published = response.total;
            }
        });

        this.ctfService.getAllChallengesAdmin().pipe(
            takeUntilDestroyed(this.destroyRef)
        ).subscribe({
            next: (response) => {
                this.stats.ctfs = response.total;
            }
        });
    }
}
