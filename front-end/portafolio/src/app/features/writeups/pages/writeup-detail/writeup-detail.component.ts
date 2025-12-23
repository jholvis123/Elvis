import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { MarkdownComponent } from 'ngx-markdown';
import { WriteupsService, Writeup } from '../../services/writeups.service';
import { AuthService } from '../../../../core/services/auth.service';

@Component({
    selector: 'app-writeup-detail',
    standalone: true,
    imports: [CommonModule, RouterLink, MarkdownComponent],
    templateUrl: './writeup-detail.component.html',
    styleUrls: ['./writeup-detail.component.scss']
})
export class WriteupDetailComponent implements OnInit {
    writeup: Writeup | null = null;
    loading = false;
    error = '';

    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private writeupsService: WriteupsService,
        public authService: AuthService
    ) { }

    ngOnInit(): void {
        const id = this.route.snapshot.paramMap.get('id');
        if (id) {
            this.loadWriteup(id);
        }
    }

    loadWriteup(id: string): void {
        this.loading = true;
        this.error = '';

        this.writeupsService.getWriteupById(id).subscribe({
            next: (writeup) => {
                this.writeup = writeup;
                this.loading = false;
            },
            error: (err) => {
                this.error = 'Writeup no encontrado';
                this.loading = false;
            }
        });
    }

    deleteWriteup(): void {
        if (!this.writeup || !confirm('¿Estás seguro de eliminar este writeup?')) {
            return;
        }

        this.writeupsService.deleteWriteup(this.writeup.id).subscribe({
            next: () => {
                this.router.navigate(['/writeups']);
            },
            error: (err) => {
                alert('Error al eliminar el writeup');
            }
        });
    }

    publishWriteup(): void {
        if (!this.writeup) return;

        this.writeupsService.publishWriteup(this.writeup.id).subscribe({
            next: (writeup) => {
                this.writeup = writeup;
                alert('Writeup publicado exitosamente');
            },
            error: (err) => {
                alert('Error al publicar el writeup');
            }
        });
    }
}
