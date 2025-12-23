import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { AuthService, LoginCredentials, RegisterData, AuthTokens, User } from './auth.service';
import { ApiService } from './api.service';

describe('AuthService', () => {
    let service: AuthService;
    let httpMock: HttpTestingController;
    let apiService: ApiService;

    const mockUser: User = {
        id: '123',
        email: 'test@example.com',
        username: 'testuser',
        is_active: true,
        is_admin: false,
        created_at: '2024-01-01T00:00:00Z'
    };

    const mockTokens: AuthTokens = {
        access_token: 'mock_access_token',
        refresh_token: 'mock_refresh_token',
        token_type: 'bearer',
        expires_in: 3600
    };

    beforeEach(() => {
        localStorage.clear();

        TestBed.configureTestingModule({
            imports: [HttpClientTestingModule],
            providers: [AuthService, ApiService]
        });

        service = TestBed.inject(AuthService);
        httpMock = TestBed.inject(HttpTestingController);
        apiService = TestBed.inject(ApiService);
    });

    afterEach(() => {
        httpMock.verify();
        localStorage.clear();
    });

    describe('Initial State', () => {
        it('should be created', () => {
            expect(service).toBeTruthy();
        });

        it('should start with no authenticated user', () => {
            expect(service.currentUser).toBeNull();
            expect(service.isAuthenticated).toBeFalse();
            expect(service.isAdmin).toBeFalse();
        });
    });

    describe('Token Management', () => {
        it('should return null when no access token is stored', () => {
            expect(service.getAccessToken()).toBeNull();
        });

        it('should return null when no refresh token is stored', () => {
            expect(service.getRefreshToken()).toBeNull();
        });

        it('should store and retrieve access token', () => {
            localStorage.setItem('access_token', 'test_token');
            expect(service.getAccessToken()).toBe('test_token');
        });
    });

    describe('Login', () => {
        it('should login successfully and store tokens', (done) => {
            const credentials: LoginCredentials = {
                email: 'test@example.com',
                password: 'password123'
            };

            // Setup localStorage mock for getCurrentUser
            localStorage.setItem('current_user', JSON.stringify(mockUser));

            service.login(credentials).subscribe({
                next: (user) => {
                    expect(user).toEqual(mockUser);
                    expect(service.getAccessToken()).toBe(mockTokens.access_token);
                    expect(service.getRefreshToken()).toBe(mockTokens.refresh_token);
                    expect(service.isAuthenticated).toBeTrue();
                    done();
                }
            });

            const req = httpMock.expectOne(request =>
                request.url.includes('/auth/login') && request.method === 'POST'
            );
            expect(req.request.body).toEqual(credentials);
            req.flush(mockTokens);
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
        it('should register a new user', (done) => {
            const registerData: RegisterData = {
                username: 'newuser',
                email: 'new@example.com',
                password: 'password123'
            };

            service.register(registerData).subscribe({
                next: (user) => {
                    expect(user).toBeTruthy();
                    expect(user.email).toBe(registerData.email);
                    done();
                }
            });

            const registerReq = httpMock.expectOne(request =>
                request.url.includes('/auth/register') && request.method === 'POST'
            );
            expect(registerReq.request.body).toEqual(registerData);
            registerReq.flush(mockUser);

            // Expect automatic login after registration
            const loginReq = httpMock.expectOne(request =>
                request.url.includes('/auth/login')
            );
            loginReq.flush(mockTokens);
        });
    });

    describe('Logout', () => {
        it('should clear tokens and user data', () => {
            // Setup authenticated state
            localStorage.setItem('access_token', 'token');
            localStorage.setItem('refresh_token', 'refresh');
            localStorage.setItem('current_user', JSON.stringify(mockUser));

            service.logout();

            expect(service.getAccessToken()).toBeNull();
            expect(service.getRefreshToken()).toBeNull();
            expect(service.currentUser).toBeNull();
            expect(service.isAuthenticated).toBeFalse();
        });
    });

    describe('Refresh Token', () => {
        it('should refresh access token', (done) => {
            localStorage.setItem('refresh_token', 'old_refresh_token');

            service.refreshToken().subscribe({
                next: (tokens) => {
                    expect(tokens.access_token).toBe('new_access_token');
                    expect(service.getAccessToken()).toBe('new_access_token');
                    done();
                }
            });

            const req = httpMock.expectOne(request =>
                request.url.includes('/auth/refresh') && request.method === 'POST'
            );
            req.flush({
                access_token: 'new_access_token',
                refresh_token: 'old_refresh_token',
                token_type: 'bearer',
                expires_in: 3600
            });
        });

        it('should logout on refresh token failure', (done) => {
            localStorage.setItem('refresh_token', 'invalid_token');
            localStorage.setItem('access_token', 'old_token');

            service.refreshToken().subscribe({
                next: () => {
                    expect(service.isAuthenticated).toBeFalse();
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
            const adminUser = { ...mockUser, is_admin: true };
            localStorage.setItem('current_user', JSON.stringify(adminUser));

            // Re-create service to load user from storage
            service = new AuthService(apiService);

            expect(service.isAdmin).toBeTrue();
        });

        it('should return false for non-admin user', () => {
            localStorage.setItem('current_user', JSON.stringify(mockUser));

            service = new AuthService(apiService);

            expect(service.isAdmin).toBeFalse();
        });
    });
});
