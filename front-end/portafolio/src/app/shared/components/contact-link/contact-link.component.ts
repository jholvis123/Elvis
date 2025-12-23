import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ContactInfo } from '@core/models';

@Component({
  selector: 'app-contact-link',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './contact-link.component.html',
  styleUrls: ['./contact-link.component.scss']
})
export class ContactLinkComponent {
  @Input({ required: true }) contact!: ContactInfo;
}
