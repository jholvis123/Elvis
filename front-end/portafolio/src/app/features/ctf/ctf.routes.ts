import { inject } from '@angular/core';
import { ActivatedRouteSnapshot, Router, Routes } from '@angular/router';
import { AuthGuard } from '../../core/guards/auth.guard';
import { AdminGuard } from '../../core/guards/admin.guard';

export const CTF_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/ctf-board/ctf-board.component').then(m => m.CtfBoardComponent)
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
    // Enlaces antiguos /ctf/:id → tablero con la modal del reto abierta
    path: ':id',
    canActivate: [
      (route: ActivatedRouteSnapshot) =>
        inject(Router).createUrlTree(['/ctf'], { queryParams: { reto: route.paramMap.get('id') } })
    ],
    children: []
  }
];
