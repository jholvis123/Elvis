import { Injectable, inject } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, Router, UrlTree } from '@angular/router';
import { Observable, map } from 'rxjs';
import { AuthService } from '../services/auth.service';

@Injectable({
    providedIn: 'root'
})
export class AdminGuard implements CanActivate {
    private authService = inject(AuthService);
    private router = inject(Router);

    canActivate(
        _route: ActivatedRouteSnapshot,
        _state: RouterStateSnapshot
    ): Observable<boolean | UrlTree> {
        // is_admin solo oculta UI (navbar). La autorización real la hace el backend.
        // El guard espera /auth/me para no usar un flag local obsoleto.
        return this.authService.checkAuthStatus().pipe(
            map(status => {
                if (!status.authenticated) {
                    return this.router.createUrlTree(['/auth/login']);
                }
                if (!status.user?.is_admin) {
                    return this.router.createUrlTree(['/']);
                }
                return true;
            })
        );
    }
}
