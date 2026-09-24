import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ProjectsService } from './projects.service';

describe('ProjectsService', () => {
    let service: ProjectsService;
    let httpMock: HttpTestingController;

    beforeEach(() => {
        TestBed.configureTestingModule({
            imports: [HttpClientTestingModule],
            providers: [ProjectsService]
        });
        service = TestBed.inject(ProjectsService);
        httpMock = TestBed.inject(HttpTestingController);
    });

    afterEach(() => {
        httpMock.verify();
    });

    it('should be created', () => {
        expect(service).toBeTruthy();
    });

    it('should get projects list', () => {
        const mockProjects = {
            items: [
                {
                    id: '1',
                    title: 'Test Project',
                    short_description: 'Test',
                    description: 'Full test',
                    technologies: ['Angular'],
                    featured: true
                }
            ],
            total: 1,
            page: 1,
            size: 10,
            pages: 1
        };

        service.getProjects().subscribe(response => {
            expect(response.items.length).toBe(1);
            expect(response.items[0].title).toBe('Test Project');
        });

        const req = httpMock.expectOne(req => req.url.includes('/projects'));
        expect(req.request.method).toBe('GET');
        req.flush(mockProjects);
    });

    it('should get featured projects', () => {
        const mockProjects = [
            {
                id: '1',
                title: 'Featured Project',
                technologies: ['React']
            }
        ];

        service.getFeaturedProjects(3).subscribe(projects => {
            expect(projects.length).toBe(1);
            expect(projects[0].title).toBe('Featured Project');
        });

        const req = httpMock.expectOne(req => req.url.includes('/projects/featured'));
        expect(req.request.method).toBe('GET');
        req.flush(mockProjects);
    });

    it('should get project by id', () => {
        const mockProject = {
            id: '1',
            title: 'Single Project',
            technologies: ['Vue']
        };

        service.getProjectById('1').subscribe(project => {
            expect(project.title).toBe('Single Project');
        });

        const req = httpMock.expectOne(req => req.url.includes('/projects/1'));
        expect(req.request.method).toBe('GET');
        req.flush(mockProject);
    });

    it('should create project', () => {
        const newProject = {
            title: 'New Project',
            short_description: 'Short',
            description: 'Full desc',
            image_url: 'http://example.com/img.jpg',
            technologies: ['Angular'],
            highlights: []
        };

        service.createProject(newProject).subscribe(project => {
            expect(project.title).toBe('New Project');
        });

        const req = httpMock.expectOne(req => req.url.includes('/projects'));
        expect(req.request.method).toBe('POST');
        expect(req.request.body).toEqual(newProject);
        req.flush({ ...newProject, id: '123' });
    });

    it('should normalize technologies map from API into an array', () => {
        const mapResponse = { Python: 4, Angular: 2 };

        service.getTechnologies().subscribe((techs) => {
            expect(Array.isArray(techs)).toBeTrue();
            expect(techs.length).toBe(2);
            expect(techs.find(t => t.technology === 'Python')?.count).toBe(4);
            expect(techs.find(t => t.technology === 'Angular')?.count).toBe(2);
        });

        const req = httpMock.expectOne(r => r.url.includes('/projects/technologies'));
        expect(req.request.method).toBe('GET');
        req.flush(mapResponse);
    });

    it('should pass through technologies array responses', () => {
        const arr = [{ technology: 'Docker', count: 3 }];

        service.getTechnologies().subscribe((techs) => {
            expect(techs).toEqual(arr);
        });

        const req = httpMock.expectOne(r => r.url.includes('/projects/technologies'));
        req.flush(arr);
    });
});
