/**
 * URL Input Component
 * Input de URL con validación y ControlValueAccessor
 */

import { 
  Component, 
  Input, 
  Output, 
  EventEmitter,
  forwardRef,
  OnDestroy
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { 
  ControlValueAccessor, 
  NG_VALUE_ACCESSOR, 
  FormControl,
  ReactiveFormsModule,
  Validators
} from '@angular/forms';
import { FileValidators } from '@core/validators/file.validators';
import { Subject, debounceTime, takeUntil } from 'rxjs';

@Component({
  selector: 'app-url-input',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './url-input.component.html',
  styleUrls: ['./url-input.component.scss'],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => UrlInputComponent),
      multi: true
    }
  ]
})
export class UrlInputComponent implements ControlValueAccessor, OnDestroy {
  // Configuración
  @Input() label: string = 'URL';
  @Input() placeholder: string = 'https://ejemplo.com';
  @Input() hint: string = '';
  @Input() required: boolean = false;
  @Input() httpsOnly: boolean = false;
  @Input() patterns: RegExp[] = [];
  @Input() disabled: boolean = false;
  
  // Eventos
  @Output() urlChange = new EventEmitter<string>();
  @Output() validUrl = new EventEmitter<boolean>();
  
  // Estado
  urlControl = new FormControl('');
  isValidating = false;
  validationResult: { valid: boolean; message: string } | null = null;
  
  private destroy$ = new Subject<void>();
  private onChange: (value: string) => void = () => {};
  private onTouched: () => void = () => {};
  
  constructor() {
    // Debounce validación mientras escribe
    this.urlControl.valueChanges
      .pipe(
        debounceTime(300),
        takeUntil(this.destroy$)
      )
      .subscribe(value => {
        this.validateUrl(value || '');
        this.onChange(value || '');
        this.urlChange.emit(value || '');
      });
  }
  
  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
  
  // ============================================
  // VALIDACIÓN
  // ============================================
  
  private validateUrl(url: string): void {
    if (!url) {
      this.validationResult = this.required 
        ? { valid: false, message: 'La URL es requerida' }
        : null;
      this.validUrl.emit(!this.required);
      return;
    }
    
    this.isValidating = true;
    
    // Validar formato básico
    try {
      const parsed = new URL(url);
      
      // Validar protocolo
      if (!['http:', 'https:'].includes(parsed.protocol)) {
        this.validationResult = { valid: false, message: 'Solo HTTP/HTTPS permitido' };
        this.validUrl.emit(false);
        return;
      }
      
      // Validar HTTPS si es requerido
      if (this.httpsOnly && parsed.protocol !== 'https:') {
        this.validationResult = { valid: false, message: 'La URL debe usar HTTPS' };
        this.validUrl.emit(false);
        return;
      }
      
      // Validar patrones
      if (this.patterns.length > 0) {
        const matchesPattern = this.patterns.some(p => p.test(url));
        if (!matchesPattern) {
          this.validationResult = { valid: false, message: 'URL no cumple el formato requerido' };
          this.validUrl.emit(false);
          return;
        }
      }
      
      // URL válida
      this.validationResult = { valid: true, message: 'URL válida' };
      this.validUrl.emit(true);
      
    } catch {
      this.validationResult = { valid: false, message: 'Formato de URL inválido' };
      this.validUrl.emit(false);
    } finally {
      this.isValidating = false;
    }
  }
  
  // ============================================
  // HELPERS
  // ============================================
  
  get showError(): boolean {
    return this.urlControl.touched && this.validationResult?.valid === false;
  }
  
  get showSuccess(): boolean {
    return !!this.urlControl.value && this.validationResult?.valid === true;
  }
  
  onBlur(): void {
    this.onTouched();
    this.urlControl.markAsTouched();
  }
  
  clearUrl(): void {
    this.urlControl.setValue('');
    this.validationResult = null;
    this.onChange('');
    this.onTouched();
  }
  
  // ============================================
  // CONTROL VALUE ACCESSOR
  // ============================================
  
  writeValue(value: string): void {
    this.urlControl.setValue(value || '', { emitEvent: false });
    if (value) {
      this.validateUrl(value);
    }
  }
  
  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }
  
  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }
  
  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
    if (isDisabled) {
      this.urlControl.disable();
    } else {
      this.urlControl.enable();
    }
  }
}
