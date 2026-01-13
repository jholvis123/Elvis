import {
    Component,
    EventEmitter,
    Input,
    OnDestroy,
    OnInit,
    Output,
    ViewChild,
    ElementRef,
    HostListener,
    ChangeDetectionStrategy,
    inject,
    signal,
    computed,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, debounceTime, takeUntil, distinctUntilChanged, catchError } from 'rxjs';
import { of } from 'rxjs';
import { WriteupsService, MarkdownRenderResponse, TOCItem } from '../../../features/writeups/services/writeups.service';

export interface EditorToolbarAction {
    id: string;
    icon: string;
    label: string;
    shortcut?: string;
    action: () => void;
}

export interface ImageUploadEvent {
    file: File;
    insertMarkdown: (markdown: string) => void;
}

@Component({
    selector: 'app-markdown-editor',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './markdown-editor.component.html',
    styleUrls: ['./markdown-editor.component.scss'],
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MarkdownEditorComponent implements OnInit, OnDestroy {
    private readonly writeupsService = inject(WriteupsService);
    private readonly destroy$ = new Subject<void>();
    private readonly contentChange$ = new Subject<string>();
    
    @ViewChild('editorTextarea') editorTextarea?: ElementRef<HTMLTextAreaElement>;
    @ViewChild('lineNumbers') lineNumbers?: ElementRef<HTMLDivElement>;
    @ViewChild('previewPanel') previewPanel?: ElementRef<HTMLDivElement>;
    
    @Input() set value(val: string) {
        this.content.set(val || '');
        this.triggerRender();
    }
    @Input() placeholder = 'Escribe tu contenido en Markdown...';
    @Input() autosaveDelay = 2000;
    
    @Output() valueChange = new EventEmitter<string>();
    @Output() save = new EventEmitter<string>();
    @Output() imageUpload = new EventEmitter<ImageUploadEvent>();
    
    // Signals
    content = signal<string>('');
    renderedHtml = signal<string>('');
    viewMode = signal<'split' | 'edit' | 'preview'>('split');
    isFullscreen = signal<boolean>(false);
    isDragging = signal<boolean>(false);
    isRendering = signal<boolean>(false);
    isSaving = signal<boolean>(false);
    hasChanges = signal<boolean>(false);
    cursorLine = signal<number>(1);
    cursorColumn = signal<number>(1);
    wordCount = signal<number>(0);
    readTime = signal<number>(0);
    languagesUsed = signal<string[]>([]);
    toc = signal<TOCItem[]>([]);
    
    lineNumbersArray = computed(() => {
        const lines = this.content().split('\n').length;
        return Array.from({ length: lines }, (_, i) => i + 1);
    });
    
    toolbarActions: EditorToolbarAction[] = [];
    
    ngOnInit(): void {
        this.initToolbarActions();
        this.setupContentDebounce();
        this.triggerRender();
    }
    
    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }
    
    private initToolbarActions(): void {
        this.toolbarActions = [
            { id: 'bold', icon: '𝐁', label: 'Negrita', shortcut: 'Ctrl+B', action: () => this.wrapSelection('**', '**') },
            { id: 'italic', icon: '𝐼', label: 'Cursiva', shortcut: 'Ctrl+I', action: () => this.wrapSelection('*', '*') },
            { id: 'strike', icon: '𝑆̶', label: 'Tachado', action: () => this.wrapSelection('~~', '~~') },
            { id: 'h1', icon: 'H1', label: 'Encabezado 1', action: () => this.insertAtLineStart('# ') },
            { id: 'h2', icon: 'H2', label: 'Encabezado 2', action: () => this.insertAtLineStart('## ') },
            { id: 'h3', icon: 'H3', label: 'Encabezado 3', action: () => this.insertAtLineStart('### ') },
            { id: 'link', icon: '🔗', label: 'Enlace', shortcut: 'Ctrl+K', action: () => this.insertLink() },
            { id: 'image', icon: '🖼️', label: 'Imagen', action: () => this.insertImage() },
            { id: 'code', icon: '<>', label: 'Código inline', action: () => this.wrapSelection('`', '`') },
            { id: 'codeblock', icon: '📝', label: 'Bloque de código', action: () => this.insertCodeBlock() },
            { id: 'quote', icon: '❝', label: 'Cita', action: () => this.insertAtLineStart('> ') },
            { id: 'ul', icon: '•', label: 'Lista', action: () => this.insertAtLineStart('- ') },
            { id: 'ol', icon: '1.', label: 'Lista numerada', action: () => this.insertAtLineStart('1. ') },
            { id: 'check', icon: '☑', label: 'Checkbox', action: () => this.insertAtLineStart('- [ ] ') },
            { id: 'table', icon: '⊞', label: 'Tabla', action: () => this.insertTable() },
            { id: 'hr', icon: '—', label: 'Línea horizontal', action: () => this.insertText('\n---\n') },
            { id: 'info', icon: 'ℹ️', label: 'Callout Info', action: () => this.insertCallout('info') },
            { id: 'warning', icon: '⚠️', label: 'Callout Warning', action: () => this.insertCallout('warning') },
            { id: 'tip', icon: '💡', label: 'Callout Tip', action: () => this.insertCallout('tip') },
        ];
    }
    
    private setupContentDebounce(): void {
        this.contentChange$.pipe(
            takeUntil(this.destroy$),
            debounceTime(this.autosaveDelay),
            distinctUntilChanged()
        ).subscribe(content => {
            this.save.emit(content);
            this.isSaving.set(true);
            setTimeout(() => {
                this.isSaving.set(false);
                this.hasChanges.set(false);
            }, 500);
        });
    }
    
    private triggerRender(): void {
        const content = this.content();
        if (!content) {
            this.renderedHtml.set('');
            this.wordCount.set(0);
            this.readTime.set(0);
            return;
        }
        
        this.isRendering.set(true);
        
        this.writeupsService.renderMarkdown(content).pipe(
            takeUntil(this.destroy$),
            catchError(err => {
                console.error('Error rendering markdown:', err);
                return of({ html: '<p>Error al renderizar</p>', toc: [], word_count: 0, read_time_minutes: 0, has_code_blocks: false, languages_used: [] });
            })
        ).subscribe(result => {
            this.renderedHtml.set(result.html);
            this.toc.set(result.toc);
            this.wordCount.set(result.word_count);
            this.readTime.set(result.read_time_minutes);
            this.languagesUsed.set(result.languages_used);
            this.isRendering.set(false);
        });
    }
    
    onContentChange(event: Event): void {
        const textarea = event.target as HTMLTextAreaElement;
        const newContent = textarea.value;
        this.content.set(newContent);
        this.hasChanges.set(true);
        this.valueChange.emit(newContent);
        this.contentChange$.next(newContent);
        this.updateCursorPosition(textarea);
        
        // Debounced render
        this.triggerRender();
    }
    
    private updateCursorPosition(textarea: HTMLTextAreaElement): void {
        const text = textarea.value.substring(0, textarea.selectionStart);
        const lines = text.split('\n');
        this.cursorLine.set(lines.length);
        this.cursorColumn.set(lines[lines.length - 1].length + 1);
    }
    
    @HostListener('window:keydown', ['$event'])
    onKeyDown(event: KeyboardEvent): void {
        if (event.ctrlKey || event.metaKey) {
            switch (event.key.toLowerCase()) {
                case 'b':
                    event.preventDefault();
                    this.wrapSelection('**', '**');
                    break;
                case 'i':
                    event.preventDefault();
                    this.wrapSelection('*', '*');
                    break;
                case 'k':
                    event.preventDefault();
                    this.insertLink();
                    break;
                case 's':
                    event.preventDefault();
                    this.save.emit(this.content());
                    break;
            }
        }
        
        // Tab handling
        if (event.key === 'Tab') {
            event.preventDefault();
            this.insertText('    ');
        }
        
        // F11 fullscreen
        if (event.key === 'F11') {
            event.preventDefault();
            this.toggleFullscreen();
        }
    }
    
    // Drag & Drop
    onDragOver(event: DragEvent): void {
        event.preventDefault();
        event.stopPropagation();
        this.isDragging.set(true);
    }
    
    onDragLeave(event: DragEvent): void {
        event.preventDefault();
        event.stopPropagation();
        this.isDragging.set(false);
    }
    
    onDrop(event: DragEvent): void {
        event.preventDefault();
        event.stopPropagation();
        this.isDragging.set(false);
        
        const files = event.dataTransfer?.files;
        if (files && files.length > 0) {
            const file = files[0];
            if (file.type.startsWith('image/')) {
                this.uploadAndInsertImage(file);
            }
        }
    }
    
    // Paste handler for images
    onPaste(event: ClipboardEvent): void {
        const items = event.clipboardData?.items;
        if (!items) return;
        
        for (const item of Array.from(items)) {
            if (item.type.startsWith('image/')) {
                event.preventDefault();
                const file = item.getAsFile();
                if (file) {
                    this.uploadAndInsertImage(file);
                }
                break;
            }
        }
    }
    
    private uploadAndInsertImage(file: File): void {
        this.writeupsService.uploadImage(file).pipe(
            takeUntil(this.destroy$),
            catchError(err => {
                console.error('Error uploading image:', err);
                this.insertText(`<!-- Error al subir imagen: ${err.message} -->`);
                return of(null);
            })
        ).subscribe(result => {
            if (result) {
                this.insertText(result.markdown);
            }
        });
    }
    
    // Scroll sync
    syncScroll(event: Event): void {
        if (!this.lineNumbers || this.viewMode() === 'preview') return;
        
        const textarea = event.target as HTMLTextAreaElement;
        this.lineNumbers.nativeElement.scrollTop = textarea.scrollTop;
        
        if (this.previewPanel && this.viewMode() === 'split') {
            const scrollRatio = textarea.scrollTop / (textarea.scrollHeight - textarea.clientHeight);
            const previewEl = this.previewPanel.nativeElement;
            previewEl.scrollTop = scrollRatio * (previewEl.scrollHeight - previewEl.clientHeight);
        }
    }
    
    // View mode
    setViewMode(mode: 'split' | 'edit' | 'preview'): void {
        this.viewMode.set(mode);
    }
    
    toggleFullscreen(): void {
        this.isFullscreen.update(v => !v);
    }
    
    // Text manipulation helpers
    private getTextarea(): HTMLTextAreaElement | null {
        return this.editorTextarea?.nativeElement || null;
    }
    
    private wrapSelection(before: string, after: string): void {
        const textarea = this.getTextarea();
        if (!textarea) return;
        
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const selected = textarea.value.substring(start, end);
        
        const newText = textarea.value.substring(0, start) + before + selected + after + textarea.value.substring(end);
        this.content.set(newText);
        this.valueChange.emit(newText);
        
        // Restore cursor position
        setTimeout(() => {
            textarea.focus();
            textarea.setSelectionRange(start + before.length, end + before.length);
        });
        
        this.hasChanges.set(true);
        this.triggerRender();
    }
    
    private insertText(text: string): void {
        const textarea = this.getTextarea();
        if (!textarea) return;
        
        const start = textarea.selectionStart;
        const newText = textarea.value.substring(0, start) + text + textarea.value.substring(textarea.selectionEnd);
        this.content.set(newText);
        this.valueChange.emit(newText);
        
        setTimeout(() => {
            textarea.focus();
            textarea.setSelectionRange(start + text.length, start + text.length);
        });
        
        this.hasChanges.set(true);
        this.triggerRender();
    }
    
    private insertAtLineStart(prefix: string): void {
        const textarea = this.getTextarea();
        if (!textarea) return;
        
        const start = textarea.selectionStart;
        const lineStart = textarea.value.lastIndexOf('\n', start - 1) + 1;
        
        const newText = textarea.value.substring(0, lineStart) + prefix + textarea.value.substring(lineStart);
        this.content.set(newText);
        this.valueChange.emit(newText);
        
        setTimeout(() => {
            textarea.focus();
            textarea.setSelectionRange(start + prefix.length, start + prefix.length);
        });
        
        this.hasChanges.set(true);
        this.triggerRender();
    }
    
    private insertLink(): void {
        const textarea = this.getTextarea();
        if (!textarea) return;
        
        const selected = textarea.value.substring(textarea.selectionStart, textarea.selectionEnd);
        const linkText = selected || 'texto';
        this.insertText(`[${linkText}](url)`);
    }
    
    private insertImage(): void {
        // Create file input and trigger click
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.onchange = () => {
            const file = input.files?.[0];
            if (file) {
                this.uploadAndInsertImage(file);
            }
        };
        input.click();
    }
    
    private insertCodeBlock(): void {
        const languages = ['python', 'javascript', 'bash', 'sql'];
        const lang = languages[0]; // Default to python
        this.insertText(`\n\`\`\`${lang}\n\n\`\`\`\n`);
    }
    
    private insertTable(): void {
        const table = `
| Columna 1 | Columna 2 | Columna 3 |
|-----------|-----------|-----------|
| Celda 1   | Celda 2   | Celda 3   |
| Celda 4   | Celda 5   | Celda 6   |
`;
        this.insertText(table);
    }
    
    private insertCallout(type: string): void {
        const titles: Record<string, string> = {
            info: 'Información',
            warning: 'Advertencia',
            tip: 'Consejo',
            danger: 'Peligro',
            note: 'Nota'
        };
        const callout = `\n:::${type} ${titles[type] || type.charAt(0).toUpperCase() + type.slice(1)}\nContenido del callout aquí.\n:::\n`;
        this.insertText(callout);
    }
}
