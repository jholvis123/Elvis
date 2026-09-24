import { Component, inject } from '@angular/core';
import { CommonModule, ViewportScroller } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { ToastContainerComponent } from './shared/components/toast-container/toast-container.component';

/** Fixed navbar ~77px; keep fragment targets below the bar (matches scroll-margin 5.5rem). */
const HASH_SCROLL_OFFSET_Y = 88;

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, ToastContainerComponent],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'portafolio';

  constructor() {
    inject(ViewportScroller).setOffset([0, HASH_SCROLL_OFFSET_Y]);
  }
}
