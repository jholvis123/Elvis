import { Component } from '@angular/core';
import { NavbarComponent } from "./navbar/navbar.component";
import { RouterOutlet } from "@angular/router";
import { FooterComponent } from "./footer/footer.component";

@Component({
  selector: 'app-main-layout',
  standalone: true,
  template: `
    <a href="#main-content" class="skip-link">Saltar al contenido</a>
    <app-navbar></app-navbar>
    <main id="main-content" class="bg-slate-900 min-h-screen text-gray-200" tabindex="-1">
      <router-outlet></router-outlet>
    </main>
    <app-footer></app-footer>
  `,
  imports: [NavbarComponent, RouterOutlet, FooterComponent]
})
export class MainLayoutComponent {}
