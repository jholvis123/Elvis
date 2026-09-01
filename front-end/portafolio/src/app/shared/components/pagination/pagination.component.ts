import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-pagination',
    standalone: true,
    imports: [CommonModule],
    template: `
    <nav class="flex flex-wrap justify-center gap-2" aria-label="Paginación">
      <button
        type="button"
        (click)="onPageChange(currentPage - 1)"
        [disabled]="currentPage === 1"
        class="px-4 py-2 min-h-[44px] bg-gray-700 text-textPrimary rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600 transition"
      >
        Anterior
      </button>
      
      <button
        type="button"
        *ngFor="let page of visiblePages"
        (click)="onPageChange(page)"
        [class.bg-primary]="page === currentPage"
        [class.text-black]="page === currentPage"
        [class.bg-gray-700]="page !== currentPage"
        [attr.aria-current]="page === currentPage ? 'page' : null"
        class="px-4 py-2 min-h-[44px] min-w-[44px] text-textPrimary rounded-lg hover:bg-primaryHover transition"
      >
        {{ page }}
      </button>

      <button
        type="button"
        (click)="onPageChange(currentPage + 1)"
        [disabled]="currentPage === totalPages"
        class="px-4 py-2 min-h-[44px] bg-gray-700 text-textPrimary rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600 transition"
      >
        Siguiente
      </button>
    </nav>
  `,
    styles: []
})
export class PaginationComponent {
    @Input() currentPage = 1;
    @Input() totalPages = 1;
    @Input() onPageChange: (page: number) => void = () => { };

    get visiblePages(): number[] {
        const maxVisible = 5;
        const pages: number[] = [];

        let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
        let end = Math.min(this.totalPages, start + maxVisible - 1);

        if (end - start < maxVisible - 1) {
            start = Math.max(1, end - maxVisible + 1);
        }

        for (let i = start; i <= end; i++) {
            pages.push(i);
        }

        return pages;
    }
}
