/**
 * CTF Custom Validators
 * Validadores personalizados para el módulo CTF
 */

import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';
import { 
  CTFCategory, 
  CTFAttachment, 
  CATEGORY_ATTACHMENT_CONFIG 
} from '@core/models/ctf.model';

export class CtfValidators {
  
  // ============================================
  // CONSTANTES
  // ============================================
  
  static readonly FLAG_PATTERN = /^flag\{[\w\-_!@#$%^&*()+=.]+\}$/;
  static readonly MIN_TITLE_LENGTH = 5;
  static readonly MAX_TITLE_LENGTH = 100;
  static readonly MIN_DESCRIPTION_LENGTH = 20;
  static readonly MAX_DESCRIPTION_LENGTH = 2000;
  static readonly MIN_SKILL_LENGTH = 2;
  static readonly MAX_SKILLS = 10;
  static readonly MIN_HINT_LENGTH = 10;
  static readonly MAX_HINTS = 5;
  
  // ============================================
  // VALIDADORES DE FLAG
  // ============================================
  
  /**
   * Valida el formato de la flag: flag{contenido}
   */
  static flag(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const value = control.value;
      if (!value) return null; // Dejar que required maneje esto
      
      if (!this.FLAG_PATTERN.test(value)) {
        return { 
          invalidFlag: { 
            message: 'La flag debe tener el formato: flag{contenido}',
            pattern: 'flag{...}'
          } 
        };
      }
      return null;
    };
  }
  
  /**
   * Valida que la flag no contenga espacios
   */
  static flagNoSpaces(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const value = control.value;
      if (!value) return null;
      
      if (value.includes(' ')) {
        return { flagHasSpaces: { message: 'La flag no puede contener espacios' } };
      }
      return null;
    };
  }
  
  // ============================================
  // VALIDADORES DE CATEGORÍA Y ADJUNTOS
  // ============================================
  
  /**
   * Valida que los adjuntos cumplan con los requisitos de la categoría
   */
  static categoryAttachments(category: CTFCategory): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const attachments = control.value as CTFAttachment[];
      const config = CATEGORY_ATTACHMENT_CONFIG[category];
      
      if (!config) return null;
      
      // Si la categoría requiere adjuntos pero no hay ninguno
      if (config.requiredTypes.length > 0 && (!attachments || attachments.length === 0)) {
        const typeLabels = config.requiredTypes.map(t => {
          switch(t) {
            case 'file': return 'archivo';
            case 'url': return 'URL';
            case 'docker': return 'Docker';
            default: return t;
          }
        }).join(' o ');
        
        return { 
          requiredAttachment: { 
            message: `Esta categoría requiere al menos un ${typeLabels}`,
            requiredTypes: config.requiredTypes
          } 
        };
      }
      
      // Validar cantidad máxima
      if (attachments && attachments.length > config.maxFiles && config.maxFiles > 0) {
        return {
          maxAttachments: {
            message: `Máximo ${config.maxFiles} adjuntos permitidos`,
            max: config.maxFiles,
            actual: attachments.length
          }
        };
      }
      
      return null;
    };
  }
  
  /**
   * Valida que se haya seleccionado una categoría válida
   */
  static validCategory(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const value = control.value as CTFCategory;
      if (!value) return null;
      
      const validCategories = Object.keys(CATEGORY_ATTACHMENT_CONFIG);
      if (!validCategories.includes(value)) {
        return { invalidCategory: { message: 'Categoría no válida' } };
      }
      return null;
    };
  }
  
  // ============================================
  // VALIDADORES DE ARRAYS (SKILLS/HINTS)
  // ============================================
  
  /**
   * Valida el tamaño mínimo de un array
   */
  static minArrayLength(min: number): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const arr = control.value as unknown[];
      if (!arr || arr.length < min) {
        return { 
          minArrayLength: { 
            message: `Se requieren al menos ${min} elementos`,
            min,
            actual: arr?.length || 0
          } 
        };
      }
      return null;
    };
  }
  
  /**
   * Valida el tamaño máximo de un array
   */
  static maxArrayLength(max: number): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const arr = control.value as unknown[];
      if (arr && arr.length > max) {
        return { 
          maxArrayLength: { 
            message: `Máximo ${max} elementos permitidos`,
            max,
            actual: arr.length
          } 
        };
      }
      return null;
    };
  }
  
  /**
   * Valida que no haya elementos duplicados en un array de strings
   */
  static noDuplicates(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const arr = control.value as string[];
      if (!arr || arr.length === 0) return null;
      
      const unique = new Set(arr.map(s => s.toLowerCase().trim()));
      if (unique.size !== arr.length) {
        return { duplicates: { message: 'No se permiten elementos duplicados' } };
      }
      return null;
    };
  }
  
  // ============================================
  // VALIDADORES DE PUNTOS
  // ============================================
  
  /**
   * Valida que los puntos estén en el rango permitido
   */
  static pointsRange(min: number = 10, max: number = 10000): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const value = control.value;
      if (value === null || value === undefined) return null;
      
      if (value < min || value > max) {
        return {
          pointsRange: {
            message: `Los puntos deben estar entre ${min} y ${max}`,
            min,
            max,
            actual: value
          }
        };
      }
      return null;
    };
  }
  
  // ============================================
  // HELPERS
  // ============================================
  
  /**
   * Obtiene el mensaje de error de un control
   */
  static getErrorMessage(control: AbstractControl): string {
    if (!control.errors) return '';
    
    const errors = control.errors;
    
    // Errores personalizados con mensaje
    for (const key of Object.keys(errors)) {
      if (errors[key]?.message) {
        return errors[key].message;
      }
    }
    
    // Errores estándar de Angular
    if (errors['required']) return 'Este campo es requerido';
    if (errors['minlength']) {
      return `Mínimo ${errors['minlength'].requiredLength} caracteres`;
    }
    if (errors['maxlength']) {
      return `Máximo ${errors['maxlength'].requiredLength} caracteres`;
    }
    if (errors['min']) return `El valor mínimo es ${errors['min'].min}`;
    if (errors['max']) return `El valor máximo es ${errors['max'].max}`;
    if (errors['email']) return 'Email inválido';
    if (errors['pattern']) return 'Formato inválido';
    
    return 'Error de validación';
  }
}
