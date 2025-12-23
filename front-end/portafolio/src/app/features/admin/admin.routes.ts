import { Routes } from '@angular/router';
import { AuthGuard } from '../../core/guards/auth.guard';
import { AdminGuard } from '../../core/guards/admin.guard';

export const ADMIN_ROUTES: Routes = [
    {
        path: '',
        canActivate: [AuthGuard, AdminGuard],
        children: [
            {
                path: '',
                redirectTo: 'dashboard',
                pathMatch: 'full'
            },
            {
                path: 'dashboard',
                loadComponent: () =>
                    import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent)
            },
            {
                path: 'projects',
                loadComponent: () =>
                    import('./pages/project-manager/project-manager.component').then(m => m.ProjectManagerComponent)
            },
            {
                path: 'writeups',
                loadComponent: () =>
                    import('./pages/writeup-manager/writeup-manager.component').then(m => m.WriteupManagerComponent)
            },
            {
                path: 'ctfs',
                loadComponent: () =>
                    import('./pages/ctf-manager/ctf-manager.component').then(m => m.CtfManagerComponent)
            }
        ]
    }
];
