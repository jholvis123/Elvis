import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

import { ContactInfo } from '@core/models';
import { ContactLinkComponent } from '@shared/components';
import { ContactFormComponent } from '@shared/components/contact-form/contact-form.component';

@Component({
  selector: 'app-contact-section',
  standalone: true,
  imports: [CommonModule, ContactLinkComponent, ContactFormComponent],
  templateUrl: './contact-section.component.html',
  styleUrls: ['./contact-section.component.scss']
})
export class ContactSectionComponent {
  @Input() contactInfo: ContactInfo[] = [];
  @Input() projectTypes: { value: string; label: string }[] = [];
}
