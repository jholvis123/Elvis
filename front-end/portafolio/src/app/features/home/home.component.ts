import { Component, OnInit, OnDestroy, HostListener, ElementRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';

import { PortfolioService, ContactService } from '@core/services';
import { ProjectsService } from '../projects/services/projects.service';
import { Project, Highlight, ContactInfo } from '@core/models';
import { ScrollToTopComponent } from '@shared/components';
import {
  HeroSectionComponent,
  AboutSectionComponent,
  ProjectsSectionComponent,
  ContactSectionComponent
} from './sections';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    CommonModule,
    ScrollToTopComponent,
    HeroSectionComponent,
    AboutSectionComponent,
    ProjectsSectionComponent,
    ContactSectionComponent
  ],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit, OnDestroy {
  private readonly portfolioService = inject(PortfolioService);
  private readonly contactService = inject(ContactService);
  private readonly projectsService = inject(ProjectsService);
  private readonly elementRef = inject(ElementRef);

  // Data from services
  technologies: string[] = [];
  highlights: Highlight[] = [];
  aboutPoints: string[] = [];
  projects: Project[] = [];
  contactInfo: ContactInfo[] = [];
  projectTypes: { value: string; label: string }[] = [];
  stackItems: string[] = [];
  roles: string[] = [];

  // Scroll to top
  showScrollTop = false;

  // Intersection Observer
  private observer!: IntersectionObserver;

  ngOnInit(): void {
    this.loadData();
    this.loadDataFromApi();
    this.setupIntersectionObserver();
  }

  ngOnDestroy(): void {
    if (this.observer) {
      this.observer.disconnect();
    }
  }

  @HostListener('window:scroll')
  onWindowScroll(): void {
    this.showScrollTop = window.scrollY > 500;
  }

  scrollToTop(): void {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  /**
   * Carga inicial con datos locales (fallback inmediato)
   */
  private loadData(): void {
    this.technologies = this.portfolioService.getTechnologies().map(t => t.name);
    this.highlights = this.portfolioService.getHighlights();
    this.aboutPoints = this.portfolioService.getAboutPoints();
    this.projects = this.portfolioService.getProjects();
    this.roles = this.portfolioService.getRoles();
    this.stackItems = this.portfolioService.getStackItems();
    this.contactInfo = this.contactService.getContactInfo();
    this.projectTypes = this.contactService.getProjectTypesSync();
  }

  /**
   * Carga datos desde la API (sobrescribe los datos locales cuando responde)
   */
  private loadDataFromApi(): void {
    // ✅ NUEVO: Cargar proyectos destacados desde API
    this.projectsService.getFeaturedProjects(6).subscribe({
      next: (projects) => {
        if (projects.length > 0) {
          // Mapear los proyectos de la API al formato de Project del home
          this.projects = projects.map(p => ({
            id: p.id,
            title: p.title,
            description: p.short_description,
            tags: p.technologies.slice(0, 3), // Primeras 3 tecnologías como tags
            cta: 'Ver proyecto',
            year: new Date(p.created_at).getFullYear(),
            category: 'web' // Por defecto
          }));
        }
      },
      error: (err) => console.log('Usando proyectos locales:', err.message)
    });

    // Cargar roles desde API
    this.portfolioService.getRolesFromApi().subscribe({
      next: (roles) => {
        if (roles.length > 0) this.roles = roles;
      },
      error: (err) => console.log('Usando roles locales:', err.message)
    });

    // Cargar stack items desde API
    this.portfolioService.getStackFromApi().subscribe({
      next: (stack) => {
        if (stack.length > 0) this.stackItems = stack;
      },
      error: (err) => console.log('Usando stack local:', err.message)
    });

    // Cargar about points desde API
    this.portfolioService.getAboutPointsFromApi().subscribe({
      next: (points) => {
        if (points.length > 0) this.aboutPoints = points;
      },
      error: (err) => console.log('Usando about points locales:', err.message)
    });

    // Cargar highlights desde API
    this.portfolioService.getHighlightsFromApi().subscribe({
      next: (highlights) => {
        if (highlights.length > 0) this.highlights = highlights;
      },
      error: (err) => console.log('Usando highlights locales:', err.message)
    });

    // Cargar project types desde API
    this.contactService.getProjectTypes().subscribe({
      next: (types) => {
        if (types.length > 0) this.projectTypes = types;
      },
      error: (err) => console.log('Usando project types locales:', err.message)
    });
  }

  private setupIntersectionObserver(): void {
    const options: IntersectionObserverInit = {
      root: null,
      rootMargin: '0px',
      threshold: 0.1
    };

    this.observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('active');
        }
      });
    }, options);

    // Observar después de que el view esté listo
    setTimeout(() => {
      const elements = this.elementRef.nativeElement.querySelectorAll('.reveal, .reveal-left, .reveal-right');
      elements.forEach((el: Element) => this.observer.observe(el));
    }, 100);
  }
}
