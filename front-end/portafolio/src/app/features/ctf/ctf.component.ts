import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-ctf',
  standalone: true,
  imports: [CommonModule, RouterOutlet],
  templateUrl: './ctf.component.html',
  styleUrls: ['./ctf.component.scss']
})
export class CtfComponent {}
