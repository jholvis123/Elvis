import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { WriteupsService, Writeup } from '../../../writeups/services/writeups.service';
import { NotificationService } from '../../../../core/services/notification.service';

@Component({
    selector: 'app-writeup-manager',
    standalone: true,
    imports: [CommonModule, RouterLink],
    templateUrl: './writeup-manager.component.html',
    styleUrls: ['./writeup-manager.component.scss']
})
export class WriteupManagerComponent implements OnInit {
    writeups: Writeup[] = [];
    loading = false;

    constructor(
        private writeupsService: WriteupsService,
        private notificationService: NotificationService
    ) { }

    ngOnInit(): void {
        this.loadWriteups();
    }

    loadWriteups(): void {
        this.loading = true;
        this.writeupsService.getWriteups({ page: 1, size: 100 }).subscribe({
            next: (response) => {
                this.writeups = response.items;
                this.loading = false;
            },
            error: () => {
                this.notificationService.error('Error al cargar writeups');
                this.loading = false;
            }
        });
    }

    publishWriteup(id: string): void {
        this.writeupsService.publishWriteup(id).subscribe({
            next: () => {
                this.notificationService.success('Writeup publicado exitosamente');
                this.loadWriteups();
            },
            error: () => {
                this.notificationService.error('Error al publicar el writeup');
            }
        });
    }

    deleteWriteup(id: string): void {
        if (!confirm('¿Estás seguro de eliminar este writeup?')) return;

        this.writeupsService.deleteWriteup(id).subscribe({
            next: () => {
                this.notificationService.success('Writeup eliminado exitosamente');
                this.loadWriteups();
            },
            error: () => {
                this.notificationService.error('Error al eliminar el writeup');
            }
        });
    }
}
