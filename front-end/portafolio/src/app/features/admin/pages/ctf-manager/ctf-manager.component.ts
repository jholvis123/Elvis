import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CtfService, CTFChallengeAdmin } from '../../../../core/services/ctf.service';
import { NotificationService } from '../../../../core/services/notification.service';

@Component({
    selector: 'app-ctf-manager',
    standalone: true,
    imports: [CommonModule, RouterLink, FormsModule],
    templateUrl: './ctf-manager.component.html',
    styleUrls: ['./ctf-manager.component.scss']
})
export class CtfManagerComponent implements OnInit {
    challenges: CTFChallengeAdmin[] = [];
    loading = false;

    // Filters
    searchTerm = '';
    filterStatus = '';
    filterCategory = '';

    // Stats
    totalChallenges = 0;
    publishedCount = 0;
    draftCount = 0;
    activeCount = 0;

    // Delete modal
    showDeleteModal = false;
    ctfToDelete: CTFChallengeAdmin | null = null;
    forceDelete = false;

    private searchTimeout: any;

    constructor(
        private ctfService: CtfService,
        private notificationService: NotificationService
    ) { }

    ngOnInit(): void {
        this.loadChallenges();
    }

    loadChallenges(): void {
        this.loading = true;
        
        const filter: any = {};
        if (this.filterStatus) filter.status = this.filterStatus;
        if (this.filterCategory) filter.category = this.filterCategory;
        if (this.searchTerm) filter.search = this.searchTerm;

        this.ctfService.getAllChallengesAdmin(filter).subscribe({
            next: (response) => {
                this.challenges = response.items;
                this.totalChallenges = response.total;
                this.updateStats();
                this.loading = false;
            },
            error: (err) => {
                console.error('Error loading challenges:', err);
                this.notificationService.error('Error al cargar los CTFs');
                this.loading = false;
            }
        });
    }

    updateStats(): void {
        this.publishedCount = this.challenges.filter(c => c.status === 'published').length;
        this.draftCount = this.challenges.filter(c => c.status === 'draft').length;
        this.activeCount = this.challenges.filter(c => c.isActive).length;
    }

    onSearch(): void {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.loadChallenges();
        }, 300);
    }

    toggleActive(ctf: CTFChallengeAdmin): void {
        const newState = !ctf.isActive;
        this.ctfService.toggleChallengeActive(ctf.id, newState).subscribe({
            next: () => {
                ctf.isActive = newState;
                this.updateStats();
                this.notificationService.success(
                    newState ? 'CTF activado' : 'CTF desactivado'
                );
            },
            error: () => {
                this.notificationService.error('Error al cambiar estado del CTF');
            }
        });
    }

    publishChallenge(ctf: CTFChallengeAdmin): void {
        this.ctfService.publishChallenge(ctf.id).subscribe({
            next: () => {
                ctf.status = 'published';
                this.updateStats();
                this.notificationService.success('CTF publicado exitosamente');
            },
            error: (err) => {
                const message = err.error?.detail || 'Error al publicar el CTF';
                this.notificationService.error(message);
            }
        });
    }

    confirmDelete(ctf: CTFChallengeAdmin): void {
        this.ctfToDelete = ctf;
        this.forceDelete = false;
        this.showDeleteModal = true;
    }

    cancelDelete(): void {
        this.showDeleteModal = false;
        this.ctfToDelete = null;
        this.forceDelete = false;
    }

    executeDelete(): void {
        if (!this.ctfToDelete) return;

        this.ctfService.deleteChallenge(this.ctfToDelete.id, this.forceDelete).subscribe({
            next: () => {
                this.notificationService.success('CTF eliminado exitosamente');
                this.showDeleteModal = false;
                this.ctfToDelete = null;
                this.loadChallenges();
            },
            error: (err) => {
                const message = err.error?.detail || 'Error al eliminar el CTF';
                this.notificationService.error(message);
            }
        });
    }

    // UI Helpers
    getCategoryClass(category: string): string {
        const classes: Record<string, string> = {
            'web': 'bg-blue-500/20 text-blue-300',
            'crypto': 'bg-purple-500/20 text-purple-300',
            'forensics': 'bg-green-500/20 text-green-300',
            'pwn': 'bg-red-500/20 text-red-300',
            'reverse': 'bg-orange-500/20 text-orange-300',
            'misc': 'bg-gray-500/20 text-gray-300',
            'osint': 'bg-cyan-500/20 text-cyan-300',
            'stego': 'bg-pink-500/20 text-pink-300'
        };
        return classes[category] || 'bg-gray-500/20 text-gray-300';
    }

    getDifficultyClass(level: string): string {
        const classes: Record<string, string> = {
            'easy': 'bg-green-500/20 text-green-300',
            'medium': 'bg-yellow-500/20 text-yellow-300',
            'hard': 'bg-orange-500/20 text-orange-300',
            'insane': 'bg-red-500/20 text-red-300'
        };
        return classes[level] || 'bg-gray-500/20 text-gray-300';
    }

    getDifficultyLabel(level: string): string {
        const labels: Record<string, string> = {
            'easy': 'Fácil',
            'medium': 'Medio',
            'hard': 'Difícil',
            'insane': 'Insano'
        };
        return labels[level] || level;
    }

    getStatusClass(status: string): string {
        const classes: Record<string, string> = {
            'draft': 'bg-yellow-500/20 text-yellow-300',
            'published': 'bg-green-500/20 text-green-300',
            'archived': 'bg-gray-500/20 text-gray-300'
        };
        return classes[status] || 'bg-gray-500/20 text-gray-300';
    }

    getStatusLabel(status: string): string {
        const labels: Record<string, string> = {
            'draft': 'Borrador',
            'published': 'Publicado',
            'archived': 'Archivado'
        };
        return labels[status] || status;
    }
}
