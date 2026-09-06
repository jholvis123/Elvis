import { Component, Input, OnInit, OnChanges, SimpleChanges, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';

import { ContactService, ApiAvailabilityService } from '@core/services';
import { IconComponent } from '@shared/icons/icon.component';

@Component({
  selector: 'app-contact-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, IconComponent],
  templateUrl: './contact-form.component.html',
  styleUrls: ['./contact-form.component.scss']
})
export class ContactFormComponent implements OnInit, OnChanges {
  private readonly fb = inject(FormBuilder);
  private readonly contactService = inject(ContactService);
  private readonly apiAvailability = inject(ApiAvailabilityService);

  @Input() projectTypes: { value: string; label: string }[] = [];
  @Input() apiUnavailable = false;

  contactForm: FormGroup = this.fb.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    email: ['', [Validators.required, Validators.email]],
    projectType: ['', Validators.required],
    message: ['', [Validators.required, Validators.minLength(10)]]
  });

  isSubmitting = false;
  submitSuccess = false;
  submitError = false;

  get isBlocked(): boolean {
    return this.apiUnavailable || !this.apiAvailability.isApiAvailable();
  }

  ngOnInit(): void {
    this.applyBlockedState();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['apiUnavailable']) {
      this.applyBlockedState();
    }
  }

  private applyBlockedState(): void {
    if (this.isBlocked) {
      this.contactForm.disable({ emitEvent: false });
      this.submitSuccess = false;
    } else {
      this.contactForm.enable({ emitEvent: false });
    }
  }

  onSubmit(): void {
    if (this.isBlocked) {
      this.submitSuccess = false;
      this.submitError = false;
      return;
    }

    if (this.contactForm.invalid) {
      this.contactForm.markAllAsTouched();
      return;
    }

    this.isSubmitting = true;
    this.submitError = false;
    this.submitSuccess = false;

    this.contactService.submitContact(this.contactForm.value).subscribe({
      next: () => {
        this.submitSuccess = true;
        this.contactForm.reset();
        this.isSubmitting = false;
        setTimeout(() => this.submitSuccess = false, 5000);
      },
      error: (err) => {
        console.error('Error enviando contacto:', err);
        this.apiAvailability.noteRequestFailure(err);
        this.submitError = true;
        this.submitSuccess = false;
        this.isSubmitting = false;
      }
    });
  }

  get f() {
    return this.contactForm.controls;
  }
}
