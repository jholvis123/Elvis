import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../../core/services/auth.service';
import { NotificationService } from '../../../../core/services/notification.service';

@Component({
    selector: 'app-login',
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule, RouterLink],
    templateUrl: './login.component.html',
    styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {
    loginForm!: FormGroup;
    loading = false;
    errorMessage = '';

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

        this.loginForm = this.fb.group({
            email: ['', [Validators.required, Validators.email]],
            password: ['', [Validators.required, Validators.minLength(6)]]
        });
    }

    get email() {
        return this.loginForm.get('email');
    }

    get password() {
        return this.loginForm.get('password');
    }

    onSubmit(): void {
        if (this.loginForm.invalid) {
            this.markFormGroupTouched(this.loginForm);
            return;
        }

        this.loading = true;
        this.errorMessage = '';

        this.authService.login(this.loginForm.value).subscribe({
            next: () => {
                this.notificationService.success('¡Bienvenido! Sesión iniciada correctamente');
                // Redirigir: si hay URL guardada se usa, si no, los admin van al dashboard y el resto al home
                let redirectUrl = localStorage.getItem('redirectUrl');

                if (!redirectUrl) {
                    redirectUrl = this.authService.isAdmin ? '/admin/dashboard' : '/';
                }

                localStorage.removeItem('redirectUrl');
                this.router.navigate([redirectUrl]);
            },
            error: (error) => {
                this.loading = false;
                this.errorMessage = error.message || 'Error al iniciar sesión. Verifica tus credenciales.';
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
