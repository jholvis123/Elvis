import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ContactService } from '../../services/contact.service';

@Component({
  selector: 'app-footer',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './footer.component.html',
  styleUrls: ['./footer.component.scss']
})
export class FooterComponent implements OnInit {
  private readonly contactService = inject(ContactService);

  currentYear = new Date().getFullYear();
  email = '';

  ngOnInit(): void {
    this.contactService.getContactInfo().subscribe({
      next: (items) => {
        this.email = items.find(item => item.type === 'email')?.value || '';
      }
    });
  }
}
