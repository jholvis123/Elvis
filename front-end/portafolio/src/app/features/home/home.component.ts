import { Component, OnInit, AfterViewInit, OnDestroy, HostListener, ElementRef, inject, DestroyRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { PortfolioService, ContactService, ApiAvailabilityService } from '@core/services';
import { ProjectsService } from '../projects/services/projects.service';
import { ProjectSummary, Highlight, ContactInfo, ExperienceItem, CapabilityChip } from '@core/models';
import { ScrollToTopComponent } from '@shared/components';
import {
  HeroSectionComponent,
  AboutSectionComponent,
  ExperienceSectionComponent,
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
    ExperienceSectionComponent,
    ProjectsSectionComponent,
    ContactSectionComponent
  ],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit, AfterViewInit, OnDestroy {
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
  avatarUrl: string | null = null;

  experienceItems: ExperienceItem[] = [];
  capabilities: CapabilityChip[] = [];

  showScrollTop = false;
  loadingProjects = true;
  loadingExperience = true;
  loadingCapabilities = true;
  apiUnavailable = false;
  experienceError = false;
  capabilitiesError = false;

  private observer?: IntersectionObserver;
  private mutationObserver?: MutationObserver;
  private readonly observedReveals = new WeakSet<Element>();

  ngOnInit(): void {
    this.apiUnavailable = !this.apiAvailability.isApiAvailable();
    this.apiAvailability.apiUnavailable$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(unavailable => {
        this.apiUnavailable = unavailable;
        if (unavailable) {
          this.clearPortfolioData();
          this.projects = [];
          this.experienceItems = [];
          this.capabilities = [];
          this.loadingProjects = false;
          this.loadingExperience = false;
          this.loadingCapabilities = false;
        }
      });

    // Tipos de proyecto solo si hay API; no inventar formulario usable sin backend
    if (this.apiAvailability.isApiConfigured()) {
      this.projectTypes = this.contactService.getProjectTypesSync();
      this.loadProfile();
      this.loadContact();
      this.loadProjects();
      this.loadProjectTypes();
      this.loadExperience();
      this.loadCapabilities();
    } else {
      this.loadingProjects = false;
      this.loadingExperience = false;
      this.loadingCapabilities = false;
      this.clearPortfolioData();
    }
  }

  ngAfterViewInit(): void {
    this.setupIntersectionObserver();
  }

  ngOnDestroy(): void {
    this.mutationObserver?.disconnect();
    this.observer?.disconnect();
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
        this.avatarUrl = this.portfolioService.resolveAvatarUrl(profile.avatar_url);
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

  private loadExperience(): void {
    this.loadingExperience = true;
    this.experienceError = false;
    this.portfolioService.getExperience().pipe(
      takeUntilDestroyed(this.destroyRef)
    ).subscribe({
      next: (items) => {
        this.apiAvailability.markNetworkOk();
        this.experienceItems = items;
        this.loadingExperience = false;
        this.experienceError = false;
      },
      error: (err) => {
        this.apiAvailability.noteRequestFailure(err);
        this.experienceItems = [];
        this.loadingExperience = false;
        // 404 (ruta aún no desplegada) → empty honesto, no error alarmista
        const status = err && typeof err === 'object' && 'status' in err
          ? (err as { status?: number }).status
          : undefined;
        this.experienceError = status !== 404;
      }
    });
  }

  private loadCapabilities(): void {
    this.loadingCapabilities = true;
    this.capabilitiesError = false;
    this.portfolioService.getCapabilities().pipe(
      takeUntilDestroyed(this.destroyRef)
    ).subscribe({
      next: (chips) => {
        this.apiAvailability.markNetworkOk();
        this.capabilities = chips;
        this.loadingCapabilities = false;
        this.capabilitiesError = false;
      },
      error: (err) => {
        this.apiAvailability.noteRequestFailure(err);
        this.capabilities = [];
        this.loadingCapabilities = false;
        const status = err && typeof err === 'object' && 'status' in err
          ? (err as { status?: number }).status
          : undefined;
        // Hasta merge+#48: 404 → empty honesto (no inventar desde stack_items)
        this.capabilitiesError = status !== 404;
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
    this.avatarUrl = null;
    this.experienceItems = [];
    this.capabilities = [];
  }

  private setupIntersectionObserver(): void {
    const root = this.elementRef.nativeElement as HTMLElement;

    // Accesibilidad: sin animación de reveal, mostrar contenido de inmediato.
    // Sin IO (o reduced-motion): nunca dejar opacity 0 permanente.
    const reducedMotion =
      typeof matchMedia !== 'undefined' &&
      matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reducedMotion || typeof IntersectionObserver === 'undefined') {
      this.activateRevealElements(root);
      this.mutationObserver = new MutationObserver(() => this.activateRevealElements(root));
      this.mutationObserver.observe(root, { childList: true, subtree: true });
      return;
    }

    this.observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('active');
          this.observer?.unobserve(entry.target);
        }
      });
    }, {
      root: null,
      rootMargin: '0px 0px -5% 0px',
      threshold: 0.05
    });

    this.observeRevealElements(root);

    // Proyectos / timeline llegan async (*ngIf / *ngFor); re-observar nodos nuevos.
    this.mutationObserver = new MutationObserver(() => this.observeRevealElements(root));
    this.mutationObserver.observe(root, { childList: true, subtree: true });
  }

  private observeRevealElements(root: HTMLElement = this.elementRef.nativeElement): void {
    if (!this.observer) {
      return;
    }

    const elements = root.querySelectorAll('.reveal, .reveal-left, .reveal-right');
    elements.forEach((el: Element) => {
      if (this.observedReveals.has(el)) {
        return;
      }
      this.observedReveals.add(el);

      // Ya en viewport al montarse (p. ej. tras carga async): no depender solo del IO.
      if (this.isElementInViewport(el)) {
        el.classList.add('active');
        return;
      }

      this.observer?.observe(el);
    });
  }

  private activateRevealElements(root: HTMLElement = this.elementRef.nativeElement): void {
    root.querySelectorAll('.reveal, .reveal-left, .reveal-right').forEach((el: Element) => {
      el.classList.add('active');
    });
  }

  private isElementInViewport(el: Element): boolean {
    const rect = el.getBoundingClientRect();
    const vh = window.innerHeight || document.documentElement.clientHeight;
    const vw = window.innerWidth || document.documentElement.clientWidth;
    return rect.bottom > 0 && rect.right > 0 && rect.top < vh && rect.left < vw;
  }
}

