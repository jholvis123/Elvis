import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

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
    }).pipe(catchError(this.handleError));
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
    }).pipe(catchError(this.handleError));
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
    }).pipe(catchError(this.handleError));
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
    }).pipe(catchError(this.handleError));
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
    }).pipe(catchError(this.handleError));
  }

  /**
   * Upload file with FormData
   */
  upload<T>(endpoint: string, formData: FormData, options?: RequestOptions): Observable<T> {
    return this.http.post<T>(`${this.baseUrl}${endpoint}`, formData, {
      headers: this.buildHeaders(options?.headers),
      withCredentials: options?.withCredentials ?? true
    }).pipe(catchError(this.handleError));
  }

  /**
   * Error handler
   */
  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'Ha ocurrido un error';
    
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = error.error.message;
    } else {
      // Server-side error
      if (error.error?.detail) {
        errorMessage = error.error.detail;
      } else if (error.status === 0) {
        errorMessage = 'No se puede conectar al servidor';
      } else if (error.status === 401) {
        errorMessage = 'No autorizado';
      } else if (error.status === 403) {
        errorMessage = 'Acceso denegado';
      } else if (error.status === 404) {
        errorMessage = 'Recurso no encontrado';
      } else if (error.status >= 500) {
        errorMessage = 'Error interno del servidor';
      }
    }
    
    console.error('API Error:', error);
    return throwError(() => new Error(errorMessage));
  }
}
