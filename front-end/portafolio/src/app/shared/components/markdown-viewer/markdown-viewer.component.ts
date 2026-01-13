import {
    Component,
    Input,
    OnChanges,
    OnDestroy,
    SimpleChanges,
    ViewChild,
    ElementRef,
    HostListener,
    signal,
    inject,
    ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject, takeUntil, catchError, of } from 'rxjs';
import { WriteupsService, MarkdownRenderResponse } from '../../../features/writeups/services/writeups.service';

@Component({
    selector: 'app-markdown-viewer',
    standalone: true,
    imports: [CommonModule],
    templateUrl: './markdown-viewer.component.html',
    styleUrls: ['./markdown-viewer.component.scss'],
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MarkdownViewerComponent implements OnChanges, OnDestroy {
    private writeupsService = inject(WriteupsService);
    private destroy$ = new Subject<void>();
    
    @ViewChild('contentArea') contentArea!: ElementRef<HTMLElement>;
    
    @Input() content = '';
    @Input() html?: string;
    
    // Signals
    renderedHtml = signal<string>('');
    isLoading = signal<boolean>(false);
    error = signal<string>('');
    lightboxImage = signal<string>('');
    
    ngOnChanges(changes: SimpleChanges): void {
        if (changes['html'] && this.html) {
            // HTML pre-renderizado desde el backend
            this.renderedHtml.set(this.html);
        } else if (changes['content'] && this.content && !this.html) {
            // Renderizar Markdown
            this.renderContent();
        }
    }
    
    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }
    
    private renderContent(): void {
        if (!this.content) {
            this.renderedHtml.set('');
            return;
        }
        
        this.isLoading.set(true);
        this.error.set('');
        
        this.writeupsService.renderMarkdown(this.content).pipe(
            takeUntil(this.destroy$),
            catchError(err => {
                this.error.set('Error al renderizar el contenido');
                return of(null);
            })
        ).subscribe(result => {
            this.isLoading.set(false);
            if (result) {
                this.renderedHtml.set(result.html);
            }
        });
    }
    
    handleContentClick(event: MouseEvent): void {
        const target = event.target as HTMLElement;
        
        // Handle image lightbox
        if (target.tagName === 'IMG' && target.classList.contains('lightbox-trigger')) {
            this.lightboxImage.set((target as HTMLImageElement).src);
        }
        
        // Handle code copy
        if (target.classList.contains('code-copy-btn')) {
            const codeBlock = target.closest('.code-block');
            const code = codeBlock?.querySelector('code')?.textContent || '';
            this.copyToClipboard(code);
        }
    }
    
    private async copyToClipboard(text: string): Promise<void> {
        try {
            await navigator.clipboard.writeText(text);
            // Could show a toast notification here
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    }
    
    closeLightbox(): void {
        this.lightboxImage.set('');
    }
    
    @HostListener('document:keydown.escape')
    onEscapeKey(): void {
        if (this.lightboxImage()) {
            this.closeLightbox();
        }
    }
}
