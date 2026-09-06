import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { ApiAvailabilityService } from '../../../core/services/api-availability.service';
import { IconComponent } from '../../../shared/icons/icon.component';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, IconComponent],
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.scss']
})
export class NavbarComponent {
  public readonly authService = inject(AuthService);
  public readonly apiAvailability = inject(ApiAvailabilityService);
  private readonly router = inject(Router);
  isMenuOpen = false;

  /** Mostrar login/salir solo si la API está disponible. */
  get showAuthLinks(): boolean {
    return this.apiAvailability.isApiAvailable();
  }

  logout(): void {
    this.authService.logout().subscribe({
      next: () => {
        this.router.navigate(['/']);
        this.closeMenu();
      },
      error: () => {
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
