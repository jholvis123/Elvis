import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { WriteupsService } from './writeups.service';

describe('WriteupsService', () => {
    let service: WriteupsService;
    let httpMock: HttpTestingController;

    beforeEach(() => {
        TestBed.configureTestingModule({
            imports: [HttpClientTestingModule],
            providers: [WriteupsService]
        });
        service = TestBed.inject(WriteupsService);
        httpMock = TestBed.inject(HttpTestingController);
    });

    afterEach(() => {
        httpMock.verify();
    });

    it('should be created', () => {
        expect(service).toBeTruthy();
    });

    it('should get writeups list with pagination', () => {
        const mockResponse = {
            items: [
                {
                    id: '1',
                    title: 'CTF Writeup 1',
                    summary: 'Writeup summary',
                    tools_used: ['nmap', 'burp'],
                    techniques: ['sqli']
                }
            ],
            total: 1,
            page: 1,
            size: 10,
            pages: 1
        };

        service.getWriteups({ page: 1, size: 10 }).subscribe(response => {
            expect(response.items.length).toBe(1);
            expect(response.items[0].title).toBe('CTF Writeup 1');
        });

        const req = httpMock.expectOne(req => req.url.includes('/writeups'));
        expect(req.request.method).toBe('GET');
        req.flush(mockResponse);
    });

    it('should get popular writeups', () => {
        const mockWriteups = [
            {
                id: '1',
                title: 'Popular Writeup',
                views: 1000
            }
        ];

        service.getPopularWriteups(5).subscribe(writeups => {
            expect(writeups.length).toBe(1);
            expect(writeups[0].views).toBe(1000);
        });

        const req = httpMock.expectOne(req => req.url.includes('/writeups/popular'));
        expect(req.request.method).toBe('GET');
        req.flush(mockWriteups);
    });

    it('should create writeup', () => {
        const newWriteup = {
            title: 'New Writeup',
            ctf_id: 'ctf-123',
            summary: 'Summary',
            content: 'Full content here',
            tools_used: ['metasploit'],
            techniques: ['buffer overflow']
        };

        service.createWriteup(newWriteup).subscribe(writeup => {
            expect(writeup.title).toBe('New Writeup');
        });

        const req = httpMock.expectOne(req => req.url.includes('/writeups'));
        expect(req.request.method).toBe('POST');
        expect(req.request.body).toEqual(newWriteup);
        req.flush({ ...newWriteup, id: '456' });
    });

    it('should publish writeup', () => {
        const publishedWriteup = {
            id: '1',
            title: 'Published',
            status: 'published'
        };

        service.publishWriteup('1').subscribe(writeup => {
            expect(writeup.status).toBe('published');
        });

        const req = httpMock.expectOne(req => req.url.includes('/writeups/1/publish'));
        expect(req.request.method).toBe('POST');
        req.flush(publishedWriteup);
    });
});
