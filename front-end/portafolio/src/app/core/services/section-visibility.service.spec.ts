import { fakeAsync, TestBed, tick } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { ApiAvailabilityService } from './api-availability.service';
import { ApiService } from './api.service';
import {
  SECTION_VISIBILITY_LOAD_TIMEOUT_MS,
  SectionVisibilityService,
} from './section-visibility.service';
import { environment } from '../../../environments/environment';

describe('SectionVisibilityService', () => {
  let service: SectionVisibilityService;
  let httpMock: HttpTestingController;
  let apiAvailability: jasmine.SpyObj<ApiAvailabilityService>;
  const apiBase = (environment.apiUrl || '').replace(/\/$/, '');

  function expectProbe(pathSuffix: string) {
    const req = httpMock.expectOne(
      (r) => r.url.startsWith(apiBase) && r.url.includes(pathSuffix)
    );
    expect(req.request.method).toBe('GET');
    return req;
  }

  function flushAllEmpty() {
    expectProbe('/writeups').flush({ items: [], total: 0, page: 1, size: 1, pages: 0 });
    expectProbe('/ctfs').flush({ items: [], total: 0, page: 1, size: 1, pages: 0 });
    expectProbe('/projects').flush({ items: [], total: 0, page: 1, size: 1, pages: 0 });
    expectProbe('/portfolio/experience').flush({ items: [] });
  }

  beforeEach(() => {
    apiAvailability = jasmine.createSpyObj<ApiAvailabilityService>(
      'ApiAvailabilityService',
      ['isApiConfigured', 'noteRequestFailure', 'markNetworkOk']
    );
    apiAvailability.isApiConfigured.and.returnValue(true);

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        SectionVisibilityService,
        ApiService,
        { provide: ApiAvailabilityService, useValue: apiAvailability },
      ],
    });

    service = TestBed.inject(SectionVisibilityService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('hides nav while loading before timeout (warm path, no flash)', fakeAsync(() => {
    service.ensureLoaded();
    expect(service.showWriteupsNav()).toBeFalse();
    expect(service.showCtfNav()).toBeFalse();

    tick(SECTION_VISIBILITY_LOAD_TIMEOUT_MS - 1);
    expect(service.showWriteupsNav()).toBeFalse();

    flushAllEmpty();
    tick(0);
    expect(service.showWriteupsNav()).toBeFalse();
  }));

  it('shows nav when no response by 2.5s (cold start timeout => SHOW)', fakeAsync(() => {
    service.ensureLoaded();
    expect(service.showWriteupsNav()).toBeFalse();

    tick(SECTION_VISIBILITY_LOAD_TIMEOUT_MS);
    expect(service.showWriteupsNav()).toBeTrue();
    expect(service.showCtfNav()).toBeTrue();
    expect(service.showProjectsNav()).toBeTrue();
    expect(service.showExperienceNav()).toBeTrue();

    // Resolve late empty — hide again (acceptable)
    flushAllEmpty();
    tick(0);
    expect(service.showWriteupsNav()).toBeFalse();
    expect(service.showCtfNav()).toBeFalse();
  }));

  it('hides nav when response count is 0 before timeout', fakeAsync(() => {
    service.ensureLoaded();
    flushAllEmpty();
    tick(0);
    expect(service.showWriteupsNav()).toBeFalse();
    expect(service.showProjectsNav()).toBeFalse();

    tick(SECTION_VISIBILITY_LOAD_TIMEOUT_MS);
    // still hidden — ready empty wins over timeout
    expect(service.showWriteupsNav()).toBeFalse();
  }));

  it('hides nav when late count 0 arrives after timeout SHOW', fakeAsync(() => {
    service.ensureLoaded();
    tick(SECTION_VISIBILITY_LOAD_TIMEOUT_MS);
    expect(service.showWriteupsNav()).toBeTrue();

    flushAllEmpty();
    tick(0);
    expect(service.showWriteupsNav()).toBeFalse();
  }));

  it('shows nav on error', fakeAsync(() => {
    service.ensureLoaded();

    expectProbe('/writeups').flush('fail', { status: 500, statusText: 'err' });
    expectProbe('/ctfs').flush('fail', { status: 500, statusText: 'err' });
    expectProbe('/projects').flush('fail', { status: 500, statusText: 'err' });
    expectProbe('/portfolio/experience').flush('fail', { status: 500, statusText: 'err' });
    tick(0);

    expect(service.showWriteupsNav()).toBeTrue();
    expect(service.showCtfNav()).toBeTrue();
    expect(apiAvailability.noteRequestFailure).toHaveBeenCalled();
  }));

  it('refresh() re-probes so nav can appear after publish without reload', fakeAsync(() => {
    service.ensureLoaded();
    flushAllEmpty();
    tick(0);
    expect(service.showWriteupsNav()).toBeFalse();

    service.refresh();
    expect(service.showWriteupsNav()).toBeFalse();

    expectProbe('/writeups').flush({ items: [{ id: '1' }], total: 1, page: 1, size: 1, pages: 1 });
    expectProbe('/ctfs').flush({ items: [], total: 0, page: 1, size: 1, pages: 0 });
    expectProbe('/projects').flush({ items: [], total: 0, page: 1, size: 1, pages: 0 });
    expectProbe('/portfolio/experience').flush({ items: [] });
    tick(0);

    expect(service.showWriteupsNav()).toBeTrue();
    expect(service.showCtfNav()).toBeFalse();
  }));
});
