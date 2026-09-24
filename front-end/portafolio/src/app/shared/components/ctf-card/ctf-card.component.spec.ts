import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { CtfCardComponent, stripMarkdownToPlain } from './ctf-card.component';
import { CTFChallenge } from '@core/models/ctf.model';

describe('CtfCardComponent', () => {
  let component: CtfCardComponent;
  let fixture: ComponentFixture<CtfCardComponent>;

  const mockChallenge: CTFChallenge = {
    id: 'test-id',
    title: 'Test Challenge',
    description: 'Intro\n\n```\nn = 1234567890123456789012345678901234567890\n```\n\nMore **text**.',
    category: 'crypto',
    difficulty: 'easy',
    points: 100,
    solvedCount: 0,
    skills: ['RSA'],
    hints: [],
    attachments: [],
    author: 'Elvis',
    createdAt: new Date(),
    isActive: true,
    solved: false,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [CtfCardComponent],
      providers: [provideRouter([])]
    });
    fixture = TestBed.createComponent(CtfCardComponent);
    component = fixture.componentInstance;
    component.challenge = mockChallenge;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should strip markdown fences from description preview', () => {
    const preview = component.descriptionPreview;
    expect(preview).not.toContain('```');
    expect(preview).not.toContain('1234567890123456789012345678901234567890');
    expect(preview).toContain('Intro');
    expect(preview).toContain('More text');
  });
});

describe('stripMarkdownToPlain', () => {
  it('removes fenced blocks and emphasis', () => {
    const out = stripMarkdownToPlain('Hi\n```\ncode\n```\n**bold**');
    expect(out).toBe('Hi bold');
  });
});
