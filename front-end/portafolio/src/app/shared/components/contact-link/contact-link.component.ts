import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ContactInfo } from '@core/models';
import { IconComponent, IconName } from '@shared/icons/icon.component';

const CONTACT_ICON_MAP: Record<ContactInfo['type'], IconName> = {
  email: 'envelope',
  linkedin: 'linkedin',
  github: 'github',
  twitter: 'x-twitter',
};

@Component({
  selector: 'app-contact-link',
  standalone: true,
  imports: [CommonModule, IconComponent],
  templateUrl: './contact-link.component.html',
  styleUrls: ['./contact-link.component.scss']
})
export class ContactLinkComponent {
  @Input({ required: true }) contact!: ContactInfo;

  get iconName(): IconName {
    return CONTACT_ICON_MAP[this.contact.type];
  }
}
