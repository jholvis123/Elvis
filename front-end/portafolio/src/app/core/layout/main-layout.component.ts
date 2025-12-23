import { Component } from '@angular/core';
import { NavbarComponent } from "./navbar/navbar.component";
import { RouterOutlet } from "@angular/router";
import { FooterComponent } from "./footer/footer.component";

@Component({
  selector: 'app-main-layout',
  standalone: true,
  template: `
    <app-navbar></app-navbar>
    <main class="bg-slate-900 min-h-screen text-gray-200">
      <router-outlet></router-outlet>
    </main>
    <app-footer></app-footer>
  `,
  imports: [NavbarComponent, RouterOutlet, FooterComponent]
})
export class MainLayoutComponent {}
