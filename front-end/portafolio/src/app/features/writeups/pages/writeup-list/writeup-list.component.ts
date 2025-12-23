import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { WriteupsService, Writeup } from '../../services/writeups.service';

@Component({
    selector: 'app-writeup-list',
    standalone: true,
    imports: [CommonModule, RouterLink],
    templateUrl: './writeup-list.component.html',
    styleUrls: ['./writeup-list.component.scss']
})
export class WriteupListComponent implements OnInit {
    writeups: Writeup[] = [];
    loading = false;
    error = '';

    currentPage = 1;
    pageSize = 12;
    totalPages = 1;
    total = 0;

    searchQuery = '';

    constructor(private writeupsService: WriteupsService) { }

    ngOnInit(): void {
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
                this.writeups = response.items;
                this.total = response.total;
                this.totalPages = response.pages;
                this.loading = false;
            },
            error: (err) => {
                this.error = 'Error al cargar los writeups';
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
