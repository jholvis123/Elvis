import { Injectable, OnDestroy, computed, inject, signal } from '@angular/core';
import { Observable, Subscription, forkJoin, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { ApiAvailabilityService } from './api-availability.service';
import { ApiService } from './api.service';

/**
 * Lightweight counts for optional portfolio surfaces (nav + home sections + hero CTAs).
 *
 * Visibility policy (LIDER / AUDITOR):
 * - loading / idle: hide nav links (anti-flash on warm API).
 * - loading past LOAD_TIMEOUT_MS (~2.5s, Render cold start): SHOW nav/CTAs
 *   provisionally; a later ready with count===0 may hide again (acceptable).
 * - ready + count === 0: hide nav link AND home section.
 * - error: SHOW (never hide permanently on failure).
 * - Home sections: still show skeleton while loading (including timed-out loading).
 * - Call refresh() after admin create/publish so counts update without full reload.
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

/** Cold-start grace: show nav if probes have not resolved yet. */
export const SECTION_VISIBILITY_LOAD_TIMEOUT_MS = 2500;

const INITIAL: SectionState = { status: 'idle', count: 0 };

@Injectable({
  providedIn: 'root',
})
export class SectionVisibilityService implements OnDestroy {
  private readonly apiAvailability = inject(ApiAvailabilityService);
  private readonly api = inject(ApiService);

  private readonly experience = signal<SectionState>({ ...INITIAL });
  private readonly projects = signal<SectionState>({ ...INITIAL });
  private readonly ctf = signal<SectionState>({ ...INITIAL });
  private readonly writeups = signal<SectionState>({ ...INITIAL });

  /**
   * When true, nav treats still-loading sections as visible (cold start).
   * Cleared on each new probe round; set by the load timeout.
   */
  private readonly loadTimedOut = signal(false);

  private started = false;
  private loadSub: Subscription | null = null;
  private loadTimeoutId: ReturnType<typeof setTimeout> | null = null;

  /** Nav / hero CTA. */
  readonly showExperienceNav = computed(() => this.visibleInNav(this.experience()));
  readonly showProjectsNav = computed(() => this.visibleInNav(this.projects()));
  readonly showCtfNav = computed(() => this.visibleInNav(this.ctf()));
  readonly showWriteupsNav = computed(() => this.visibleInNav(this.writeups()));

  /** Home section: skeleton while loading; hide only on successful empty. */
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
    this.startProbes();
  }

  /**
   * Re-probe counts after admin create/publish so nav appears without reload.
   * Cancels any in-flight probes and resets the cold-start timer.
   */
  refresh(): void {
    this.cancelInFlight();
    this.started = true;
    this.startProbes();
  }

  ngOnDestroy(): void {
    this.cancelInFlight();
  }

  private startProbes(): void {
    this.loadTimedOut.set(false);

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

    this.loadTimeoutId = setTimeout(() => {
      this.loadTimeoutId = null;
      // Only flip SHOW if something is still loading (warm API already resolved).
      if (
        this.writeups().status === 'loading' ||
        this.ctf().status === 'loading' ||
        this.projects().status === 'loading' ||
        this.experience().status === 'loading'
      ) {
        this.loadTimedOut.set(true);
      }
    }, SECTION_VISIBILITY_LOAD_TIMEOUT_MS);

    this.loadSub = forkJoin({
      writeups: this.countFrom('/writeups'),
      ctf: this.countFrom('/ctfs'),
      projects: this.countFrom('/projects'),
      // Use raw list endpoint — do NOT go through PortfolioService.getExperience()
      // (that pipe already noteRequestFailure + rethrows → double note).
      experience: this.countExperience(),
    }).subscribe({
      next: (counts) => {
        this.applyCount(this.writeups, counts.writeups);
        this.applyCount(this.ctf, counts.ctf);
        this.applyCount(this.projects, counts.projects);
        this.applyCount(this.experience, counts.experience);
        this.clearLoadTimeout();
        if (
          counts.writeups >= 0 ||
          counts.ctf >= 0 ||
          counts.projects >= 0 ||
          counts.experience >= 0
        ) {
          this.apiAvailability.markNetworkOk();
        }
      },
      error: () => {
        // forkJoin should not error (each stream catches), but be safe.
        this.applyCount(this.writeups, -1);
        this.applyCount(this.ctf, -1);
        this.applyCount(this.projects, -1);
        this.applyCount(this.experience, -1);
        this.clearLoadTimeout();
      },
    });
  }

  private cancelInFlight(): void {
    this.loadSub?.unsubscribe();
    this.loadSub = null;
    this.clearLoadTimeout();
  }

  private clearLoadTimeout(): void {
    if (this.loadTimeoutId != null) {
      clearTimeout(this.loadTimeoutId);
      this.loadTimeoutId = null;
    }
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

  private countExperience(): Observable<number> {
    return this.api.get<CountPage | unknown[]>('/portfolio/experience').pipe(
      map((r) => {
        if (Array.isArray(r)) {
          return r.length;
        }
        if (r && typeof r === 'object' && Array.isArray((r as CountPage).items)) {
          return (r as CountPage).items!.length;
        }
        return 0;
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
    if (state.status === 'error') {
      return true;
    }
    if (state.status === 'ready') {
      return state.count > 0;
    }
    // idle / loading: hide until cold-start timeout, then SHOW
    return this.loadTimedOut();
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
