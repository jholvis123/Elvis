import { Routes } from '@angular/router';
import { AuthGuard } from '../../core/guards/auth.guard';
import { AdminGuard } from '../../core/guards/admin.guard';

export const CTF_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/ctf-list/ctf-list.component').then(m => m.CtfListComponent)
  },
  {
    path: 'leaderboard',
    loadComponent: () =>
      import('./pages/leaderboard/leaderboard.component').then(m => m.LeaderboardComponent)
  },
  {
    path: 'admin/new',
    canActivate: [AuthGuard, AdminGuard],
    loadComponent: () =>
      import('./pages/ctf-upload/ctf-upload.component').then(m => m.CtfUploadComponent)
  },
  {
    path: ':id',
    loadComponent: () =>
      import('./pages/ctf-detail/ctf-detail.component').then(m => m.CtfDetailComponent)
  }
];
