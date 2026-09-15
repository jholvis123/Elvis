import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { AuthService, LoginCredentials, RegisterData, AuthStatus, User } from './auth.service';
import { ApiService } from './api.service';
import { ApiAvailabilityService } from './api-availability.service';

describe('AuthService', () => {
    let service: AuthService;
    let httpMock: HttpTestingController;
    let apiAvailability: jasmine.SpyObj<ApiAvailabilityService>;

    const mockUser: User = {
        id: '123',
        email: 'test@example.com',
        username: 'testuser',
        is_active: true,
        is_admin: false,
        created_at: '2024-01-01T00:00:00Z'
    };

    const mockBearerStatus: AuthStatus = {
        authenticated: true,
        user: mockUser,
        expires_in: 3600,
        access_token: 'mock_access_token',
        refresh_token: 'mock_refresh_token',
        token_type: 'bearer'
    };

    const mockCookieStatus: AuthStatus = {
        authenticated: true,
        user: mockUser,
        expires_in: 3600,
        access_token: null,
        refresh_token: null,
        token_type: null
    };

    function setup(crossOrigin: boolean): void {
        localStorage.clear();
        sessionStorage.clear();

        apiAvailability = jasmine.createSpyObj('ApiAvailabilityService', [
            'isCrossOriginApi',
            'isApiConfigured',
            'isApiAvailable'
        ]);
        apiAvailability.isCrossOriginApi.and.returnValue(crossOrigin);

        TestBed.configureTestingModule({
            imports: [HttpClientTestingModule],
            providers: [
                AuthService,
                ApiService,
                { provide: ApiAvailabilityService, useValue: apiAvailability }
            ]
        });

        service = TestBed.inject(AuthService);
        httpMock = TestBed.inject(HttpTestingController);
    }

    afterEach(() => {
        httpMock.verify();
        localStorage.clear();
        sessionStorage.clear();
    });

    describe('Initial State (same-origin)', () => {
        beforeEach(() => setup(false));

        it('should be created', () => {
            expect(service).toBeTruthy();
        });

        it('should start with no authenticated user', () => {
            expect(service.currentUser).toBeNull();
            expect(service.isAuthenticated).toBeFalse();
            expect(service.isAdmin).toBeFalse();
        });

        it('should not use Bearer auth on same-origin', () => {
            expect(service.usesBearerAuth()).toBeFalse();
        });
    });

    describe('Token Management (Bearer / cross-origin)', () => {
        beforeEach(() => setup(true));

        it('should return null when no access token is stored', () => {
            expect(service.getAccessToken()).toBeNull();
        });

        it('should return null when no refresh token is stored', () => {
            expect(service.getRefreshToken()).toBeNull();
        });

        it('should use Bearer auth when API is cross-origin', () => {
            expect(service.usesBearerAuth()).toBeTrue();
        });
    });

    describe('Login (same-origin cookie mode)', () => {
        beforeEach(() => setup(false));

        it('should login without token_in_body and not store Bearer tokens', (done) => {
            const credentials: LoginCredentials = {
                email: 'test@example.com',
                password: 'password123'
            };

            service.login(credentials).subscribe({
                next: (user) => {
                    expect(user).toEqual(mockUser);
                    expect(service.getAccessToken()).toBeNull();
                    expect(service.getRefreshToken()).toBeNull();
                    expect(service.isAuthenticated).toBeTrue();
                    done();
                }
            });

            const req = httpMock.expectOne(request =>
                request.url.includes('/auth/login') && request.method === 'POST'
            );
            expect(req.request.body).toEqual(credentials);
            expect(req.request.body.token_in_body).toBeUndefined();
            req.flush(mockCookieStatus);
        });
    });

    describe('Login (Bearer / cross-origin)', () => {
        beforeEach(() => setup(true));

        it('should login with token_in_body and store tokens in sessionStorage', (done) => {
            const credentials: LoginCredentials = {
                email: 'test@example.com',
                password: 'password123'
            };

            service.login(credentials).subscribe({
                next: (user) => {
                    expect(user).toEqual(mockUser);
                    expect(service.getAccessToken()).toBe(mockBearerStatus.access_token!);
                    expect(service.getRefreshToken()).toBe(mockBearerStatus.refresh_token!);
                    expect(sessionStorage.getItem('access_token')).toBe(mockBearerStatus.access_token!);
                    expect(localStorage.getItem('access_token')).toBeNull();
                    expect(service.isAuthenticated).toBeTrue();
                    done();
                }
            });

            const req = httpMock.expectOne(request =>
                request.url.includes('/auth/login') && request.method === 'POST'
            );
            expect(req.request.body).toEqual({ ...credentials, token_in_body: true });
            req.flush(mockBearerStatus);
        });

        it('should fail honestly when cross-origin API omits Bearer tokens', (done) => {
            const credentials: LoginCredentials = {
                email: 'test@example.com',
                password: 'password123'
            };

            service.login(credentials).subscribe({
                error: (error) => {
                    expect(error.message).toContain('tokens Bearer');
                    expect(service.isAuthenticated).toBeFalse();
                    expect(service.getAccessToken()).toBeNull();
                    done();
                }
            });

            const req = httpMock.expectOne(request =>
                request.url.includes('/auth/login')
            );
            req.flush(mockCookieStatus);
        });

        it('should handle login error', (done) => {
            const credentials: LoginCredentials = {
                email: 'wrong@example.com',
                password: 'wrong'
            };

            service.login(credentials).subscribe({
                error: (error) => {
                    expect(error).toBeTruthy();
                    expect(service.isAuthenticated).toBeFalse();
                    done();
                }
            });

            const req = httpMock.expectOne(request =>
                request.url.includes('/auth/login')
            );
            req.flush({ detail: 'Invalid credentials' }, { status: 401, statusText: 'Unauthorized' });
        });
    });

    describe('Register', () => {
        beforeEach(() => setup(false));

        it('should register a new user then login', (done) => {
            const registerData: RegisterData = {
                username: 'newuser',
                email: 'new@example.com',
                password: 'password123'
            };

            service.register(registerData).subscribe({
                next: (user) => {
                    expect(user).toBeTruthy();
                    expect(user.email).toBe(mockUser.email);
                    done();
                }
            });

            const registerReq = httpMock.expectOne(request =>
                request.url.includes('/auth/register') && request.method === 'POST'
            );
            expect(registerReq.request.body).toEqual(registerData);
            registerReq.flush(mockUser);

            const loginReq = httpMock.expectOne(request =>
                request.url.includes('/auth/login')
            );
            loginReq.flush(mockCookieStatus);
        });
    });

    describe('Logout', () => {
        beforeEach(() => setup(true));

        it('should clear tokens and user data', (done) => {
            sessionStorage.setItem('access_token', 'token');
            sessionStorage.setItem('refresh_token', 'refresh');
            localStorage.setItem('current_user', JSON.stringify(mockUser));

            service.logout().subscribe({
                next: () => {
                    expect(service.getAccessToken()).toBeNull();
                    expect(service.getRefreshToken()).toBeNull();
                    expect(service.currentUser).toBeNull();
                    expect(service.isAuthenticated).toBeFalse();
                    done();
                }
            });

            const req = httpMock.expectOne(request =>
                request.url.includes('/auth/logout') && request.method === 'POST'
            );
            req.flush({ message: 'Logged out successfully' });
        });
    });

    describe('Refresh Token (Bearer)', () => {
        beforeEach(() => setup(true));

        it('should refresh with refresh_token + token_in_body and store new tokens', (done) => {
            sessionStorage.setItem('refresh_token', 'old_refresh_token');

            service.refreshToken().subscribe({
                next: (status) => {
                    expect(status.access_token).toBe('new_access_token');
                    expect(service.getAccessToken()).toBe('new_access_token');
                    expect(service.getRefreshToken()).toBe('new_refresh_token');
                    done();
                }
            });

            const req = httpMock.expectOne(request =>
                request.url.includes('/auth/refresh') && request.method === 'POST'
            );
            expect(req.request.body).toEqual({
                refresh_token: 'old_refresh_token',
                token_in_body: true
            });
            req.flush({
                authenticated: true,
                user: mockUser,
                expires_in: 3600,
                access_token: 'new_access_token',
                refresh_token: 'new_refresh_token',
                token_type: 'bearer'
            });
        });

        it('should clear auth on refresh token failure', (done) => {
            sessionStorage.setItem('refresh_token', 'invalid_token');
            sessionStorage.setItem('access_token', 'old_token');
            localStorage.setItem('current_user', JSON.stringify(mockUser));

            service.refreshToken().subscribe({
                next: (status) => {
                    expect(status.authenticated).toBeFalse();
                    expect(service.isAuthenticated).toBeFalse();
                    expect(service.getAccessToken()).toBeNull();
                    done();
                }
            });

            const req = httpMock.expectOne(request =>
                request.url.includes('/auth/refresh')
            );
            req.flush({ detail: 'Invalid token' }, { status: 401, statusText: 'Unauthorized' });
        });
    });

    describe('Get Current User', () => {
        beforeEach(() => setup(false));

        it('should fetch and store current user', (done) => {
            service.getCurrentUser().subscribe({
                next: (user) => {
                    expect(user).toEqual(mockUser);
                    expect(service.currentUser).toEqual(mockUser);
                    done();
                }
            });

            const req = httpMock.expectOne(request =>
                request.url.includes('/auth/me') && request.method === 'GET'
            );
            req.flush(mockUser);
        });
    });

    describe('Admin Check', () => {
        it('should return true for admin user', () => {
            setup(false);
            const adminUser = { ...mockUser, is_admin: true };
            localStorage.setItem('current_user', JSON.stringify(adminUser));

            const api = TestBed.inject(ApiService);
            service = new AuthService(api, apiAvailability);

            const req = httpMock.expectOne(r => r.url.includes('/auth/me'));
            req.flush(adminUser);

            expect(service.isAdmin).toBeTrue();
        });

        it('should return false for non-admin user', () => {
            setup(false);
            localStorage.setItem('current_user', JSON.stringify(mockUser));

            const api = TestBed.inject(ApiService);
            service = new AuthService(api, apiAvailability);

            const req = httpMock.expectOne(r => r.url.includes('/auth/me'));
            req.flush(mockUser);

            expect(service.isAdmin).toBeFalse();
        });
    });
});
