import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { ApiService } from './api.service';

/** Contrato esperado de GET /admin/stats (PR de backend hermano). */
export interface AdminStats {
  projects: number;
  writeups_published: number;
  writeups_draft: number;
  ctfs: number;
  contact_pending: number;
  contact_total: number;
}

@Injectable({
  providedIn: 'root'
})
export class AdminService {
  constructor(private api: ApiService) {}

  getStats(): Observable<AdminStats> {
    return this.api.get<Record<string, number>>('/admin/stats').pipe(
      map(raw => ({
        projects: raw['projects'] ?? raw['total_projects'] ?? raw['totalProjects'] ?? 0,
        writeups_published: raw['writeups_published'] ?? raw['published_writeups'] ?? raw['publishedWriteups'] ?? 0,
        writeups_draft: raw['writeups_draft'] ?? raw['draft_writeups'] ?? 0,
        ctfs: raw['ctfs'] ?? raw['total_ctfs'] ?? raw['totalCTFs'] ?? 0,
        contact_pending: raw['contact_pending'] ?? raw['unread_contacts'] ?? 0,
        contact_total: raw['contact_total'] ?? raw['total_contacts'] ?? 0
      }))
    );
  }
}
