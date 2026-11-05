import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
    AbstractControl,
    FormBuilder,
    ReactiveFormsModule,
    ValidationErrors,
    Validators
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthService, PLAYER_ALIAS_PATTERN } from '../../../../core/services/auth.service';
import { NotificationService } from '../../../../core/services/notification.service';

function passwordsMatch(group: AbstractControl): ValidationErrors | null {
    const password = group.get('password')?.value;
    const confirm = group.get('confirm')?.value;
    return password && confirm && password !== confirm ? { mismatch: true } : null;
}

/**
 * Registro de jugador del CTF: solo alias + contraseña (POST /auth/register-player).
 * Si el backend tiene ALLOW_PLAYER_REGISTER=false responde 403 y se muestra aviso.
 */
@Component({
    selector: 'app-register',
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule, RouterLink],
    templateUrl: './register.component.html',
    styleUrls: ['./register.component.scss']
})
export class RegisterComponent implements OnInit {
    private readonly fb = inject(FormBuilder);
    private readonly authService = inject(AuthService);
    private readonly router = inject(Router);
    private readonly notifications = inject(NotificationService);

    loading = false;
    errorMessage = '';
    registrationDisabled = false;

    readonly form = this.fb.group(
        {
            username: ['', [Validators.required, Validators.pattern(PLAYER_ALIAS_PATTERN)]],
            password: ['', [Validators.required, Validators.minLength(8), Validators.maxLength(72)]],
            confirm: ['', [Validators.required]]
        },
        { validators: passwordsMatch }
    );

    ngOnInit(): void {
        if (this.authService.isAuthenticated) {
            this.router.navigate(['/ctf']);
        }
    }

    get username() { return this.form.get('username'); }
    get password() { return this.form.get('password'); }
    get confirm() { return this.form.get('confirm'); }

    onSubmit(): void {
        if (this.form.invalid) {
            this.form.markAllAsTouched();
            return;
        }
        this.loading = true;
        this.errorMessage = '';

        const { username, password } = this.form.getRawValue();
        this.authService.registerPlayer({ username: (username ?? '').trim(), password: password ?? '' }).subscribe({
            next: () => {
                this.notifications.success('¡Alias creado! Ya puedes resolver retos y aparecer en el ranking.');
                this.router.navigate(['/ctf']);
            },
            error: (error: HttpErrorResponse) => {
                this.loading = false;
                if (error.status === 403) {
                    this.registrationDisabled = true;
                    this.errorMessage = 'El registro de jugadores está desactivado en este momento.';
                } else if (error.status === 400) {
                    this.errorMessage = 'Ese alias ya está en uso. Prueba con otro.';
                } else if (error.status === 422) {
                    this.errorMessage = 'Alias no válido o reservado. Usa 3-30 letras, números, - o _.';
                } else if (error.status === 429) {
                    this.errorMessage = 'Demasiados registros desde tu conexión. Inténtalo más tarde.';
                } else {
                    this.errorMessage = 'No se pudo crear el alias. Inténtalo de nuevo.';
                }
            },
            complete: () => {
                this.loading = false;
            }
        });
    }
}
