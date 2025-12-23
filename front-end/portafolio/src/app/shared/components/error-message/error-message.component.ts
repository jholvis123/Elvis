import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-error-message',
    standalone: true,
    imports: [CommonModule],
    template: `
    <div class="bg-red-500/20 border border-red-500/50 rounded-lg p-6 text-center" [class]="customClass">
      <p class="text-red-200">{{ message }}</p>
      <ng-content></ng-content>
    </div>
  `,
    styles: []
})
export class ErrorMessageComponent {
    @Input() message = 'Ha ocurrido un error';
    @Input() customClass = '';
}
