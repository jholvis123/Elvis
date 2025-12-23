import { Component, Input, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';

import { ContactService } from '@core/services';

@Component({
  selector: 'app-contact-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './contact-form.component.html',
  styleUrls: ['./contact-form.component.scss']
})
export class ContactFormComponent {
  private readonly fb = inject(FormBuilder);
  private readonly contactService = inject(ContactService);

  @Input() projectTypes: { value: string; label: string }[] = [];

  contactForm: FormGroup = this.fb.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    email: ['', [Validators.required, Validators.email]],
    projectType: ['', Validators.required],
    message: ['', [Validators.required, Validators.minLength(10)]]
  });

  isSubmitting = false;
  submitSuccess = false;
  submitError = false;

  onSubmit(): void {
    if (this.contactForm.invalid) {
      this.contactForm.markAllAsTouched();
      return;
    }

    this.isSubmitting = true;
    this.submitError = false;

    // Usar el Observable directamente para enviar a la API
    this.contactService.submitContact(this.contactForm.value).subscribe({
      next: () => {
        this.submitSuccess = true;
        this.contactForm.reset();
        this.isSubmitting = false;
        setTimeout(() => this.submitSuccess = false, 5000);
      },
      error: (err) => {
        console.error('Error enviando contacto:', err);
        this.submitError = true;
        this.isSubmitting = false;
      }
    });
  }

  get f() {
    return this.contactForm.controls;
  }
}
