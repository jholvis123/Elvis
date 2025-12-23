import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CtfCardComponent } from './ctf-card.component';

describe('CtfCardComponent', () => {
  let component: CtfCardComponent;
  let fixture: ComponentFixture<CtfCardComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [CtfCardComponent]
    });
    fixture = TestBed.createComponent(CtfCardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
