import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-code-block',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './code-block.component.html',
  styleUrls: ['./code-block.component.scss']
})
export class CodeBlockComponent implements OnInit, OnDestroy {
  displayedRole = '';
  displayedStack = '';
  displayedStatus = '';
  displayedQuote = '';

  private currentTyping: string | null = null;
  private destroyed = false;
  private prefersReducedMotion = false;

  /** Perfil tipado con propósito: quién soy / stack / disponibilidad — no lluvia Matrix. */
  private profiles = [
    {
      role: "'Fullstack & Security'",
      stack: "['Angular','Node','FastAPI']",
      status: "'Disponible'",
      quote: "Me apasiona crear experiencias digitales tan seguras como elegantes."
    },
    {
      role: "'Security Researcher'",
      stack: "['Python','Metasploit','Nmap']",
      status: "'Investigando'",
      quote: "Cada vulnerabilidad es una oportunidad para fortalecer el sistema."
    },
    {
      role: "'CTF Player'",
      stack: "['Pwn','Crypto','Reverse']",
      status: "'Practicando'",
      quote: "No es solo encontrar el flag, es entender el porqué del fallo."
    }
  ];

  private currentProfileIndex = 0;

  ngOnInit(): void {
    this.prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (this.prefersReducedMotion) {
      const profile = this.profiles[0];
      this.displayedRole = profile.role;
      this.displayedStack = profile.stack;
      this.displayedStatus = profile.status;
      this.displayedQuote = profile.quote;
      return;
    }

    void this.runInfiniteLoop();
  }

  ngOnDestroy(): void {
    this.destroyed = true;
  }

  async runInfiniteLoop(): Promise<void> {
    while (!this.destroyed) {
      const profile = this.profiles[this.currentProfileIndex];

      await this.typeEffect('displayedRole', profile.role, 40);
      if (this.destroyed) return;
      await this.typeEffect('displayedStack', profile.stack, 40);
      if (this.destroyed) return;
      await this.typeEffect('displayedStatus', profile.status, 40);
      if (this.destroyed) return;
      await this.typeEffect('displayedQuote', profile.quote, 20);
      if (this.destroyed) return;

      await new Promise(resolve => setTimeout(resolve, 3000));
      if (this.destroyed) return;

      await this.clearEffect();
      if (this.destroyed) return;

      this.currentProfileIndex = (this.currentProfileIndex + 1) % this.profiles.length;
    }
  }

  private async clearEffect(): Promise<void> {
    const props: Array<'displayedRole' | 'displayedStack' | 'displayedStatus' | 'displayedQuote'> =
      ['displayedQuote', 'displayedStatus', 'displayedStack', 'displayedRole'];

    for (const prop of props) {
      if (this.destroyed) return;
      this.currentTyping = prop;
      while (this[prop].length > 0) {
        this[prop] = this[prop].slice(0, -1);
        await new Promise(resolve => setTimeout(resolve, 15));
      }
      this.currentTyping = null;
    }
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  private typeEffect(
    property: 'displayedRole' | 'displayedStack' | 'displayedStatus' | 'displayedQuote',
    text: string,
    speed: number
  ): Promise<void> {
    this.currentTyping = property;
    return new Promise((resolve) => {
      let i = 0;
      const interval = setInterval(() => {
        if (this.destroyed) {
          clearInterval(interval);
          resolve();
          return;
        }
        this[property] += text.charAt(i);
        i++;
        if (i === text.length) {
          clearInterval(interval);
          this.currentTyping = null;
          setTimeout(resolve, 300);
        }
      }, speed);
    });
  }

  isTypingProperty(prop: string): boolean {
    return this.currentTyping === prop;
  }
}
