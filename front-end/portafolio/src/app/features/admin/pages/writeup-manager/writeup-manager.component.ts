import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { WriteupsService, Writeup } from '../../../writeups/services/writeups.service';
import { NotificationService } from '../../../../core/services/notification.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { IconComponent } from '../../../../shared/icons/icon.component';
import { ApiError } from '../../../../core/services/api.service';

@Component({
    selector: 'app-writeup-manager',
    standalone: true,
    imports: [CommonModule, RouterLink, ConfirmDialogComponent, IconComponent],
    templateUrl: './writeup-manager.component.html',
    styleUrls: ['./writeup-manager.component.scss']
})
export class WriteupManagerComponent implements OnInit {
    writeups: Writeup[] = [];
    loading = false;
    errorMessage = '';
    showDeleteModal = false;
    writeupToDelete: Writeup | null = null;

    private readonly writeupsService = inject(WriteupsService);
    private readonly notificationService = inject(NotificationService);
    private readonly destroyRef = inject(DestroyRef);

    ngOnInit(): void {
        this.loadWriteups();
    }

    loadWriteups(): void {
        this.loading = true;
        this.errorMessage = '';
        this.writeupsService.getAdminAll({ page: 1, size: 100 }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
            next: (response) => {
                this.writeups = response.items || [];
                this.loading = false;
            },
            error: (err: unknown) => {
                this.writeups = [];
                this.loading = false;
                if (err instanceof ApiError && err.status === 404) {
                    this.errorMessage = 'No hay writeups para mostrar. El listado de administración aún no está disponible.';
                    return;
                }
                this.errorMessage = err instanceof Error && err.message
                    ? err.message
                    : 'No se pudieron cargar los writeups.';
            }
        });
    }

    publishWriteup(id: string): void {
        this.writeupsService.publishWriteup(id).subscribe({
            next: () => {
                this.notificationService.success('Writeup publicado exitosamente');
                this.loadWriteups();
            }
        });
    }

    confirmDelete(writeup: Writeup): void {
        this.writeupToDelete = writeup;
        this.showDeleteModal = true;
    }

    cancelDelete(): void {
        this.showDeleteModal = false;
        this.writeupToDelete = null;
    }

    executeDelete(): void {
        if (!this.writeupToDelete) return;
        const id = this.writeupToDelete.id;
        this.writeupsService.deleteWriteup(id).subscribe({
            next: () => {
                this.notificationService.success('Writeup eliminado exitosamente');
                this.cancelDelete();
                this.loadWriteups();
            }
        });
    }

    tools(writeup: Writeup): string[] {
        return writeup.tools_used || [];
    }
}
