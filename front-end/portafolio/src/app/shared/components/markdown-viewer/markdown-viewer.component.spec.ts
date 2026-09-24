import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { MarkdownService } from 'ngx-markdown';
import { of } from 'rxjs';

import { MarkdownViewerComponent } from './markdown-viewer.component';
import { WriteupsService } from '../../../features/writeups/services/writeups.service';

describe('MarkdownViewerComponent', () => {
  let component: MarkdownViewerComponent;
  let fixture: ComponentFixture<MarkdownViewerComponent>;
  let clipboardWrite: jasmine.Spy;

  const htmlWithTwoPres = `
    <p>Intro</p>
    <pre><code class="language-python">print(1)</code></pre>
    <p>Mid</p>
    <pre><code class="language-text">n = 42</code></pre>
  `;

  const htmlWithOnePre = `
    <p>Only one</p>
    <pre><code class="language-js">const x = 1;</code></pre>
  `;

  beforeEach(async () => {
    const clipboard = navigator.clipboard ?? ({} as Clipboard);
    if (!navigator.clipboard) {
      Object.defineProperty(navigator, 'clipboard', {
        configurable: true,
        value: clipboard,
      });
    }
    clipboardWrite = spyOn(clipboard, 'writeText').and.returnValue(Promise.resolve());

    await TestBed.configureTestingModule({
      imports: [MarkdownViewerComponent],
      providers: [
        { provide: MarkdownService, useValue: { parse: (s: string) => `<p>${s}</p>` } },
        {
          provide: WriteupsService,
          useValue: { renderMarkdown: () => of(null) },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(MarkdownViewerComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('decorates each pre with exactly one copy button', fakeAsync(() => {
    fixture.componentRef.setInput('html', htmlWithTwoPres);
    fixture.detectChanges();
    tick(0);

    const root = fixture.nativeElement as HTMLElement;
    const pres = root.querySelectorAll('pre');
    const btns = root.querySelectorAll('.code-copy-btn');
    expect(pres.length).toBe(2);
    expect(btns.length).toBe(2);
  }));

  it('re-render replaces buttons so count still equals pre count (no duplicates)', fakeAsync(() => {
    fixture.componentRef.setInput('html', htmlWithTwoPres);
    fixture.detectChanges();
    tick(0);
    expect((fixture.nativeElement as HTMLElement).querySelectorAll('.code-copy-btn').length).toBe(2);

    fixture.componentRef.setInput('html', htmlWithOnePre);
    fixture.detectChanges();
    tick(0);

    const root = fixture.nativeElement as HTMLElement;
    expect(root.querySelectorAll('pre').length).toBe(1);
    expect(root.querySelectorAll('.code-copy-btn').length).toBe(1);
  }));

  it('copy button click calls navigator.clipboard.writeText', fakeAsync(() => {
    fixture.componentRef.setInput('html', htmlWithOnePre);
    fixture.detectChanges();
    tick(0);

    const btn = (fixture.nativeElement as HTMLElement).querySelector(
      '.code-copy-btn'
    ) as HTMLButtonElement;
    expect(btn).toBeTruthy();
    btn.click();
    tick(0);

    expect(clipboardWrite).toHaveBeenCalled();
    const arg = clipboardWrite.calls.mostRecent().args[0] as string;
    expect(arg).toContain('const x = 1');
    // Flush Copiado -> Copiar reset timer (2s)
    tick(2000);
  }));
});
