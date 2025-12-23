import { Routes } from '@angular/router';
import { AuthGuard } from '../../core/guards/auth.guard';
import { AdminGuard } from '../../core/guards/admin.guard';

export const WRITEUPS_ROUTES: Routes = [
    {
        path: '',
        loadComponent: () =>
            import('./pages/writeup-list/writeup-list.component').then(m => m.WriteupListComponent)
    },
    {
        path: 'new',
        canActivate: [AuthGuard, AdminGuard],
        loadComponent: () =>
            import('./pages/writeup-form/writeup-form.component').then(m => m.WriteupFormComponent)
    },
    {
        path: ':id',
        loadComponent: () =>
            import('./pages/writeup-detail/writeup-detail.component').then(m => m.WriteupDetailComponent)
    },
    {
        path: ':id/edit',
        canActivate: [AuthGuard, AdminGuard],
        loadComponent: () =>
            import('./pages/writeup-form/writeup-form.component').then(m => m.WriteupFormComponent)
    }
];
