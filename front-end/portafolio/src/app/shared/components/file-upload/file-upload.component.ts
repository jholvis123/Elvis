/**
 * File Upload Component
 * Componente reutilizable para subida de archivos con drag & drop
 */

import { 
  Component, 
  Input, 
  Output, 
  EventEmitter, 
  ElementRef, 
  ViewChild,
  inject,
  forwardRef 
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { AttachmentService } from '@core/services/attachment.service';
import { CTFCategory, CTFAttachment, ValidationResult } from '@core/models/ctf.model';
import { FileValidators } from '@core/validators/file.validators';

@Component({
  selector: 'app-file-upload',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './file-upload.component.html',
  styleUrls: ['./file-upload.component.scss'],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => FileUploadComponent),
      multi: true
    }
  ]
})
export class FileUploadComponent implements ControlValueAccessor {
  @ViewChild('fileInput') fileInput!: ElementRef<HTMLInputElement>;
  
  // Configuración por categoría
  @Input() category: CTFCategory | null = null;
  
  // Configuración manual (alternativa a categoría)
  @Input() accept: string = '*/*';
  @Input() maxSize: number = 10 * 1024 * 1024; // 10MB default
  @Input() maxFiles: number = 5;
  @Input() multiple: boolean = true;
  
  // UI
  @Input() label: string = 'Archivos adjuntos';
  @Input() hint: string = '';
  @Input() disabled: boolean = false;
  
  // Eventos
  @Output() filesSelected = new EventEmitter<File[]>();
  @Output() fileRemoved = new EventEmitter<number>();
  @Output() uploadError = new EventEmitter<string>();
  @Output() filesUploaded = new EventEmitter<CTFAttachment[]>();
  
  private readonly attachmentService = inject(AttachmentService);
  
  // Estado interno
  files: File[] = [];
  uploadedAttachments: CTFAttachment[] = [];
  isDragging = false;
  isUploading = false;
  errors: string[] = [];
  
  // ControlValueAccessor
  private onChange: (value: CTFAttachment[]) => void = () => {};
  private onTouched: () => void = () => {};
  
  // ============================================
  // GETTERS COMPUTADOS
  // ============================================
  
  get effectiveAccept(): string {
    if (this.category) {
      return this.attachmentService.getAcceptString(this.category);
    }
    return this.accept;
  }
  
  get effectiveMaxSize(): number {
    if (this.category) {
      const config = this.attachmentService.getConfigForCategory(this.category);
      return config?.maxFileSize || this.maxSize;
    }
    return this.maxSize;
  }
  
  get effectiveMaxFiles(): number {
    if (this.category) {
      const config = this.attachmentService.getConfigForCategory(this.category);
      return config?.maxFiles || this.maxFiles;
    }
    return this.maxFiles;
  }
  
  get maxSizeFormatted(): string {
    return FileValidators.formatSize(this.effectiveMaxSize);
  }
  
  get allowedExtensions(): string {
    if (this.category) {
      return this.attachmentService.getAllowedExtensionsString(this.category);
    }
    return 'Cualquier archivo';
  }
  
  get canAddMore(): boolean {
    return this.files.length < this.effectiveMaxFiles;
  }
  
  get totalSize(): number {
    return this.files.reduce((sum, f) => sum + f.size, 0);
  }
  
  get totalSizeFormatted(): string {
    return FileValidators.formatSize(this.totalSize);
  }
  
  // ============================================
  // DRAG & DROP
  // ============================================
  
  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    if (!this.disabled) {
      this.isDragging = true;
    }
  }
  
  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }
  
  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
    
    if (this.disabled) return;
    
    const droppedFiles = event.dataTransfer?.files;
    if (droppedFiles) {
      this.handleFiles(Array.from(droppedFiles));
    }
  }
  
  // ============================================
  // SELECCIÓN DE ARCHIVOS
  // ============================================
  
  openFileDialog(): void {
    if (!this.disabled && this.canAddMore) {
      this.fileInput.nativeElement.click();
    }
  }
  
  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files) {
      this.handleFiles(Array.from(input.files));
    }
    // Reset input para permitir seleccionar el mismo archivo
    input.value = '';
  }
  
  private handleFiles(newFiles: File[]): void {
    this.errors = [];
    
    // Verificar límite de archivos
    const availableSlots = this.effectiveMaxFiles - this.files.length;
    if (newFiles.length > availableSlots) {
      this.errors.push(`Solo puedes agregar ${availableSlots} archivo(s) más`);
      newFiles = newFiles.slice(0, availableSlots);
    }
    
    // Validar cada archivo
    const validFiles: File[] = [];
    
    for (const file of newFiles) {
      const validation = this.validateFile(file);
      if (validation.valid) {
        // Verificar duplicados
        const isDuplicate = this.files.some(f => 
          f.name === file.name && f.size === file.size
        );
        
        if (isDuplicate) {
          this.errors.push(`"${file.name}" ya está agregado`);
        } else {
          validFiles.push(file);
        }
      } else {
        this.errors.push(`${file.name}: ${validation.errors.join(', ')}`);
      }
    }
    
    if (validFiles.length > 0) {
      this.files = [...this.files, ...validFiles];
      this.filesSelected.emit(validFiles);
      this.onTouched();
    }
    
    if (this.errors.length > 0) {
      this.uploadError.emit(this.errors.join('\n'));
    }
  }
  
  private validateFile(file: File): ValidationResult {
    if (this.category) {
      return this.attachmentService.validateFile(file, this.category);
    }
    
    // Validación manual
    const errors: string[] = [];
    
    if (file.size > this.effectiveMaxSize) {
      errors.push(`Demasiado grande (máx: ${this.maxSizeFormatted})`);
    }
    
    return { valid: errors.length === 0, errors };
  }
  
  // ============================================
  // GESTIÓN DE ARCHIVOS
  // ============================================
  
  removeFile(index: number): void {
    this.files.splice(index, 1);
    this.files = [...this.files];
    this.fileRemoved.emit(index);
    this.onTouched();
    
    // También remover del array de subidos si existe
    if (this.uploadedAttachments[index]) {
      this.uploadedAttachments.splice(index, 1);
      this.updateValue();
    }
  }
  
  clearAll(): void {
    this.files = [];
    this.uploadedAttachments = [];
    this.errors = [];
    this.updateValue();
    this.onTouched();
  }
  
  // ============================================
  // UPLOAD
  // ============================================
  
  async uploadAll(): Promise<void> {
    if (!this.category || this.files.length === 0 || this.isUploading) return;
    
    this.isUploading = true;
    this.errors = [];
    
    try {
      const results = await this.attachmentService.uploadFiles(this.files, this.category);
      
      const successful: CTFAttachment[] = [];
      
      results.forEach((result, index) => {
        if (result.success && result.attachment) {
          successful.push(result.attachment);
        } else {
          this.errors.push(`${this.files[index].name}: ${result.error}`);
        }
      });
      
      this.uploadedAttachments = successful;
      this.updateValue();
      this.filesUploaded.emit(successful);
      
    } catch (error) {
      this.errors.push('Error al subir archivos');
      this.uploadError.emit('Error al subir archivos');
    } finally {
      this.isUploading = false;
    }
  }
  
  // ============================================
  // CONTROL VALUE ACCESSOR
  // ============================================
  
  writeValue(value: CTFAttachment[]): void {
    this.uploadedAttachments = value || [];
  }
  
  registerOnChange(fn: (value: CTFAttachment[]) => void): void {
    this.onChange = fn;
  }
  
  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }
  
  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }
  
  private updateValue(): void {
    this.onChange(this.uploadedAttachments);
  }
  
  // ============================================
  // UTILIDADES
  // ============================================
  
  getFileIcon(file: File): string {
    const type = file.type;
    if (type.startsWith('image/')) return '🖼️';
    if (type.startsWith('audio/')) return '🎵';
    if (type.startsWith('video/')) return '🎬';
    if (type.includes('pdf')) return '📄';
    if (type.includes('zip') || type.includes('tar') || type.includes('rar')) return '📦';
    if (type.includes('executable') || type.includes('x-msdownload')) return '⚙️';
    return '📎';
  }
  
  formatSize(bytes: number): string {
    return FileValidators.formatSize(bytes);
  }
}
