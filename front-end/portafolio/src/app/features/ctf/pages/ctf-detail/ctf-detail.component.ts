import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { CtfService } from '@core/services/ctf.service';
import { AuthService } from '../../../../core/services/auth.service';
import { CTFChallenge, CTF_CATEGORIES, CTF_DIFFICULTIES, CTFAttachment, AttachmentType } from '@core/models/ctf.model';

@Component({
  selector: 'app-ctf-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './ctf-detail.component.html',
  styleUrls: ['./ctf-detail.component.scss']
})
export class CtfDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly ctfService = inject(CtfService);
  public readonly authService = inject(AuthService); // Public para usar en template

  challenge: CTFChallenge | null = null;
  isSolved = false;
  isLoading = true;

  // Flag submission
  flagInput = '';
  isSubmitting = false;
  submitResult: { success: boolean; message: string } | null = null;

  // Hints
  revealedHints: Set<number> = new Set();

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loadChallenge(id);
      this.loadChallengeFromApi(id);
    }
  }

  loadChallenge(id: string): void {
    const challenge = this.ctfService.getChallengeById(id);
    if (challenge) {
      this.challenge = challenge;
      this.isSolved = this.ctfService.isSolved(id);
      this.isLoading = false;
    }
  }

  /**
   * Carga el challenge desde la API
   */
  loadChallengeFromApi(id: string): void {
    this.ctfService.getChallengeByIdFromApi(id).subscribe({
      next: (challenge) => {
        if (challenge) {
          this.challenge = challenge;
          this.isSolved = challenge.solved || this.ctfService.isSolved(id);
        } else if (!this.challenge) {
          // No hay datos ni de API ni locales
          this.router.navigate(['/ctf']);
        }
        this.isLoading = false;
      },
      error: (err) => {
        console.log('Usando challenge local:', err.message);
        this.isLoading = false;
        if (!this.challenge) {
          this.router.navigate(['/ctf']);
        }
      }
    });
  }

  get categoryInfo() {
    if (!this.challenge) return null;
    return CTF_CATEGORIES.find(c => c.value === this.challenge?.category);
  }

  get difficultyInfo() {
    if (!this.challenge) return null;
    return CTF_DIFFICULTIES.find(d => d.value === this.challenge?.difficulty);
  }

  get difficultyColorClass(): string {
    if (!this.challenge) return '';
    const colors: Record<string, string> = {
      easy: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      medium: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      hard: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
      insane: 'bg-red-500/20 text-red-400 border-red-500/30'
    };
    return colors[this.challenge.difficulty] || '';
  }

  async submitFlag(): Promise<void> {
    if (!this.challenge || !this.flagInput.trim() || this.isSubmitting) return;

    // Verificar si el usuario está autenticado
    if (!this.authService.isAuthenticated) {
      this.submitResult = {
        success: false,
        message: '🔒 Debes iniciar sesión para enviar flags'
      };
      return;
    }

    this.isSubmitting = true;
    this.submitResult = null;

    // Intentar con la API primero
    this.ctfService.submitFlagToApi(this.challenge.id, this.flagInput.trim()).subscribe({
      next: (result) => {
        this.submitResult = result;
        if (result.success) {
          this.isSolved = true;
          this.flagInput = '';

          // ✅ Recargar el challenge actual para actualizar su estado
          this.loadChallengeFromApi(this.challenge!.id);
        }
        this.isSubmitting = false;
      },
      error: async () => {
        // Fallback a método local
        try {
          const result = await this.ctfService.submitFlag({
            challengeId: this.challenge!.id,
            flag: this.flagInput.trim(),
            submittedAt: new Date()
          });

          this.submitResult = result;

          if (result.success) {
            this.isSolved = true;
            this.flagInput = '';
          }
        } finally {
          this.isSubmitting = false;
        }
      }
    });
  }

  revealHint(index: number): void {
    this.revealedHints.add(index);
  }

  isHintRevealed(index: number): boolean {
    return this.revealedHints.has(index);
  }

  // ==================== ATTACHMENT HELPERS ====================

  get hasAttachments(): boolean {
    return !!this.challenge?.attachments && this.challenge.attachments.length > 0;
  }

  getAttachmentIcon(type: AttachmentType): string {
    const icons: Record<AttachmentType, string> = {
      file: '📎',
      url: '🔗',
      docker: '🐳'
    };
    return icons[type] || '📎';
  }

  getAttachmentAction(type: AttachmentType): string {
    const actions: Record<AttachmentType, string> = {
      file: 'Descargar',
      url: 'Abrir enlace',
      docker: 'Ver instrucciones'
    };
    return actions[type] || 'Ver';
  }

  getAttachmentClass(type: AttachmentType): string {
    const classes: Record<AttachmentType, string> = {
      file: 'resource--file',
      url: 'resource--url',
      docker: 'resource--docker'
    };
    return classes[type] || '';
  }

  onAttachmentClick(attachment: CTFAttachment): void {
    if (attachment.type === 'url') {
      // Abrir URL en nueva pestaña
      window.open(attachment.url, '_blank', 'noopener,noreferrer');
    } else if (attachment.type === 'file') {
      // Descargar archivo
      this.downloadFile(attachment);
    } else if (attachment.type === 'docker') {
      // Mostrar instrucciones de Docker (por ahora copiar al clipboard)
      this.copyDockerCommand(attachment);
    }
  }

  private downloadFile(attachment: CTFAttachment): void {
    // Crear un link temporal para descargar
    const link = document.createElement('a');
    link.href = attachment.url;
    link.download = attachment.name;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  private copyDockerCommand(attachment: CTFAttachment): void {
    const dockerImage = attachment.url.replace('docker://', '');
    const command = `docker run -it --rm ${dockerImage}`;

    navigator.clipboard.writeText(command).then(() => {
      // Podríamos mostrar un toast aquí
      alert(`Comando copiado:\n${command}`);
    });
  }

  formatFileSize(bytes?: number): string {
    if (!bytes) return '';
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    const mb = kb / 1024;
    return `${mb.toFixed(1)} MB`;
  }
}
