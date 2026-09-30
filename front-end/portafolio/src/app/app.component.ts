import { Component, inject, OnDestroy, OnInit } from '@angular/core';
import { CommonModule, ViewportScroller } from '@angular/common';
import { NavigationEnd, NavigationStart, Router, RouterOutlet, Scroll } from '@angular/router';
import { Subscription } from 'rxjs';
import { ToastContainerComponent } from './shared/components/toast-container/toast-container.component';

/** Fixed navbar ~77px; matches CSS scroll-margin 5.5rem. Used only as a fallback. */
const HASH_SCROLL_OFFSET_Y = 88;
/** Heading sits this far below the real navbar bottom (TESTR window 4–40px). */
const ANCHOR_GAP_PX = 16;

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, ToastContainerComponent],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit, OnDestroy {
  title = 'portafolio';

  private readonly viewportScroller = inject(ViewportScroller);
  private readonly router = inject(Router);

  /** Bumps on every navigation so in-flight rAF/observer callbacks no-op. */
  private followGen = 0;
  private resizeObserver: ResizeObserver | null = null;
  private routerSub?: Subscription;
  /** Inline scroll-behavior while a fragment follow is active. */
  private savedScrollBehavior: string | null = null;

  ngOnInit(): void {
    this.viewportScroller.setOffset([0, HASH_SCROLL_OFFSET_Y]);

    const initial = this.fragmentFrom(this.router.url, null, true);
    if (initial) {
      this.followAnchor(initial);
    }

    this.routerSub = this.router.events.subscribe((event) => {
      if (event instanceof NavigationStart) {
        // Fast route changes must not scroll a page we already left.
        this.cancelAnchorFollow();
        return;
      }
      if (event instanceof NavigationEnd) {
        const anchor = this.fragmentFrom(event.urlAfterRedirects, null, true);
        if (anchor) {
          this.followAnchor(anchor);
        }
        return;
      }
      if (event instanceof Scroll) {
        // Fires after the router restores history scroll (browser back). Re-align
        // the fragment using the live navbar, which that restore does not.
        const routerEvent = event.routerEvent;
        const url = routerEvent instanceof NavigationEnd ? routerEvent.urlAfterRedirects : routerEvent.url;
        const anchor = this.fragmentFrom(url, event.anchor, true);
        if (anchor) {
          this.followAnchor(anchor);
        }
      }
    });
  }

  ngOnDestroy(): void {
    this.cancelAnchorFollow();
    this.routerSub?.unsubscribe();
  }

  private fragmentFrom(url: string, anchor: string | null | undefined, allowLiveHash: boolean): string | null {
    if (anchor) {
      return anchor;
    }
    const hashIdx = url.indexOf('#');
    if (hashIdx >= 0 && hashIdx < url.length - 1) {
      return decodeURIComponent(url.slice(hashIdx + 1));
    }
    if (!allowLiveHash) {
      return null;
    }
    const live = window.location.hash;
    return live.length > 1 ? decodeURIComponent(live.slice(1)) : null;
  }

  private cancelAnchorFollow(): void {
    this.followGen++;
    this.resizeObserver?.disconnect();
    this.resizeObserver = null;
    this.unlockScrollBehavior();
  }

  /** Router scrollToPosition inherits `scroll-behavior: smooth` and undoes the anchor. */
  private lockScrollBehavior(): void {
    if (this.savedScrollBehavior === null) {
      this.savedScrollBehavior = document.documentElement.style.scrollBehavior;
    }
    document.documentElement.style.scrollBehavior = 'auto';
  }

  private unlockScrollBehavior(): void {
    if (this.savedScrollBehavior === null) {
      return;
    }
    document.documentElement.style.scrollBehavior = this.savedScrollBehavior;
    this.savedScrollBehavior = null;
  }

  /**
   * Keep `anchor` just below the real navbar. Re-runs when the hero (or anything
   * above the target) changes size — no fixed delay. Callbacks die on the next navigation.
   */
  private followAnchor(anchor: string): void {
    this.cancelAnchorFollow();
    const gen = this.followGen;
    this.lockScrollBehavior();

    const align = (): void => {
      if (gen !== this.followGen) {
        return;
      }
      this.alignAnchor(anchor);
    };

    let watching = false;
    const watch = (): void => {
      if (watching || gen !== this.followGen || typeof ResizeObserver === 'undefined') {
        return;
      }
      watching = true;
      this.resizeObserver?.disconnect();
      this.resizeObserver = new ResizeObserver(() => align());
      const nav = document.querySelector('nav');
      if (nav) {
        this.resizeObserver.observe(nav);
      }
      // Stays connected until the next navigation so a late hero (cold API) still re-aligns.
      this.resizeObserver.observe(document.body);
      const hero = document.getElementById('hero') ?? document.querySelector('app-hero-section');
      if (hero) {
        this.resizeObserver.observe(hero);
      }
      const target = document.getElementById(anchor);
      let node: Element | null = target;
      while (node && node !== document.body) {
        let prev = node.previousElementSibling;
        while (prev) {
          this.resizeObserver.observe(prev);
          prev = prev.previousElementSibling;
        }
        node = node.parentElement;
      }
    };

    let frames = 0;
    let foundFrame = -1;
    const tick = (): void => {
      if (gen !== this.followGen) {
        return;
      }
      align();
      watch();
      if (foundFrame < 0 && document.getElementById(anchor)) {
        foundFrame = frames;
        watching = false;
        watch();
      }
      frames++;
      // A few frames after the target exists so we run after the router's
      // scrollToPosition (same turn as Scroll). Keep polling if the view is still loading.
      const settled = foundFrame >= 0 && frames > foundFrame + 3;
      if (!settled && frames < 600) {
        requestAnimationFrame(tick);
      } else if (gen === this.followGen) {
        this.unlockScrollBehavior();
      }
    };
    tick();
  }

  /** Place the heading ~16px under the closed navbar (not the open mobile panel). */
  private alignAnchor(anchor: string): void {
    const el = document.getElementById(anchor);
    if (!el) {
      return;
    }
    const navBottom = this.compactNavBottom();
    // .reveal uses translateY until it is on screen. Align the resting position
    // so the heading does not jump up under the navbar when that transform ends.
    const delta = this.restingTop(el) - (navBottom + ANCHOR_GAP_PX);
    if (Math.abs(delta) < 2) {
      return;
    }
    const root = document.documentElement;
    const prev = root.style.scrollBehavior;
    root.style.scrollBehavior = 'auto';
    window.scrollBy(0, delta);
    root.style.scrollBehavior = prev;
  }

  /** Viewport Y of the heading after reveal transforms finish (translate → 0). */
  private restingTop(el: HTMLElement): number {
    let translateY = 0;
    let node: HTMLElement | null = el;
    while (node && node !== document.documentElement) {
      const transform = getComputedStyle(node).transform;
      if (transform && transform !== 'none') {
        translateY += new DOMMatrixReadOnly(transform).m42;
      }
      node = node.parentElement;
    }
    return el.getBoundingClientRect().top - translateY;
  }

  private compactNavBottom(): number {
    const nav = document.querySelector('nav');
    if (!nav) {
      return HASH_SCROLL_OFFSET_Y;
    }
    const navRect = nav.getBoundingClientRect();
    // Open mobile drawer makes <nav> hundreds of px tall; use the top bar instead.
    if (navRect.height > 100) {
      const bar = nav.querySelector('.max-w-6xl');
      if (bar) {
        return bar.getBoundingClientRect().bottom;
      }
    }
    return navRect.bottom;
  }
}
