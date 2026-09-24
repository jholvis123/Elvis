import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, forkJoin, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { ApiAvailabilityService } from './api-availability.service';
import { ApiService } from './api.service';
import { PortfolioService } from './portfolio.service';

/**
 * Lightweight counts for optional portfolio surfaces (nav + home sections + hero CTAs).
 *
 * Visibility policy (documented for LIDER/AUDITOR):
 * - loading / idle: hide nav links (avoid flash of empty destinations); keep home
 *   sections mounted so their skeletons can paint.
 * - ready + count === 0: hide nav link AND home section (reappear when count > 0).
 * - error: keep nav link + home section visible so a transient API failure never
 *   permanently hides content the user could still reach/retry.
 */
export type SectionKey = 'experience' | 'projects' | 'ctf' | 'writeups';

export type SectionStatus = 'idle' | 'loading' | 'ready' | 'error';

export interface SectionState {
  status: SectionStatus;
  count: number;
}

interface CountPage {
  items?: unknown[];
  total?: number;
}

const INITIAL: SectionState = { status: 'idle', count: 0 };

@Injectable({
  providedIn: 'root',
})
export class SectionVisibilityService {
  private readonly apiAvailability = inject(ApiAvailabilityService);
  private readonly api = inject(ApiService);
  private readonly portfolioService = inject(PortfolioService);

  private readonly experience = signal<SectionState>({ ...INITIAL });
  private readonly projects = signal<SectionState>({ ...INITIAL });
  private readonly ctf = signal<SectionState>({ ...INITIAL });
  private readonly writeups = signal<SectionState>({ ...INITIAL });

  private started = false;

  /** Nav / hero CTA: hide while loading; show on error; show when count > 0. */
  readonly showExperienceNav = computed(() => this.visibleInNav(this.experience()));
  readonly showProjectsNav = computed(() => this.visibleInNav(this.projects()));
  readonly showCtfNav = computed(() => this.visibleInNav(this.ctf()));
  readonly showWriteupsNav = computed(() => this.visibleInNav(this.writeups()));

  /**
   * Home section: show while loading (skeleton) or on error; hide only on
   * successful empty response.
   */
  readonly showExperienceSection = computed(() => this.visibleInHome(this.experience()));
  readonly showProjectsSection = computed(() => this.visibleInHome(this.projects()));

  readonly writeupsCount = computed(() =>
    this.writeups().status === 'ready' ? this.writeups().count : 0
  );
  readonly ctfCount = computed(() => (this.ctf().status === 'ready' ? this.ctf().count : 0));
  readonly projectsCount = computed(() =>
    this.projects().status === 'ready' ? this.projects().count : 0
  );

  /** Kick off size=1 probes once (safe to call from multiple injectors). */
  ensureLoaded(): void {
    if (this.started) {
      return;
    }
    this.started = true;

    if (!this.apiAvailability.isApiConfigured()) {
      this.experience.set({ status: 'ready', count: 0 });
      this.projects.set({ status: 'ready', count: 0 });
      this.ctf.set({ status: 'ready', count: 0 });
      this.writeups.set({ status: 'ready', count: 0 });
      return;
    }

    this.experience.set({ status: 'loading', count: 0 });
    this.projects.set({ status: 'loading', count: 0 });
    this.ctf.set({ status: 'loading', count: 0 });
    this.writeups.set({ status: 'loading', count: 0 });

    forkJoin({
      writeups: this.countFrom('/writeups'),
      ctf: this.countFrom('/ctfs'),
      projects: this.countFrom('/projects'),
      experience: this.portfolioService.getExperience().pipe(
        map((items) => items.length),
        catchError((err) => {
          this.apiAvailability.noteRequestFailure(err);
          return of(-1);
        })
      ),
    }).subscribe({
      next: (counts) => {
        this.applyCount(this.writeups, counts.writeups);
        this.applyCount(this.ctf, counts.ctf);
        this.applyCount(this.projects, counts.projects);
        this.applyCount(this.experience, counts.experience);
        if (
          counts.writeups >= 0 ||
          counts.ctf >= 0 ||
          counts.projects >= 0 ||
          counts.experience >= 0
        ) {
          this.apiAvailability.markNetworkOk();
        }
      },
    });
  }

  private countFrom(path: string): Observable<number> {
    return this.api.get<CountPage>(path, { page: 1, size: 1 }).pipe(
      map((r) => {
        if (typeof r?.total === 'number') {
          return r.total;
        }
        return Array.isArray(r?.items) ? r.items.length : 0;
      }),
      catchError((err) => {
        this.apiAvailability.noteRequestFailure(err);
        return of(-1);
      })
    );
  }

  private applyCount(
    target: { set: (v: SectionState) => void },
    count: number
  ): void {
    if (count < 0) {
      target.set({ status: 'error', count: 0 });
      return;
    }
    target.set({ status: 'ready', count });
  }

  private visibleInNav(state: SectionState): boolean {
    if (state.status === 'loading' || state.status === 'idle') {
      return false;
    }
    if (state.status === 'error') {
      return true;
    }
    return state.count > 0;
  }

  private visibleInHome(state: SectionState): boolean {
    if (state.status === 'loading' || state.status === 'idle') {
      return true;
    }
    if (state.status === 'error') {
      return true;
    }
    return state.count > 0;
  }
}
