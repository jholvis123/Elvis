import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { WriteupsService, Writeup } from '../../services/writeups.service';
import { SkeletonLoaderComponent } from '@shared/components/skeleton-loader/skeleton-loader.component';
import { ErrorMessageComponent } from '@shared/components/error-message/error-message.component';
import { IconComponent } from '@shared/icons/icon.component';
import { ApiAvailabilityService } from '@core/services/api-availability.service';

@Component({
    selector: 'app-writeup-list',
    standalone: true,
    imports: [
        CommonModule,
        RouterLink,
        SkeletonLoaderComponent,
        ErrorMessageComponent,
        IconComponent
    ],
    templateUrl: './writeup-list.component.html',
    styleUrls: ['./writeup-list.component.scss']
})
export class WriteupListComponent implements OnInit {
    private readonly writeupsService = inject(WriteupsService);
    private readonly apiAvailability = inject(ApiAvailabilityService);

    writeups: Writeup[] = [];
    loading = false;
    error = '';
    apiUnavailable = false;

    currentPage = 1;
    pageSize = 12;
    totalPages = 1;
    total = 0;

    searchQuery = '';

    ngOnInit(): void {
        this.apiUnavailable = !this.apiAvailability.isApiAvailable();
        if (!this.apiAvailability.isApiConfigured()) {
            this.apiUnavailable = true;
            this.writeups = [];
            this.error = 'API no configurada. Los writeups no están disponibles.';
            return;
        }
        this.loadWriteups();
    }

    loadWriteups(): void {
        this.loading = true;
        this.error = '';

        const params = {
            page: this.currentPage,
            size: this.pageSize,
            ...(this.searchQuery && { search: this.searchQuery })
        };

        this.writeupsService.getWriteups(params).subscribe({
            next: (response) => {
                this.writeups = response.items ?? [];
                this.total = response.total;
                this.totalPages = response.pages;
                this.loading = false;
                this.apiAvailability.markNetworkOk();
                this.apiUnavailable = false;
            },
            error: (err) => {
                this.apiAvailability.noteRequestFailure(err);
                this.apiUnavailable = !this.apiAvailability.isApiAvailable();
                this.writeups = [];
                this.error = this.apiUnavailable
                    ? 'API no disponible. No se pueden cargar los writeups.'
                    : 'No se pudieron cargar los writeups. Intenta de nuevo más tarde.';
                this.loading = false;
            }
        });
    }

    search(query: string): void {
        this.searchQuery = query;
        this.currentPage = 1;
        this.loadWriteups();
    }

    goToPage(page: number): void {
        if (page >= 1 && page <= this.totalPages) {
            this.currentPage = page;
            this.loadWriteups();
        }
    }

    get pages(): number[] {
        return Array.from({ length: this.totalPages }, (_, i) => i + 1);
    }
}
