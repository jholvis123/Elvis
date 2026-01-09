/**
 * Attachment Service
 * Servicio para gestión de adjuntos (archivos y URLs) en retos CTF
 */

import { Injectable, inject } from '@angular/core';
import {
  CTFCategory,
  CTFAttachment,
  AttachmentType,
  CategoryAttachmentConfig,
  ValidationResult,
  CATEGORY_ATTACHMENT_CONFIG
} from '@core/models/ctf.model';
import { FileValidators } from '@core/validators/file.validators';
import { ApiService } from './api.service';
import { firstValueFrom } from 'rxjs'; // For toPromise replacement if strictly angular 16+ (using toPromise for now as it's common)

export interface FileUploadResult {
  success: boolean;
  attachment?: CTFAttachment;
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AttachmentService {

  constructor(private api: ApiService) { }

  // ============================================
  // CONFIGURACIÓN POR CATEGORÍA
  // ============================================

  /**
   * Obtiene la configuración de adjuntos para una categoría
   */
  getConfigForCategory(category: CTFCategory): CategoryAttachmentConfig {
    return CATEGORY_ATTACHMENT_CONFIG[category];
  }

  /**
   * Verifica si una categoría requiere archivos
   */
  requiresFiles(category: CTFCategory): boolean {
    const config = this.getConfigForCategory(category);
    return config?.requiredTypes.includes('file') ?? false;
  }

  /**
   * Verifica si una categoría requiere URLs
   */
  requiresUrl(category: CTFCategory): boolean {
    const config = this.getConfigForCategory(category);
    return config?.requiredTypes.includes('url') ?? false;
  }

  /**
   * Verifica si una categoría soporta Docker
   */
  supportsDocker(category: CTFCategory): boolean {
    const config = this.getConfigForCategory(category);
    return config?.requiredTypes.includes('docker') ?? false;
  }

  /**
   * Obtiene los tipos de adjuntos permitidos para una categoría
   */
  getAllowedTypes(category: CTFCategory): AttachmentType[] {
    const config = this.getConfigForCategory(category);
    return config?.requiredTypes ?? [];
  }

  // ============================================
  // VALIDACIÓN DE ARCHIVOS
  // ============================================

  /**
   * Valida un archivo contra la configuración de categoría
   */
  validateFile(file: File, category: CTFCategory): ValidationResult {
    const config = this.getConfigForCategory(category);
    const errors: string[] = [];

    if (!config) {
      return { valid: false, errors: ['Categoría no válida'] };
    }

    // No permite archivos
    if (!config.requiredTypes.includes('file')) {
      return { valid: false, errors: ['Esta categoría no acepta archivos'] };
    }

    // Validar tamaño
    if (config.maxFileSize > 0 && file.size > config.maxFileSize) {
      errors.push(`Archivo demasiado grande. Máximo: ${FileValidators.formatSize(config.maxFileSize)}`);
    }

    // Validar MIME type
    if (config.allowedMimeTypes.length > 0 && !config.allowedMimeTypes.includes('*/*')) {
      if (!FileValidators.isMimeTypeAllowed(file.type, config.allowedMimeTypes)) {
        errors.push(`Tipo de archivo no permitido: ${file.type || 'desconocido'}`);
      }
    }

    // Validar extensión
    const ext = FileValidators.getExtension(file.name);
    if (config.allowedExtensions.length > 0 && !config.allowedExtensions.includes('*')) {
      if (!FileValidators.isExtensionAllowed(ext, config.allowedExtensions)) {
        errors.push(`Extensión .${ext} no permitida. Usa: ${config.allowedExtensions.join(', ')}`);
      }
    }

    return { valid: errors.length === 0, errors };
  }

  /**
   * Valida múltiples archivos
   */
  validateFiles(files: File[], category: CTFCategory): ValidationResult {
    const config = this.getConfigForCategory(category);
    const errors: string[] = [];

    if (!config) {
      return { valid: false, errors: ['Categoría no válida'] };
    }

    // Validar cantidad máxima
    if (config.maxFiles > 0 && files.length > config.maxFiles) {
      errors.push(`Máximo ${config.maxFiles} archivos permitidos`);
    }

    // Validar cada archivo
    files.forEach((file, index) => {
      const result = this.validateFile(file, category);
      if (!result.valid) {
        errors.push(`Archivo ${index + 1} (${file.name}): ${result.errors.join(', ')}`);
      }
    });

    return { valid: errors.length === 0, errors };
  }

  // ============================================
  // VALIDACIÓN DE URLs
  // ============================================

  /**
   * Valida una URL contra la configuración de categoría
   */
  validateUrl(url: string, category: CTFCategory): ValidationResult {
    const config = this.getConfigForCategory(category);
    const errors: string[] = [];

    if (!config) {
      return { valid: false, errors: ['Categoría no válida'] };
    }

    // Validar formato URL
    try {
      new URL(url);
    } catch {
      return { valid: false, errors: ['URL inválida'] };
    }

    // Validar patrones si existen
    if (config.urlPatterns && config.urlPatterns.length > 0) {
      const matchesPattern = config.urlPatterns.some(p => p.test(url));
      if (!matchesPattern) {
        errors.push('La URL no cumple con el formato requerido');
      }
    }

    // Validar protocolo (debe ser http o https)
    const parsed = new URL(url);
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      errors.push('Solo se permiten URLs HTTP o HTTPS');
    }

    return { valid: errors.length === 0, errors };
  }

  // ============================================
  // CREACIÓN DE ADJUNTOS
  // ============================================

  /**
   * Crea un objeto CTFAttachment desde un File
   */
  createFileAttachment(file: File, uploadedUrl: string): CTFAttachment {
    return {
      id: this.generateId(),
      name: file.name,
      type: 'file',
      url: uploadedUrl,
      size: file.size,
      mimeType: file.type,
      uploadedAt: new Date()
    };
  }

  /**
   * Crea un objeto CTFAttachment desde una URL
   */
  createUrlAttachment(url: string, name?: string): CTFAttachment {
    const parsed = new URL(url);
    return {
      id: this.generateId(),
      name: name || parsed.hostname,
      type: 'url',
      url: url,
      uploadedAt: new Date()
    };
  }

  /**
   * Crea un objeto CTFAttachment para Docker
   */
  createDockerAttachment(imageName: string): CTFAttachment {
    return {
      id: this.generateId(),
      name: imageName,
      type: 'docker',
      url: `docker://${imageName}`,
      uploadedAt: new Date()
    };
  }

  // ============================================
  // UPLOAD (simulado - integrar con backend real)
  // ============================================

  /**
   * Sube un archivo al servidor (simulado)
   * En producción: integrar con tu backend/storage
   */
  /**
   * Sube un archivo al servidor
   */
  async uploadFile(file: File, category: CTFCategory, ctfId?: string): Promise<FileUploadResult> {
    // Validar primero
    const validation = this.validateFile(file, category);
    if (!validation.valid) {
      return { success: false, error: validation.errors.join(', ') };
    }

    try {
      const formData = new FormData();
      formData.append('file', file);
      if (ctfId) {
        formData.append('ctf_id', ctfId);
      }

      const response = await firstValueFrom(this.api.upload<any>('/attachments/upload', formData));

      return {
        success: true,
        attachment: this.mapApiToAttachment(response)
      };
    } catch (error: any) {
      console.error('Error uploading file:', error);
      return {
        success: false,
        error: error.message || 'Error al subir archivo'
      };
    }
  }

  private mapApiToAttachment(apiResponse: any): CTFAttachment {
    return {
      id: apiResponse.id,
      name: apiResponse.filename,
      type: 'file',
      url: apiResponse.url,
      size: apiResponse.size,
      mimeType: apiResponse.mime_type,
      uploadedAt: new Date()
    };
  }

  /**
   * Sube múltiples archivos
   */
  async uploadFiles(files: File[], category: CTFCategory): Promise<FileUploadResult[]> {
    const results: FileUploadResult[] = [];

    for (const file of files) {
      const result = await this.uploadFile(file, category);
      results.push(result);
    }

    return results;
  }

  // ============================================
  // UTILIDADES
  // ============================================

  /**
   * Genera un ID único
   */
  private generateId(): string {
    return `att_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Formatea tamaño de archivo
   */
  formatFileSize(bytes: number): string {
    return FileValidators.formatSize(bytes);
  }

  /**
   * Obtiene las extensiones permitidas como string
   */
  getAllowedExtensionsString(category: CTFCategory): string {
    const config = this.getConfigForCategory(category);
    if (!config || config.allowedExtensions.includes('*')) {
      return 'Cualquier extensión';
    }
    return config.allowedExtensions.join(', ');
  }

  /**
   * Obtiene el tamaño máximo formateado
   */
  getMaxFileSizeFormatted(category: CTFCategory): string {
    const config = this.getConfigForCategory(category);
    if (!config || config.maxFileSize === 0) {
      return 'Sin límite';
    }
    return FileValidators.formatSize(config.maxFileSize);
  }

  /**
   * Obtiene el accept string para input file
   */
  getAcceptString(category: CTFCategory): string {
    const config = this.getConfigForCategory(category);
    if (!config || config.allowedMimeTypes.includes('*/*')) {
      return '*/*';
    }

    // Combinar MIME types y extensiones
    const mimes = config.allowedMimeTypes.join(',');
    const exts = config.allowedExtensions
      .filter(e => e !== '*')
      .map(e => e.startsWith('.') ? e : `.${e}`)
      .join(',');

    return [mimes, exts].filter(Boolean).join(',');
  }
}
