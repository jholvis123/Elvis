import { Routes } from '@angular/router';
import { MainLayoutComponent } from './core/layout/main-layout.component';
import { AuthGuard } from './core/guards/auth.guard';
import { AdminGuard } from './core/guards/admin.guard';

export const routes: Routes = [
  // Rutas de autenticación (sin layout)
  {
    path: 'auth',
    loadChildren: () => import('./features/auth/auth.routes').then(m => m.AUTH_ROUTES)
  },

  // Rutas principales con layout
  {
    path: '',
    component: MainLayoutComponent,
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./features/home/home.component').then(m => m.HomeComponent)
      },
      {
        path: 'ctf',
        loadChildren: () =>
          import('./features/ctf/ctf.routes').then(m => m.CTF_ROUTES)
      },
      {
        path: 'projects',
        loadChildren: () =>
          import('./features/projects/projects.routes').then(m => m.PROJECTS_ROUTES)
      },
      {
        path: 'writeups',
        loadChildren: () =>
          import('./features/writeups/writeups.routes').then(m => m.WRITEUPS_ROUTES)
      },
      {
        path: 'admin',
        canActivate: [AuthGuard, AdminGuard],
        loadChildren: () =>
          import('./features/admin/admin.routes').then(m => m.ADMIN_ROUTES)
      }
    ]
  },

  // Redirección por defecto
  {
    path: '**',
    redirectTo: ''
  }
];
