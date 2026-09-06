import { Component, OnInit, OnDestroy, HostListener, ElementRef, inject, DestroyRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { PortfolioService, ContactService, ApiAvailabilityService } from '@core/services';
import { ProjectsService } from '../projects/services/projects.service';
import { ProjectSummary, Highlight, ContactInfo } from '@core/models';
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
  private readonly apiAvailability = inject(ApiAvailabilityService);
  private readonly elementRef = inject(ElementRef);
  private readonly destroyRef = inject(DestroyRef);

  technologies: string[] = [];
  highlights: Highlight[] = [];
  aboutPoints: string[] = [];
  projects: ProjectSummary[] = [];
  contactInfo: ContactInfo[] = [];
  projectTypes: { value: string; label: string }[] = [];
  stackItems: string[] = [];
  roles: string[] = [];

  showScrollTop = false;
  loadingProjects = true;
  apiUnavailable = false;

  private observer!: IntersectionObserver;

  ngOnInit(): void {
    this.apiUnavailable = !this.apiAvailability.isApiAvailable();
    this.apiAvailability.apiUnavailable$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(unavailable => {
        this.apiUnavailable = unavailable;
        if (unavailable) {
          this.clearPortfolioData();
          this.projects = [];
          this.loadingProjects = false;
        }
      });

    // Tipos de proyecto solo si hay API; no inventar formulario usable sin backend
    if (this.apiAvailability.isApiConfigured()) {
      this.projectTypes = this.contactService.getProjectTypesSync();
      this.loadProfile();
      this.loadContact();
      this.loadProjects();
      this.loadProjectTypes();
    } else {
      this.loadingProjects = false;
      this.clearPortfolioData();
    }
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
        this.apiAvailability.markNetworkOk();
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
      error: (err) => {
        this.apiAvailability.noteRequestFailure(err);
        this.clearPortfolioData();
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
      },
      error: (err) => {
        this.apiAvailability.noteRequestFailure(err);
        this.contactInfo = [];
      }
    });
  }

  private loadProjects(): void {
    this.loadingProjects = true;
    this.projectsService.getFeaturedProjects(6).pipe(
      takeUntilDestroyed(this.destroyRef)
    ).subscribe({
      next: (projects) => {
        this.apiAvailability.markNetworkOk();
        this.projects = projects;
        this.loadingProjects = false;
      },
      error: (err) => {
        this.apiAvailability.noteRequestFailure(err);
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
      },
      error: (err) => this.apiAvailability.noteRequestFailure(err)
    });
  }

  /** Vaciar datos de portafolio — no usar stats inventados. */
  private clearPortfolioData(): void {
    this.roles = [];
    this.stackItems = [];
    this.technologies = [];
    this.aboutPoints = [];
    this.highlights = [];
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
