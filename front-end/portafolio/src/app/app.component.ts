import { Component, inject, OnInit } from '@angular/core';
import { CommonModule, ViewportScroller } from '@angular/common';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs/operators';
import { ToastContainerComponent } from './shared/components/toast-container/toast-container.component';

/** Fixed navbar ~77px; matches CSS scroll-margin 5.5rem on sections/headings. */
const HASH_SCROLL_OFFSET_Y = 88;

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, ToastContainerComponent],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  title = 'portafolio';

  private readonly viewportScroller = inject(ViewportScroller);
  private readonly router = inject(Router);

  ngOnInit(): void {
    this.viewportScroller.setOffset([0, HASH_SCROLL_OFFSET_Y]);

    this.router.events
      .pipe(filter((e): e is NavigationEnd => e instanceof NavigationEnd))
      .subscribe((e) => {
        const anchor = e.urlAfterRedirects.split('#')[1];
        if (!anchor) {
          return;
        }
        const go = () => {
          const el = document.getElementById(anchor);
          if (!el) {
            return;
          }
          const root = document.documentElement;
          const prev = root.style.scrollBehavior;
          root.style.scrollBehavior = 'auto';
          el.scrollIntoView({ block: 'start' });
          root.style.scrollBehavior = prev;
        };
        // Wait for mobile nav closeMenu() so layout/scroll-margin resolve correctly
        setTimeout(go, 200);
      });
  }
}
