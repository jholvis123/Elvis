import { Component, OnInit, OnDestroy, HostListener, ElementRef, inject, DestroyRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

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
  private readonly destroyRef = inject(DestroyRef);

  technologies: string[] = [];
  highlights: Highlight[] = [];
  aboutPoints: string[] = [];
  projects: Project[] = [];
  contactInfo: ContactInfo[] = [];
  projectTypes: { value: string; label: string }[] = [];
  stackItems: string[] = [];
  roles: string[] = [];

  showScrollTop = false;
  loadingProjects = true;

  private observer!: IntersectionObserver;

  ngOnInit(): void {
    this.applyPortfolioFallback();
    this.projectTypes = this.contactService.getProjectTypesSync();
    this.loadProfile();
    this.loadContact();
    this.loadProjects();
    this.loadProjectTypes();
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

  private loadProfile(): void {
    this.portfolioService.getProfile().pipe(
      takeUntilDestroyed(this.destroyRef)
    ).subscribe({
      next: (profile) => {
        if (profile.roles?.length) this.roles = profile.roles;
        if (profile.stack_items?.length) {
          this.stackItems = profile.stack_items;
          this.technologies = profile.stack_items;
        }
        if (profile.about_points?.length) this.aboutPoints = profile.about_points;
        if (profile.highlights?.length) this.highlights = profile.highlights;
        if (!this.contactInfo.length && profile.social_links) {
          this.contactInfo = this.contactService.mapSocialLinks(profile.social_links);
        }
      },
      error: () => {
        this.applyPortfolioFallback();
      }
    });
  }

  private loadContact(): void {
    this.contactService.getContactInfo().pipe(
      takeUntilDestroyed(this.destroyRef)
    ).subscribe({
      next: (info) => {
        if (info.length) {
          this.contactInfo = info;
        }
      }
    });
  }

  private loadProjects(): void {
    this.loadingProjects = true;
    this.projectsService.getFeaturedProjects(6).pipe(
      takeUntilDestroyed(this.destroyRef)
    ).subscribe({
      next: (projects) => {
        this.projects = projects.map(p => ({
          id: p.id,
          title: p.title,
          description: p.short_description,
          tags: p.technologies.slice(0, 3),
          cta: 'Ver proyecto',
          year: new Date(p.created_at).getFullYear(),
          category: 'web'
        }));
        this.loadingProjects = false;
      },
      error: () => {
        this.projects = [];
        this.loadingProjects = false;
      }
    });
  }

  private loadProjectTypes(): void {
    this.contactService.getProjectTypes().pipe(
      takeUntilDestroyed(this.destroyRef)
    ).subscribe({
      next: (types) => {
        if (types.length > 0) this.projectTypes = types;
      }
    });
  }

  private applyPortfolioFallback(): void {
    this.roles = this.portfolioService.getRoles();
    this.stackItems = this.portfolioService.getStackItems();
    this.technologies = this.portfolioService.getTechnologies().map(t => t.name);
    this.aboutPoints = this.portfolioService.getAboutPoints();
    this.highlights = this.portfolioService.getHighlights();
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

    setTimeout(() => {
      const elements = this.elementRef.nativeElement.querySelectorAll('.reveal, .reveal-left, .reveal-right');
      elements.forEach((el: Element) => this.observer.observe(el));
    }, 100);
  }
}
