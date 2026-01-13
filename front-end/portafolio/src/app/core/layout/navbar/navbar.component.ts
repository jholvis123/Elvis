import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.scss']
})
export class NavbarComponent {
  public readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  isMenuOpen = false;

  logout(): void {
    // IMPORTANTE: Suscribirse al Observable para que se ejecute
    this.authService.logout().subscribe({
      next: () => {
        this.router.navigate(['/']);
        this.closeMenu();
      },
      error: () => {
        // Incluso si falla, redirigir al home
        this.router.navigate(['/']);
        this.closeMenu();
      }
    });
  }

  toggleMenu(): void {
    this.isMenuOpen = !this.isMenuOpen;
  }

  closeMenu(): void {
    this.isMenuOpen = false;
  }
}
