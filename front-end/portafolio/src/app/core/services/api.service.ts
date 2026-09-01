import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export interface RequestOptions {
  params?: Record<string, string | number | boolean>;
  withCredentials?: boolean;
  headers?: Record<string, string>;
}

// Type guard para detectar si es RequestOptions o params directo
function isRequestOptions(obj: unknown): obj is RequestOptions {
  if (!obj || typeof obj !== 'object') return false;
  const keys = Object.keys(obj);
  // Si tiene las claves específicas de RequestOptions
  return keys.some(k => ['params', 'withCredentials', 'headers'].includes(k));
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  private buildParams(params?: Record<string, string | number | boolean>): HttpParams {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach(key => {
        if (params[key] !== undefined && params[key] !== null) {
          httpParams = httpParams.set(key, String(params[key]));
        }
      });
    }
    return httpParams;
  }

  private buildHeaders(headers?: Record<string, string>): HttpHeaders {
    let httpHeaders = new HttpHeaders();
    if (headers) {
      Object.keys(headers).forEach(key => {
        httpHeaders = httpHeaders.set(key, headers[key]);
      });
    }
    return httpHeaders;
  }

  /**
   * Normaliza las opciones: acepta tanto params directo (retrocompatibilidad) como RequestOptions
   */
  private normalizeOptions(optionsOrParams?: RequestOptions | Record<string, string | number | boolean>): RequestOptions {
    if (!optionsOrParams) return {};
    if (isRequestOptions(optionsOrParams)) return optionsOrParams;
    // Es un objeto de params directo (retrocompatibilidad)
    return { params: optionsOrParams };
  }

  /**
   * GET request
   * @param endpoint - API endpoint
   * @param optionsOrParams - RequestOptions object or params object (for backwards compatibility)
   */
  get<T>(endpoint: string, optionsOrParams?: RequestOptions | Record<string, string | number | boolean>): Observable<T> {
    const options = this.normalizeOptions(optionsOrParams);
    return this.http.get<T>(`${this.baseUrl}${endpoint}`, { 
      params: this.buildParams(options.params),
      headers: this.buildHeaders(options.headers),
      withCredentials: options.withCredentials ?? true
    });
  }

  /**
   * POST request
   */
  post<T>(endpoint: string, body: unknown, optionsOrParams?: RequestOptions | Record<string, string | number | boolean>): Observable<T> {
    const options = this.normalizeOptions(optionsOrParams);
    return this.http.post<T>(`${this.baseUrl}${endpoint}`, body, {
      params: this.buildParams(options.params),
      headers: this.buildHeaders(options.headers),
      withCredentials: options.withCredentials ?? true
    });
  }

  /**
   * PUT request
   */
  put<T>(endpoint: string, body: unknown, optionsOrParams?: RequestOptions | Record<string, string | number | boolean>): Observable<T> {
    const options = this.normalizeOptions(optionsOrParams);
    return this.http.put<T>(`${this.baseUrl}${endpoint}`, body, {
      params: this.buildParams(options.params),
      headers: this.buildHeaders(options.headers),
      withCredentials: options.withCredentials ?? true
    });
  }

  /**
   * PATCH request
   */
  patch<T>(endpoint: string, body?: unknown, optionsOrParams?: RequestOptions | Record<string, string | number | boolean>): Observable<T> {
    const options = this.normalizeOptions(optionsOrParams);
    return this.http.patch<T>(`${this.baseUrl}${endpoint}`, body, {
      params: this.buildParams(options.params),
      headers: this.buildHeaders(options.headers),
      withCredentials: options.withCredentials ?? true
    });
  }

  /**
   * DELETE request
   */
  delete<T>(endpoint: string, optionsOrParams?: RequestOptions | Record<string, string | number | boolean>): Observable<T> {
    const options = this.normalizeOptions(optionsOrParams);
    return this.http.delete<T>(`${this.baseUrl}${endpoint}`, { 
      params: this.buildParams(options.params),
      headers: this.buildHeaders(options.headers),
      withCredentials: options.withCredentials ?? true
    });
  }

  /**
   * Upload file with FormData
   */
  upload<T>(endpoint: string, formData: FormData, options?: RequestOptions): Observable<T> {
    return this.http.post<T>(`${this.baseUrl}${endpoint}`, formData, {
      headers: this.buildHeaders(options?.headers),
      withCredentials: options?.withCredentials ?? true
    });
  }

  /**
   * Los errores HTTP se traducen en un único sitio: errorInterceptor.
   * ApiService no vuelve a mapear el mensaje para evitar duplicar toasts y perder el status.
   */
}
