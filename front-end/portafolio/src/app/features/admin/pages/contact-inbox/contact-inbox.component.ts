import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ContactService } from '@core/services';
import { ContactMessage } from '@core/models';
import { NotificationService } from '@core/services/notification.service';
import { PaginationComponent } from '@shared/components/pagination/pagination.component';
import { ConfirmDialogComponent } from '@shared/components/confirm-dialog/confirm-dialog.component';
import { IconComponent } from '@shared/icons/icon.component';
import { ApiError } from '@core/services/api.service';

@Component({
  selector: 'app-contact-inbox',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    FormsModule,
    PaginationComponent,
    ConfirmDialogComponent,
    IconComponent
  ],
  templateUrl: './contact-inbox.component.html',
  styleUrls: ['./contact-inbox.component.scss']
})
export class ContactInboxComponent implements OnInit {
  private readonly contactService = inject(ContactService);
  private readonly notifications = inject(NotificationService);
  private readonly destroyRef = inject(DestroyRef);

  messages: ContactMessage[] = [];
  loading = false;
  errorMessage = '';
  filterStatus = '';
  page = 1;
  limit = 10;
  total = 0;

  selected: ContactMessage | null = null;
  showDeleteModal = false;
  messageToDelete: ContactMessage | null = null;

  readonly goToPage = (page: number) => this.onPageChange(page);

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.total / this.limit));
  }

  ngOnInit(): void {
    this.loadMessages();
  }

  loadMessages(): void {
    this.loading = true;
    this.errorMessage = '';
    const skip = (this.page - 1) * this.limit;

    this.contactService.getMessages({
      status: this.filterStatus || undefined,
      skip,
      limit: this.limit
    }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (response) => {
        this.messages = response.items || [];
        this.total = response.total || 0;
        this.loading = false;
      },
      error: (err: unknown) => {
        this.messages = [];
        this.total = 0;
        this.loading = false;
        this.errorMessage = this.humanError(err, 'No se pudieron cargar los mensajes.');
      }
    });
  }

  onFilterChange(): void {
    this.page = 1;
    this.selected = null;
    this.loadMessages();
  }

  onPageChange(page: number): void {
    if (page < 1 || page > this.totalPages) return;
    this.page = page;
    this.loadMessages();
  }

  openMessage(message: ContactMessage): void {
    this.selected = message;
    if (message.status === 'pending') {
      this.markRead(message, false);
    }
  }

  markRead(message: ContactMessage, notify = true): void {
    this.contactService.markRead(message.id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (updated) => {
        this.patchMessage(updated);
        if (notify) {
          this.notifications.success('Mensaje marcado como leído');
        }
      }
    });
  }

  markReplied(message: ContactMessage): void {
    this.contactService.markReplied(message.id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (updated) => {
        this.patchMessage(updated);
        this.notifications.success('Mensaje marcado como respondido');
      }
    });
  }

  confirmDelete(message: ContactMessage): void {
    this.messageToDelete = message;
    this.showDeleteModal = true;
  }

  cancelDelete(): void {
    this.showDeleteModal = false;
    this.messageToDelete = null;
  }

  executeDelete(): void {
    if (!this.messageToDelete) return;
    const id = this.messageToDelete.id;
    this.contactService.deleteMessage(id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.notifications.success('Mensaje eliminado');
        if (this.selected?.id === id) {
          this.selected = null;
        }
        this.cancelDelete();
        this.loadMessages();
      }
    });
  }

  statusLabel(status: string): string {
    const labels: Record<string, string> = {
      pending: 'Pendiente',
      read: 'Leído',
      replied: 'Respondido'
    };
    return labels[status] || status;
  }

  statusClass(status: string): string {
    const classes: Record<string, string> = {
      pending: 'bg-warning/20 text-warning',
      read: 'bg-primary/20 text-primary',
      replied: 'bg-success/20 text-success'
    };
    return classes[status] || 'bg-slate-700 text-textSecondary';
  }

  projectTypeLabel(type: string): string {
    const labels: Record<string, string> = {
      web: 'Desarrollo web',
      security: 'Seguridad',
      ctf: 'CTF / Red Team',
      other: 'Otro'
    };
    return labels[type] || type;
  }

  private patchMessage(updated: ContactMessage): void {
    this.messages = this.messages.map(m => m.id === updated.id ? updated : m);
    if (this.selected?.id === updated.id) {
      this.selected = updated;
    }
  }

  private humanError(err: unknown, fallback: string): string {
    if (err instanceof ApiError) {
      return err.message;
    }
    if (err instanceof Error && err.message) {
      return err.message;
    }
    return fallback;
  }
}
