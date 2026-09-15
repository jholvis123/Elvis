import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IconComponent } from '@shared/icons/icon.component';

@Component({
  selector: 'app-scroll-to-top',
  standalone: true,
  imports: [CommonModule, IconComponent],
  templateUrl: './scroll-to-top.component.html',
  styleUrls: ['./scroll-to-top.component.scss']
})
export class ScrollToTopComponent {
  @Input() show = false;
  @Output() scrollTop = new EventEmitter<void>();

  onClick(): void {
    this.scrollTop.emit();
  }
}
