import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import {
  ContactForm,
  ContactInfo,
  ContactInfoApi,
  ContactListResponse,
  ContactMessage
} from '../models';
import { ApiService } from './api.service';

interface ProjectTypeResponse {
  value: string;
  label: string;
}

@Injectable({
  providedIn: 'root'
})
export class ContactService {
  private readonly fallbackProjectTypes = [
    { value: 'web', label: 'Desarrollo web' },
    { value: 'security', label: 'Consultoría de seguridad' },
    { value: 'ctf', label: 'CTF / Red Team' },
    { value: 'other', label: 'Otro' }
  ];

  constructor(private api: ApiService) {}

  getContactInfo(): Observable<ContactInfo[]> {
    return this.api.get<ContactInfoApi>('/portfolio/contact-info').pipe(
      map(info => this.mapContactInfo(info)),
      catchError(() => of([]))
    );
  }

  mapContactInfo(info: ContactInfoApi | null | undefined): ContactInfo[] {
    if (!info) return [];
    const items: ContactInfo[] = [];
    const email = info.email?.trim();
    const github = info.github?.trim();
    const linkedin = info.linkedin?.trim();
    const twitter = info.twitter?.trim();

    if (email) {
      items.push({
        type: 'email',
        label: 'Correo directo',
        value: email,
        url: `mailto:${email}`,
        icon: 'email'
      });
    }
    if (github) {
      items.push({
        type: 'github',
        label: 'Código y proyectos',
        value: this.displayUrl(github),
        url: this.ensureUrl(github),
        icon: 'github'
      });
    }
    if (linkedin) {
      items.push({
        type: 'linkedin',
        label: 'Perfil profesional',
        value: this.displayUrl(linkedin),
        url: this.ensureUrl(linkedin),
        icon: 'linkedin'
      });
    }
    if (twitter) {
      items.push({
        type: 'twitter',
        label: 'Red social',
        value: this.displayUrl(twitter),
        url: this.ensureUrl(twitter),
        icon: 'twitter'
      });
    }

    return items;
  }

  mapSocialLinks(social: {
    email?: string;
    github?: string;
    linkedin?: string;
    twitter?: string;
  } | Record<string, string> | null | undefined): ContactInfo[] {
    if (!social) return [];
    const record = social as Record<string, string | undefined>;
    return this.mapContactInfo({
      email: record['email'] || '',
      github: record['github'],
      linkedin: record['linkedin'],
      twitter: record['twitter']
    });
  }

  getProjectTypes(): Observable<ProjectTypeResponse[]> {
    return this.api.get<ProjectTypeResponse[]>('/contact/project-types').pipe(
      catchError(() => of(this.fallbackProjectTypes))
    );
  }

  getProjectTypesSync(): { value: string; label: string }[] {
    return [...this.fallbackProjectTypes];
  }

  submitContact(form: ContactForm): Observable<ContactMessage> {
    return this.api.post<ContactMessage>('/contact', {
      name: form.name,
      email: form.email,
      project_type: form.projectType,
      message: form.message
    });
  }

  async submitContactAsync(form: ContactForm): Promise<boolean> {
    return new Promise((resolve, reject) => {
      this.submitContact(form).subscribe({
        next: () => resolve(true),
        error: (err) => reject(err)
      });
    });
  }

  getMessages(params?: {
    status?: string;
    skip?: number;
    limit?: number;
  }): Observable<ContactListResponse> {
    return this.api.get<ContactListResponse>('/contact', {
      ...(params?.status && { status_filter: params.status }),
      skip: params?.skip ?? 0,
      limit: params?.limit ?? 20
    });
  }

  getMessage(id: string): Observable<ContactMessage> {
    return this.api.get<ContactMessage>(`/contact/${id}`);
  }

  markRead(id: string): Observable<ContactMessage> {
    return this.api.patch<ContactMessage>(`/contact/${id}/mark-read`, {});
  }

  markReplied(id: string): Observable<ContactMessage> {
    return this.api.patch<ContactMessage>(`/contact/${id}/mark-replied`, {});
  }

  deleteMessage(id: string): Observable<void> {
    return this.api.delete<void>(`/contact/${id}`);
  }

  private displayUrl(value: string): string {
    return value.replace(/^https?:\/\//, '').replace(/\/$/, '');
  }

  private ensureUrl(value: string): string {
    if (/^https?:\/\//i.test(value) || value.startsWith('mailto:')) {
      return value;
    }
    return `https://${value}`;
  }
}
