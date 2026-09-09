import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../../core/services/auth.service';

/**
 * Public register is disabled (backend #42 / CICLO A Pages honest).
 * Route kept so deep links do not 404; UI explains and points to login.
 */
@Component({
    selector: 'app-register',
    standalone: true,
    imports: [CommonModule, RouterLink],
    templateUrl: './register.component.html',
    styleUrls: ['./register.component.scss']
})
export class RegisterComponent implements OnInit {
    private readonly authService = inject(AuthService);
    private readonly router = inject(Router);

    /** Always false — public register off. */
    readonly registrationEnabled = false;

    ngOnInit(): void {
        if (this.authService.isAuthenticated) {
            this.router.navigate(['/']);
        }
    }
}
