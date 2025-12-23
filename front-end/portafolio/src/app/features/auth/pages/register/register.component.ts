import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../../core/services/auth.service';
import { NotificationService } from '../../../../core/services/notification.service';

@Component({
    selector: 'app-register',
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule, RouterLink],
    templateUrl: './register.component.html',
    styleUrls: ['./register.component.scss']
})
export class RegisterComponent implements OnInit {
    registerForm!: FormGroup;
    loading = false;
    errorMessage = '';
    successMessage = '';

    constructor(
        private fb: FormBuilder,
        private authService: AuthService,
        private router: Router,
        private notificationService: NotificationService
    ) { }

    ngOnInit(): void {
        // Si ya está autenticado, redirigir
        if (this.authService.isAuthenticated) {
            this.router.navigate(['/']);
        }

        this.registerForm = this.fb.group({
            username: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(50)]],
            email: ['', [Validators.required, Validators.email]],
            password: ['', [Validators.required, Validators.minLength(6)]],
            confirmPassword: ['', [Validators.required]]
        }, {
            validators: this.passwordMatchValidator
        });
    }

    get username() {
        return this.registerForm.get('username');
    }

    get email() {
        return this.registerForm.get('email');
    }

    get password() {
        return this.registerForm.get('password');
    }

    get confirmPassword() {
        return this.registerForm.get('confirmPassword');
    }

    passwordMatchValidator(form: FormGroup) {
        const password = form.get('password');
        const confirmPassword = form.get('confirmPassword');

        if (password && confirmPassword && password.value !== confirmPassword.value) {
            confirmPassword.setErrors({ passwordMismatch: true });
            return { passwordMismatch: true };
        }

        return null;
    }

    onSubmit(): void {
        if (this.registerForm.invalid) {
            this.markFormGroupTouched(this.registerForm);
            return;
        }

        this.loading = true;
        this.errorMessage = '';
        this.successMessage = '';

        const { username, email, password } = this.registerForm.value;

        this.authService.register({ username, email, password }).subscribe({
            next: () => {
                this.notificationService.success('¡Cuenta creada exitosamente! Bienvenido');
                this.successMessage = 'Registro exitoso. Redirigiendo...';

                // Auto-login después del registro
                this.authService.login({ email, password }).subscribe({
                    next: () => {
                        setTimeout(() => {
                            this.router.navigate(['/']);
                        }, 1000);
                    },
                    error: () => {
                        this.notificationService.info('Por favor inicia sesión con tus credenciales');
                        setTimeout(() => {
                            this.router.navigate(['/auth/login']);
                        }, 1000);
                    }
                });
            },
            error: (error) => {
                this.loading = false;
                this.errorMessage = error.message || 'Error al registrarse. Intenta nuevamente.';
                this.notificationService.error(this.errorMessage);
            },
            complete: () => {
                this.loading = false;
            }
        });
    }

    private markFormGroupTouched(formGroup: FormGroup): void {
        Object.keys(formGroup.controls).forEach(key => {
            const control = formGroup.get(key);
            control?.markAsTouched();
        });
    }
}
