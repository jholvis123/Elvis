
import { Component, inject, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';

import { CtfService } from '@core/services/ctf.service';
import { AttachmentService } from '@core/services/attachment.service';
import {
  CTF_DIFFICULTIES,
  CTFCategory,
  CTFChallengeForm,
  CTFAttachment,
  CATEGORY_ATTACHMENT_CONFIG
} from '@core/models/ctf.model';
import { CtfValidators } from '@core/validators/ctf.validators';

// Shared Components
import { FileUploadComponent } from '@shared/components/file-upload/file-upload.component';
import { UrlInputComponent } from '@shared/components/url-input/url-input.component';
import { CategorySelectorComponent } from '@shared/components/category-selector/category-selector.component';
import { DynamicListComponent } from '@shared/components/dynamic-list/dynamic-list.component';

@Component({
  selector: 'app-ctf-upload',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    FileUploadComponent,
    UrlInputComponent,
    CategorySelectorComponent,
    DynamicListComponent
  ],
  templateUrl: './ctf-upload.component.html',
  styleUrls: ['./ctf-upload.component.scss']
})
export class CtfUploadComponent implements OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);
  private readonly ctfService = inject(CtfService);
  private readonly attachmentService = inject(AttachmentService);
  private destroy$ = new Subject<void>();

  readonly difficulties = CTF_DIFFICULTIES;

  // Estado
  selectedCategory: CTFCategory | null = null;
  isSubmitting = false;
  submitError = '';
  fileAttachments: CTFAttachment[] = [];
  urlAttachment: string = '';

  // Formulario principal
  challengeForm: FormGroup = this.fb.group({
    title: ['', [
      Validators.required,
      Validators.minLength(CtfValidators.MIN_TITLE_LENGTH),
      Validators.maxLength(CtfValidators.MAX_TITLE_LENGTH)
    ]],
    description: ['', [
      Validators.required,
      Validators.minLength(CtfValidators.MIN_DESCRIPTION_LENGTH),
      Validators.maxLength(CtfValidators.MAX_DESCRIPTION_LENGTH)
    ]],
    category: ['', [Validators.required, CtfValidators.validCategory()]],
    difficulty: ['', Validators.required],
    platform: ['Web', [Validators.required, Validators.minLength(1), Validators.maxLength(100)]],
    points: [100, [Validators.required, CtfValidators.pointsRange()]],
    flag: ['', [Validators.required, CtfValidators.flag()]],
    skills: [[] as string[]],
    hints: [[] as string[]],
    isActive: [true]
  });

  constructor() {
    // Escuchar cambios en categoría
    this.challengeForm.get('category')?.valueChanges
      .pipe(takeUntil(this.destroy$))
      .subscribe((category: CTFCategory) => {
        this.onCategoryChange(category);
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // ============================================
  // GETTERS
  // ============================================

  get f() {
    return this.challengeForm.controls;
  }

  get requiresFiles(): boolean {
    return this.selectedCategory
      ? this.attachmentService.requiresFiles(this.selectedCategory)
      : false;
  }

  get requiresUrl(): boolean {
    return this.selectedCategory
      ? this.attachmentService.requiresUrl(this.selectedCategory)
      : false;
  }

  get supportsDocker(): boolean {
    return this.selectedCategory
      ? this.attachmentService.supportsDocker(this.selectedCategory)
      : false;
  }

  get categoryConfig() {
    return this.selectedCategory
      ? CATEGORY_ATTACHMENT_CONFIG[this.selectedCategory]
      : null;
  }

  get flagPreview(): string {
    const flag = this.challengeForm.get('flag')?.value || '';
    return flag || 'flag{tu_flag_aqui}';
  }

  get hasAttachments(): boolean {
    return this.fileAttachments.length > 0 || !!this.urlAttachment;
  }

  get attachmentError(): string {
    if (!this.selectedCategory) return '';

    const config = this.categoryConfig;
    if (!config) return '';

    // Verificar si requiere adjuntos pero no tiene
    if (config.requiredTypes.includes('file') && this.fileAttachments.length === 0) {
      return 'Esta categoría requiere al menos un archivo adjunto';
    }

    if (config.requiredTypes.includes('url') && !this.urlAttachment && !config.requiredTypes.includes('file')) {
      return 'Esta categoría requiere una URL';
    }

    return '';
  }

  // ============================================
  // MANEJADORES DE EVENTOS
  // ============================================

  onCategoryChange(category: CTFCategory): void {
    this.selectedCategory = category;
    // Limpiar adjuntos al cambiar categoría
    this.fileAttachments = [];
    this.urlAttachment = '';
  }

  onDifficultyChange(): void {
    const difficulty = this.challengeForm.get('difficulty')?.value;
    const diffInfo = this.difficulties.find(d => d.value === difficulty);
    if (diffInfo) {
      this.challengeForm.patchValue({ points: diffInfo.points });
    }
  }

  onFilesUploaded(attachments: CTFAttachment[]): void {
    this.fileAttachments = attachments;
  }

  onUrlChange(url: string): void {
    this.urlAttachment = url;
  }

  onSkillsChange(skills: string[]): void {
    this.challengeForm.patchValue({ skills });
  }

  onHintsChange(hints: string[]): void {
    this.challengeForm.patchValue({ hints });
  }

  // ============================================
  // HELPERS DE ERROR
  // ============================================

  getErrorMessage(controlName: string): string {
    const control = this.challengeForm.get(controlName);
    if (!control) return '';
    return CtfValidators.getErrorMessage(control);
  }

  hasError(controlName: string): boolean {
    const control = this.challengeForm.get(controlName);
    return !!control && control.touched && control.invalid;
  }

  // ============================================
  // ENVÍO DEL FORMULARIO
  // ============================================

  async onSubmit(): Promise<void> {
    // Validar formulario
    if (this.challengeForm.invalid) {
      this.challengeForm.markAllAsTouched();
      return;
    }

    // Validar adjuntos según categoría
    if (this.attachmentError) {
      this.submitError = this.attachmentError;
      return;
    }

    this.isSubmitting = true;
    this.submitError = '';

    try {
      // Construir objeto de adjuntos
      const attachments: CTFAttachment[] = [...this.fileAttachments];

      if (this.urlAttachment) {
        attachments.push(
          this.attachmentService.createUrlAttachment(this.urlAttachment)
        );
      }

      const formValue: CTFChallengeForm = {
        ...this.challengeForm.value,
        attachments
      };

      await this.ctfService.createChallenge(formValue);
      this.router.navigate(['/ctf']);

    } catch (error) {
      this.submitError = 'Error al crear el reto. Intenta de nuevo.';
      console.error('Error creating challenge:', error);
    } finally {
      this.isSubmitting = false;
    }
  }
}
