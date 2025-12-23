import { Routes } from '@angular/router';
import { AuthGuard } from '../../core/guards/auth.guard';
import { AdminGuard } from '../../core/guards/admin.guard';

export const PROJECTS_ROUTES: Routes = [
    {
        path: '',
        loadComponent: () =>
            import('./pages/project-list/project-list.component').then(m => m.ProjectListComponent)
    },
    {
        path: 'new',
        canActivate: [AuthGuard, AdminGuard],
        loadComponent: () =>
            import('./pages/project-form/project-form.component').then(m => m.ProjectFormComponent)
    },
    {
        path: ':id',
        loadComponent: () =>
            import('./pages/project-detail/project-detail.component').then(m => m.ProjectDetailComponent)
    },
    {
        path: ':id/edit',
        canActivate: [AuthGuard, AdminGuard],
        loadComponent: () =>
            import('./pages/project-form/project-form.component').then(m => m.ProjectFormComponent)
    }
];
