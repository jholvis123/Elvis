import { Component, OnInit, OnDestroy, signal, HostListener, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { WriteupsService, Writeup, TOCItem } from '../../services/writeups.service';
import { AuthService } from '../../../../core/services/auth.service';
import { NotificationService } from '../../../../core/services/notification.service';
import { MarkdownViewerComponent } from '../../../../shared/components/markdown-viewer/markdown-viewer.component';
import { TableOfContentsComponent, TOCItem as TOCComponentItem, TOCStats } from '../../../../shared/components/table-of-contents/table-of-contents.component';

@Component({
    selector: 'app-writeup-detail',
    standalone: true,
    imports: [CommonModule, RouterLink, MarkdownViewerComponent, TableOfContentsComponent],
    templateUrl: './writeup-detail.component.html',
    styleUrls: ['./writeup-detail.component.scss']
})
export class WriteupDetailComponent implements OnInit, OnDestroy {
    writeup: Writeup | null = null;
    loading = false;
    error = '';
    
    // TOC State
    tocOpen = signal(true);
    activeHeadingId = signal<string>('');
    readingProgress = signal<number>(0);

    // Computed TOC items converted to the component format
    tocItems = computed<TOCComponentItem[]>(() => {
        if (!this.writeup?.toc) return [];
        return this.writeup.toc.map(item => ({
            id: item.id,
            text: item.text,
            level: item.level
        }));
    });

    // Computed TOC stats
    tocStats = computed<TOCStats | undefined>(() => {
        if (!this.writeup) return undefined;
        return {
            wordCount: this.writeup.word_count || 0,
            readTime: this.writeup.read_time || 0,
            languagesUsed: this.writeup.languages_used || []
        };
    });

    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private writeupsService: WriteupsService,
        public authService: AuthService,
        private notificationService: NotificationService
    ) { }

    ngOnInit(): void {
        const id = this.route.snapshot.paramMap.get('id');
        if (id) {
            this.loadWriteup(id);
        }
    }

    ngOnDestroy(): void {
        // Cleanup if needed
    }

    @HostListener('window:scroll')
    onScroll(): void {
        this.updateReadingProgress();
        this.updateActiveHeading();
    }

    private updateReadingProgress(): void {
        const scrollTop = window.scrollY;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
        this.readingProgress.set(Math.min(100, progress));
    }

    private updateActiveHeading(): void {
        const items = this.tocItems();
        if (items.length === 0) return;

        const scrollPosition = window.scrollY + 120;

        for (let i = items.length - 1; i >= 0; i--) {
            const element = document.getElementById(items[i].id);
            if (element && element.offsetTop <= scrollPosition) {
                this.activeHeadingId.set(items[i].id);
                return;
            }
        }

        this.activeHeadingId.set(items[0].id);
    }

    onTocItemClick(item: TOCComponentItem): void {
        const element = document.getElementById(item.id);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
            this.activeHeadingId.set(item.id);
        }
    }

    onTocStateChange(isOpen: boolean): void {
        this.tocOpen.set(isOpen);
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
                this.notificationService.success('Writeup eliminado');
                this.router.navigate(['/writeups']);
            },
            error: (err) => {
                this.notificationService.error('Error al eliminar el writeup');
            }
        });
    }

    publishWriteup(): void {
        if (!this.writeup) return;

        this.writeupsService.publishWriteup(this.writeup.id).subscribe({
            next: (writeup) => {
                this.writeup = writeup;
                this.notificationService.success('Writeup publicado exitosamente');
            },
            error: (err) => {
                this.notificationService.error('Error al publicar el writeup');
            }
        });
    }
}
