import {
    ChangeDetectionStrategy,
    ChangeDetectorRef,
    Component,
    ElementRef,
    HostListener,
    Input,
    OnChanges,
    OnDestroy,
    Renderer2,
    SecurityContext,
    SimpleChanges,
    ViewChild,
    inject,
    signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer } from '@angular/platform-browser';
import { MarkdownService } from 'ngx-markdown';
import { IconComponent } from '@shared/icons/icon.component';
import { Subject, takeUntil, catchError, of } from 'rxjs';
import { WriteupsService } from '../../../features/writeups/services/writeups.service';

@Component({
    selector: 'app-markdown-viewer',
    standalone: true,
    imports: [CommonModule, IconComponent],
    templateUrl: './markdown-viewer.component.html',
    styleUrls: ['./markdown-viewer.component.scss'],
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MarkdownViewerComponent implements OnChanges, OnDestroy {
    private readonly writeupsService = inject(WriteupsService);
    private readonly markdownService = inject(MarkdownService);
    private readonly sanitizer = inject(DomSanitizer);
    private readonly renderer = inject(Renderer2);
    private readonly cdr = inject(ChangeDetectorRef);
    private readonly destroy$ = new Subject<void>();
    private copyResetTimer: ReturnType<typeof setTimeout> | null = null;
    private copyUnlisteners: Array<() => void> = [];
    /** Pending decorate timer; cleared on re-render or component destroy. */
    private decorateTimer: ReturnType<typeof setTimeout> | null = null;

    @ViewChild('contentArea') contentArea?: ElementRef<HTMLElement>;

    @Input() content = '';
    @Input() html?: string;

    /** Always a sanitized HTML string — never SafeHtml / bypass. */
    renderedHtml = signal<string>('');
    isLoading = signal<boolean>(false);
    error = signal<string>('');
    lightboxImage = signal<string>('');
    /** aria-live polite region for copy feedback */
    copyStatus = signal<string>('');

    ngOnChanges(changes: SimpleChanges): void {
        if (changes['html'] && this.html) {
            this.setSanitizedHtml(this.html);
            this.isLoading.set(false);
            this.error.set('');
        } else if (changes['content'] && this.content && !this.html) {
            this.renderContent();
        } else if ((changes['content'] || changes['html']) && !this.content && !this.html) {
            this.cancelPendingDecorate();
            this.clearCopyListeners();
            this.renderedHtml.set('');
        }
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
        this.cancelPendingDecorate();
        this.clearCopyListeners();
        if (this.copyResetTimer) {
            clearTimeout(this.copyResetTimer);
            this.copyResetTimer = null;
        }
    }

    /**
     * Client-side markdown via ngx-markdown (uses DomSanitizer internally),
     * then an explicit SecurityContext.HTML sanitize before [innerHTML].
     * Public CTF pages must not depend on authenticated /writeups/render-markdown.
     */
    private renderContent(): void {
        if (!this.content) {
            this.cancelPendingDecorate();
            this.clearCopyListeners();
            this.renderedHtml.set('');
            return;
        }

        this.isLoading.set(true);
        this.error.set('');

        try {
            const parsed = this.markdownService.parse(this.content);
            this.setSanitizedHtml(parsed);
            this.isLoading.set(false);
            return;
        } catch {
            // fall through to API
        }

        this.writeupsService.renderMarkdown(this.content).pipe(
            takeUntil(this.destroy$),
            catchError(() => {
                this.error.set('Error al renderizar el contenido');
                return of(null);
            })
        ).subscribe(result => {
            this.isLoading.set(false);
            if (result?.html) {
                this.setSanitizedHtml(result.html);
            }
        });
    }

    /**
     * Sanitize HTML for [innerHTML]. Copy buttons are NOT embedded here —
     * Angular strips <button> from bound HTML; we add them with Renderer2 after paint.
     * Listeners/buttons are cleared only on a full re-render (new sanitized HTML).
     */
    private setSanitizedHtml(rawHtml: string): void {
        const cleaned = this.sanitizer.sanitize(SecurityContext.HTML, rawHtml) || '';
        // Full re-render: drop prior listeners (old DOM nodes are about to be replaced)
        // and cancel any decorate scheduled for a previous render.
        this.cancelPendingDecorate();
        this.clearCopyListeners();
        this.renderedHtml.set(cleaned);
        this.cdr.markForCheck();
        this.scheduleDecorateAfterRender();
    }

    /**
     * Decorate exactly once after [innerHTML] updates.
     * Angular 16.2 exposes afterNextRender (dev preview) but it is awkward outside
     * constructor injection context and flaky under TestBed; setTimeout(0) +
     * detectChanges reliably runs after the binding paints.
     */
    private scheduleDecorateAfterRender(): void {
        this.decorateTimer = setTimeout(() => {
            this.decorateTimer = null;
            // Ensure the view has applied the latest sanitized HTML before querying <pre>.
            this.cdr.detectChanges();
            this.decorateCodeBlocksWithCopyButtons();
        }, 0);
    }

    private cancelPendingDecorate(): void {
        if (this.decorateTimer != null) {
            clearTimeout(this.decorateTimer);
            this.decorateTimer = null;
        }
    }

    /**
     * After sanitized HTML is in the DOM, wrap each <pre> and attach an accessible Copy button.
     * Called once per full re-render; [innerHTML] already removed prior buttons.
     * Idempotent: never adds a second button to a block that already has one.
     */
    private decorateCodeBlocksWithCopyButtons(): void {
        const root = this.contentArea?.nativeElement;
        if (!root) {
            return;
        }

        const pres = Array.from(root.querySelectorAll('pre')) as HTMLPreElement[];
        for (const pre of pres) {
            let block = pre.closest('.code-block') as HTMLElement | null;
            if (!block) {
                block = this.renderer.createElement('div');
                this.renderer.addClass(block, 'code-block');
                const parent = pre.parentNode;
                if (!parent) {
                    continue;
                }
                this.renderer.insertBefore(parent, block, pre);

                const header = this.renderer.createElement('div');
                this.renderer.addClass(header, 'code-header');

                const lang = this.renderer.createElement('span');
                this.renderer.addClass(lang, 'code-language');
                const codeEl = pre.querySelector('code');
                const langClass = codeEl
                    ? Array.from(codeEl.classList).find((c) => c.startsWith('language-'))
                    : undefined;
                this.renderer.setProperty(
                    lang,
                    'textContent',
                    langClass ? langClass.replace('language-', '') : 'text'
                );
                this.renderer.appendChild(header, lang);
                this.renderer.appendChild(block, header);
                this.renderer.appendChild(block, pre);
            }

            if (!block || block.querySelector('.code-copy-btn')) {
                continue;
            }

            let header = block.querySelector('.code-header') as HTMLElement | null;
            if (!header) {
                header = this.renderer.createElement('div');
                this.renderer.addClass(header, 'code-header');
                this.renderer.insertBefore(block, header, block.firstChild);
            }

            const btn = this.renderer.createElement('button') as HTMLButtonElement;
            this.renderer.setAttribute(btn, 'type', 'button');
            this.renderer.addClass(btn, 'code-copy-btn');
            this.renderer.setAttribute(btn, 'aria-label', 'Copiar');
            this.renderer.setProperty(btn, 'textContent', 'Copiar');
            this.renderer.appendChild(header, btn);

            const unlisten = this.renderer.listen(btn, 'click', (event: Event) => {
                event.preventDefault();
                event.stopPropagation();
                const text = pre.textContent || '';
                void this.copyToClipboard(text, btn);
            });
            this.copyUnlisteners.push(unlisten);
        }
    }

    private clearCopyListeners(): void {
        for (const un of this.copyUnlisteners) {
            try {
                un();
            } catch {
                // ignore
            }
        }
        this.copyUnlisteners = [];
    }

    handleContentClick(event: MouseEvent): void {
        const target = event.target as HTMLElement | null;
        if (!target) {
            return;
        }
        if (target.tagName === 'IMG' && target.classList.contains('lightbox-trigger')) {
            this.lightboxImage.set((target as HTMLImageElement).src);
        }
    }

    private async copyToClipboard(text: string, btn: HTMLButtonElement): Promise<void> {
        try {
            await navigator.clipboard.writeText(text);
            this.copyStatus.set('Copiado');
            this.renderer.setProperty(btn, 'textContent', 'Copiado');
            this.renderer.setAttribute(btn, 'aria-label', 'Copiado');
            this.cdr.markForCheck();
            if (this.copyResetTimer) {
                clearTimeout(this.copyResetTimer);
            }
            this.copyResetTimer = setTimeout(() => {
                this.renderer.setProperty(btn, 'textContent', 'Copiar');
                this.renderer.setAttribute(btn, 'aria-label', 'Copiar');
                this.copyStatus.set('');
                this.copyResetTimer = null;
                this.cdr.markForCheck();
            }, 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
            this.copyStatus.set('No se pudo copiar');
            this.cdr.markForCheck();
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
