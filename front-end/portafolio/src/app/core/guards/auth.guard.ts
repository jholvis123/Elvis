import { Injectable, inject } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Injectable({
    providedIn: 'root'
})
export class AuthGuard implements CanActivate {
    private authService = inject(AuthService);
    private router = inject(Router);

    canActivate(
        route: ActivatedRouteSnapshot,
        state: RouterStateSnapshot
    ): boolean {
        if (this.authService.isAuthenticated) {
            return true;
        }

        // Guardar la URL a la que intentaba acceder
        localStorage.setItem('redirectUrl', state.url);

        // Redirigir al login
        this.router.navigate(['/auth/login']);
        return false;
    }
}
