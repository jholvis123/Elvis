/**
 * File Validators
 * Validadores para archivos y URLs
 */

import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';
import { CategoryAttachmentConfig } from '@core/models/ctf.model';

export class FileValidators {
  
  // ============================================
  // VALIDADORES DE ARCHIVOS
  // ============================================
  
  /**
   * Valida el tamaño máximo de un archivo
   */
  static maxSize(maxBytes: number): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const file = control.value as File;
      if (!file || !(file instanceof File)) return null;
      
      if (file.size > maxBytes) {
        return {
          maxSize: {
            message: `El archivo es demasiado grande (máx: ${FileValidators.formatSize(maxBytes)})`,
            max: maxBytes,
            actual: file.size,
            maxFormatted: FileValidators.formatSize(maxBytes),
            actualFormatted: FileValidators.formatSize(file.size)
          }
        };
      }
      return null;
    };
  }
  
  /**
   * Valida los tipos MIME permitidos
   */
  static allowedMimeTypes(mimeTypes: string[]): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const file = control.value as File;
      if (!file || !(file instanceof File)) return null;
      
      const isAllowed = FileValidators.isMimeTypeAllowed(file.type, mimeTypes);
      
      if (!isAllowed) {
        return {
          invalidMimeType: {
            message: 'Tipo de archivo no permitido',
            allowed: mimeTypes,
            actual: file.type
          }
        };
      }
      return null;
    };
  }
  
  /**
   * Valida las extensiones permitidas
   */
  static allowedExtensions(extensions: string[]): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const file = control.value as File;
      if (!file || !(file instanceof File)) return null;
      
      if (extensions.includes('*')) return null;
      
      const ext = FileValidators.getExtension(file.name);
      const isAllowed = extensions.some(e => 
        e.toLowerCase() === ext.toLowerCase() ||
        e.toLowerCase() === `.${ext}`.toLowerCase()
      );
      
      if (!isAllowed) {
        return {
          invalidExtension: {
            message: `Extensión no permitida. Permitidas: ${extensions.join(', ')}`,
            allowed: extensions,
            actual: ext
          }
        };
      }
      return null;
    };
  }
  
  /**
   * Validador combinado usando configuración de categoría
   */
  static fromConfig(config: CategoryAttachmentConfig): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const file = control.value as File;
      if (!file || !(file instanceof File)) return null;
      
      // Validar tamaño
      if (config.maxFileSize > 0 && file.size > config.maxFileSize) {
        return {
          maxSize: {
            message: `El archivo es demasiado grande (máx: ${FileValidators.formatSize(config.maxFileSize)})`,
            max: config.maxFileSize,
            actual: file.size
          }
        };
      }
      
      // Validar MIME type
      if (config.allowedMimeTypes.length > 0) {
        const isAllowed = FileValidators.isMimeTypeAllowed(file.type, config.allowedMimeTypes);
        if (!isAllowed) {
          return {
            invalidMimeType: {
              message: 'Tipo de archivo no permitido para esta categoría',
              allowed: config.allowedMimeTypes,
              actual: file.type
            }
          };
        }
      }
      
      // Validar extensión
      if (config.allowedExtensions.length > 0 && !config.allowedExtensions.includes('*')) {
        const ext = FileValidators.getExtension(file.name);
        const isExtAllowed = config.allowedExtensions.some(e => 
          e.toLowerCase().replace('.', '') === ext.toLowerCase()
        );
        if (!isExtAllowed) {
          return {
            invalidExtension: {
              message: `Extensión no permitida. Usa: ${config.allowedExtensions.join(', ')}`,
              allowed: config.allowedExtensions,
              actual: ext
            }
          };
        }
      }
      
      return null;
    };
  }
  
  // ============================================
  // VALIDADORES DE URL
  // ============================================
  
  /**
   * Valida que sea una URL válida
   */
  static validUrl(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const value = control.value;
      if (!value) return null;
      
      try {
        new URL(value);
        return null;
      } catch {
        return { invalidUrl: { message: 'URL inválida' } };
      }
    };
  }
  
  /**
   * Valida que la URL use HTTPS
   */
  static httpsOnly(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const value = control.value;
      if (!value) return null;
      
      try {
        const url = new URL(value);
        if (url.protocol !== 'https:') {
          return { httpsRequired: { message: 'La URL debe usar HTTPS' } };
        }
        return null;
      } catch {
        return null; // validUrl manejará esto
      }
    };
  }
  
  /**
   * Valida que la URL coincida con patrones específicos
   */
  static urlPatterns(patterns: RegExp[]): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const value = control.value;
      if (!value || !patterns.length) return null;
      
      const matchesPattern = patterns.some(p => p.test(value));
      if (!matchesPattern) {
        return {
          urlPatternMismatch: {
            message: 'La URL no cumple con el formato requerido'
          }
        };
      }
      return null;
    };
  }
  
  /**
   * Lista negra de dominios peligrosos
   */
  static blockedDomains(domains: string[]): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const value = control.value;
      if (!value) return null;
      
      try {
        const url = new URL(value);
        const hostname = url.hostname.toLowerCase();
        
        const isBlocked = domains.some(d => 
          hostname === d.toLowerCase() || 
          hostname.endsWith(`.${d.toLowerCase()}`)
        );
        
        if (isBlocked) {
          return {
            blockedDomain: {
              message: 'Este dominio no está permitido',
              domain: url.hostname
            }
          };
        }
        return null;
      } catch {
        return null;
      }
    };
  }
  
  // ============================================
  // UTILIDADES
  // ============================================
  
  /**
   * Formatea bytes a una cadena legible
   */
  static formatSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  }
  
  /**
   * Obtiene la extensión de un nombre de archivo
   */
  static getExtension(filename: string): string {
    const parts = filename.split('.');
    return parts.length > 1 ? parts.pop()?.toLowerCase() || '' : '';
  }
  
  /**
   * Verifica si un MIME type está permitido
   */
  static isMimeTypeAllowed(mimeType: string, allowedTypes: string[]): boolean {
    if (allowedTypes.includes('*/*')) return true;
    
    return allowedTypes.some(allowed => {
      if (allowed.endsWith('/*')) {
        // Wildcard: image/*, audio/*, etc.
        const category = allowed.replace('/*', '');
        return mimeType.startsWith(category);
      }
      return mimeType === allowed;
    });
  }
  
  /**
   * Verifica si una extensión está permitida
   */
  static isExtensionAllowed(extension: string, allowedExtensions: string[]): boolean {
    if (allowedExtensions.includes('*')) return true;
    
    const ext = extension.toLowerCase().replace('.', '');
    return allowedExtensions.some(e => 
      e.toLowerCase().replace('.', '') === ext
    );
  }
}
