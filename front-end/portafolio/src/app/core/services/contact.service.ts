import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { ContactForm, ContactInfo } from '../models';
import { ApiService } from './api.service';

interface ProjectTypeResponse {
  value: string;
  label: string;
}

interface ContactResponse {
  id: string;
  name: string;
  email: string;
  project_type: string;
  message: string;
  status: string;
  created_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class ContactService {

  // Datos de respaldo (fallback) si la API no responde
  private readonly fallbackContactInfo: ContactInfo[] = [
    {
      type: 'email',
      label: 'Correo directo',
      value: 'elvis.dev@mail.com',
      url: 'mailto:elvis.dev@mail.com',
      icon: 'email'
    },
    {
      type: 'linkedin',
      label: 'Perfil profesional',
      value: 'linkedin.com/in/elvis',
      url: 'https://linkedin.com/in/elvis',
      icon: 'linkedin'
    },
    {
      type: 'github',
      label: 'Código y proyectos',
      value: 'github.com/elvis',
      url: 'https://github.com/elvis',
      icon: 'github'
    }
  ];

  private readonly fallbackProjectTypes = [
    { value: 'web', label: 'Desarrollo web' },
    { value: 'security', label: 'Consultoría de seguridad' },
    { value: 'ctf', label: 'CTF / Red Team' },
    { value: 'other', label: 'Otro' }
  ];

  constructor(private api: ApiService) {}

  /**
   * Obtiene la información de contacto desde la API
   */
  getContactInfo(): ContactInfo[] {
    // Por ahora retorna datos locales ya que el backend devuelve formato diferente
    // TODO: Mapear respuesta del backend cuando se implemente
    return [...this.fallbackContactInfo];
  }

  /**
   * Obtiene los tipos de proyecto desde la API
   */
  getProjectTypes(): Observable<ProjectTypeResponse[]> {
    return this.api.get<ProjectTypeResponse[]>('/contact/project-types').pipe(
      catchError(() => of(this.fallbackProjectTypes))
    );
  }

  /**
   * Obtiene los tipos de proyecto de forma síncrona (fallback)
   */
  getProjectTypesSync(): { value: string; label: string }[] {
    return [...this.fallbackProjectTypes];
  }

  /**
   * Envía el formulario de contacto a la API
   */
  submitContact(form: ContactForm): Observable<ContactResponse> {
    return this.api.post<ContactResponse>('/contact', {
      name: form.name,
      email: form.email,
      project_type: form.projectType,
      message: form.message
    });
  }

  /**
   * Versión async para compatibilidad con código existente
   */
  async submitContactAsync(form: ContactForm): Promise<boolean> {
    return new Promise((resolve, reject) => {
      this.submitContact(form).subscribe({
        next: () => resolve(true),
        error: (err) => {
          console.error('Error submitting contact:', err);
          reject(err);
        }
      });
    });
  }
}
