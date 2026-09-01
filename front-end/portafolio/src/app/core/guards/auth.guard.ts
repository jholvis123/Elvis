import { Injectable, inject } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, Router, UrlTree } from '@angular/router';
import { Observable, map } from 'rxjs';
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
    ): Observable<boolean | UrlTree> {
        return this.authService.checkAuthStatus().pipe(
            map(status => {
                if (status.authenticated) {
                    return true;
                }
                localStorage.setItem('redirectUrl', state.url);
                return this.router.createUrlTree(['/auth/login']);
            })
        );
    }
}
