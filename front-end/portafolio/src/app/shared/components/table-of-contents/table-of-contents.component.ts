import {
    Component,
    Input,
    Output,
    EventEmitter,
    OnInit,
    OnDestroy,
    HostListener,
    signal,
    computed,
    ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';

export interface TOCItem {
    id: string;
    text: string;
    level: number;
}

export interface TOCStats {
    wordCount: number;
    readTime: number;
    languagesUsed: string[];
}

const TOC_STORAGE_KEY = 'writeup-toc-open';

@Component({
    selector: 'app-table-of-contents',
    standalone: true,
    imports: [CommonModule],
    changeDetection: ChangeDetectionStrategy.OnPush,
    template: `
        <!-- Desktop TOC Sidebar -->
        <aside 
            class="toc-sidebar"
            [class.collapsed]="!isOpen()"
            [class.mobile-visible]="mobileOpen()"
        >
            <!-- Header -->
            <div class="toc-header">
                <div class="toc-title">
                    <span class="toc-icon">📑</span>
                    <span class="toc-label">Contenido</span>
                </div>
                <button 
                    class="toc-toggle desktop-toggle"
                    (click)="toggleDesktop()"
                    [attr.aria-label]="isOpen() ? 'Cerrar índice' : 'Abrir índice'"
                >
                    <span class="toggle-icon">{{ isOpen() ? '◀' : '▶' }}</span>
                </button>
                <button 
                    class="toc-toggle mobile-close"
                    (click)="closeMobile()"
                    aria-label="Cerrar índice"
                >
                    ✕
                </button>
            </div>
            
            <!-- Navigation -->
            <nav class="toc-nav" *ngIf="isOpen() || mobileOpen()">
                <div class="toc-items">
                    <a 
                        *ngFor="let item of items; let i = index"
                        class="toc-item"
                        [class.active]="activeId() === item.id"
                        [class.level-1]="item.level === 1"
                        [class.level-2]="item.level === 2"
                        [class.level-3]="item.level === 3"
                        [class.level-4]="item.level === 4"
                        [class.level-5]="item.level === 5"
                        [class.level-6]="item.level === 6"
                        [href]="'#' + item.id"
                        (click)="onItemClick($event, item)"
                    >
                        <span class="item-indicator"></span>
                        <span class="item-text">{{ item.text }}</span>
                    </a>
                </div>
                
                <!-- Stats Section -->
                <div class="toc-stats" *ngIf="stats">
                    <div class="stat-item">
                        <span class="stat-icon">📖</span>
                        <span class="stat-value">{{ stats.readTime }} min lectura</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-icon">✍️</span>
                        <span class="stat-value">{{ stats.wordCount | number }} palabras</span>
                    </div>
                    <div class="stat-item" *ngIf="stats.languagesUsed.length > 0">
                        <span class="stat-icon">💻</span>
                        <span class="stat-value">{{ stats.languagesUsed.length }} lenguajes</span>
                    </div>
                </div>
            </nav>
            
            <!-- Collapsed indicator -->
            <div class="collapsed-indicator" *ngIf="!isOpen() && !mobileOpen()">
                <span class="indicator-icon">📑</span>
                <span class="indicator-count">{{ items.length }}</span>
            </div>
        </aside>
        
        <!-- Mobile Overlay -->
        <div 
            class="toc-overlay"
            *ngIf="mobileOpen()"
            (click)="closeMobile()"
        ></div>
        
        <!-- Mobile FAB Toggle -->
        <button 
            class="toc-fab"
            (click)="openMobile()"
            *ngIf="items.length > 0"
            aria-label="Abrir índice de contenido"
        >
            <span class="fab-icon">📑</span>
            <span class="fab-badge" *ngIf="items.length > 0">{{ items.length }}</span>
        </button>
    `,
    styles: [`
        :host {
            display: contents;
        }
        
        /* ==================== DESKTOP TOC ==================== */
        .toc-sidebar {
            position: fixed;
            top: 80px;
            left: 0;
            width: 280px;
            height: calc(100vh - 100px);
            background: var(--toc-bg, #161616);
            border-right: 1px solid var(--border-color, #2d2d2d);
            display: flex;
            flex-direction: column;
            z-index: 100;
            transition: width 0.3s ease, transform 0.3s ease;
            
            &.collapsed {
                width: 48px;
                
                .toc-header {
                    padding: 12px 8px;
                    justify-content: center;
                    
                    .toc-title {
                        display: none;
                    }
                }
                
                .toc-nav {
                    display: none;
                }
            }
            
            @media (max-width: 1200px) {
                transform: translateX(-100%);
                width: 300px;
                top: 0;
                height: 100vh;
                border-right: none;
                box-shadow: 4px 0 20px rgba(0, 0, 0, 0.5);
                
                &.mobile-visible {
                    transform: translateX(0);
                }
                
                &.collapsed {
                    width: 300px;
                }
            }
        }
        
        /* Header */
        .toc-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px;
            border-bottom: 1px solid var(--border-color, #2d2d2d);
            background: var(--toc-header-bg, #1a1a1a);
        }
        
        .toc-title {
            display: flex;
            align-items: center;
            gap: 8px;
            
            .toc-icon {
                font-size: 16px;
            }
            
            .toc-label {
                font-size: 14px;
                font-weight: 600;
                color: var(--text-color, #e0e0e0);
            }
        }
        
        .toc-toggle {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            border: none;
            background: var(--toggle-bg, #2d2d2d);
            border-radius: 6px;
            cursor: pointer;
            color: var(--text-muted, #888);
            transition: all 0.2s ease;
            
            &:hover {
                background: var(--toggle-hover-bg, #3d3d3d);
                color: var(--text-color, #e0e0e0);
            }
            
            .toggle-icon {
                font-size: 10px;
            }
        }
        
        .desktop-toggle {
            @media (max-width: 1200px) {
                display: none;
            }
        }
        
        .mobile-close {
            display: none;
            font-size: 18px;
            
            @media (max-width: 1200px) {
                display: flex;
            }
        }
        
        /* Navigation */
        .toc-nav {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .toc-items {
            flex: 1;
            overflow-y: auto;
            padding: 12px 8px;
            
            /* Custom scrollbar */
            &::-webkit-scrollbar {
                width: 6px;
            }
            
            &::-webkit-scrollbar-track {
                background: transparent;
            }
            
            &::-webkit-scrollbar-thumb {
                background: var(--scrollbar-thumb, #3d3d3d);
                border-radius: 3px;
                
                &:hover {
                    background: var(--scrollbar-thumb-hover, #4d4d4d);
                }
            }
        }
        
        .toc-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            margin-bottom: 2px;
            color: var(--text-muted, #888);
            text-decoration: none;
            border-radius: 6px;
            font-size: 13px;
            line-height: 1.4;
            transition: all 0.15s ease;
            position: relative;
            
            &:hover {
                background: var(--item-hover-bg, rgba(255, 255, 255, 0.05));
                color: var(--text-color, #e0e0e0);
            }
            
            &.active {
                background: var(--item-active-bg, rgba(88, 166, 255, 0.15));
                color: var(--link-color, #58a6ff);
                
                .item-indicator {
                    background: var(--link-color, #58a6ff);
                    width: 3px;
                }
            }
            
            .item-indicator {
                position: absolute;
                left: 0;
                top: 4px;
                bottom: 4px;
                width: 0;
                background: transparent;
                border-radius: 2px;
                transition: all 0.2s ease;
            }
            
            .item-text {
                flex: 1;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            
            /* Level indentation */
            &.level-1 {
                font-weight: 600;
                font-size: 14px;
                padding-left: 12px;
            }
            
            &.level-2 {
                padding-left: 20px;
            }
            
            &.level-3 {
                padding-left: 32px;
                font-size: 12px;
            }
            
            &.level-4 {
                padding-left: 44px;
                font-size: 12px;
                color: var(--text-dimmed, #666);
            }
            
            &.level-5, &.level-6 {
                padding-left: 56px;
                font-size: 11px;
                color: var(--text-dimmed, #666);
            }
        }
        
        /* Stats */
        .toc-stats {
            padding: 16px;
            border-top: 1px solid var(--border-color, #2d2d2d);
            background: var(--toc-stats-bg, #1a1a1a);
        }
        
        .stat-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 0;
            font-size: 12px;
            color: var(--text-muted, #888);
            
            .stat-icon {
                font-size: 14px;
                width: 20px;
                text-align: center;
            }
        }
        
        /* Collapsed state */
        .collapsed-indicator {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 16px 8px;
            cursor: pointer;
            
            .indicator-icon {
                font-size: 20px;
            }
            
            .indicator-count {
                font-size: 11px;
                color: var(--text-muted, #888);
                background: var(--badge-bg, #2d2d2d);
                padding: 2px 6px;
                border-radius: 10px;
            }
            
            @media (max-width: 1200px) {
                display: none;
            }
        }
        
        /* ==================== MOBILE ==================== */
        .toc-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.6);
            z-index: 99;
            backdrop-filter: blur(2px);
            
            @media (max-width: 1200px) {
                display: block;
            }
        }
        
        .toc-fab {
            display: none;
            position: fixed;
            bottom: 24px;
            left: 24px;
            width: 56px;
            height: 56px;
            border-radius: 16px;
            border: none;
            background: var(--fab-bg, linear-gradient(135deg, #007acc 0%, #005a9e 100%));
            color: white;
            cursor: pointer;
            box-shadow: 0 4px 16px rgba(0, 122, 204, 0.4);
            z-index: 98;
            transition: all 0.2s ease;
            
            &:hover {
                transform: scale(1.05);
                box-shadow: 0 6px 20px rgba(0, 122, 204, 0.5);
            }
            
            &:active {
                transform: scale(0.95);
            }
            
            .fab-icon {
                font-size: 24px;
            }
            
            .fab-badge {
                position: absolute;
                top: -4px;
                right: -4px;
                min-width: 20px;
                height: 20px;
                padding: 0 6px;
                background: var(--badge-color, #ef4444);
                border-radius: 10px;
                font-size: 11px;
                font-weight: 600;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            @media (max-width: 1200px) {
                display: flex;
                align-items: center;
                justify-content: center;
            }
        }
    `]
})
export class TableOfContentsComponent implements OnInit, OnDestroy {
    @Input() items: TOCItem[] = [];
    @Input() stats?: TOCStats;
    @Input() activeId = signal<string>('');
    
    @Output() itemClick = new EventEmitter<TOCItem>();
    @Output() stateChange = new EventEmitter<boolean>();
    
    // State signals
    isOpen = signal<boolean>(true);
    mobileOpen = signal<boolean>(false);
    
    ngOnInit(): void {
        this.loadState();
    }
    
    ngOnDestroy(): void {
        // Cleanup if needed
    }
    
    private loadState(): void {
        try {
            const saved = localStorage.getItem(TOC_STORAGE_KEY);
            if (saved !== null) {
                this.isOpen.set(saved === 'true');
            }
        } catch {
            // localStorage not available
        }
    }
    
    private saveState(): void {
        try {
            localStorage.setItem(TOC_STORAGE_KEY, String(this.isOpen()));
            this.stateChange.emit(this.isOpen());
        } catch {
            // localStorage not available
        }
    }
    
    toggleDesktop(): void {
        this.isOpen.update(v => !v);
        this.saveState();
    }
    
    openMobile(): void {
        this.mobileOpen.set(true);
    }
    
    closeMobile(): void {
        this.mobileOpen.set(false);
    }
    
    onItemClick(event: Event, item: TOCItem): void {
        event.preventDefault();
        
        const element = document.getElementById(item.id);
        if (element) {
            // Smooth scroll with offset for fixed header
            const headerOffset = 100;
            const elementPosition = element.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.scrollY - headerOffset;
            
            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
            
            this.activeId.set(item.id);
            this.itemClick.emit(item);
            
            // Close mobile drawer after click
            this.mobileOpen.set(false);
        }
    }
    
    @HostListener('document:keydown.escape')
    onEscape(): void {
        if (this.mobileOpen()) {
            this.closeMobile();
        }
    }
}
