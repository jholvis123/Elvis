import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CtfComponent } from './ctf.component';

describe('CtfComponent', () => {
  let component: CtfComponent;
  let fixture: ComponentFixture<CtfComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [CtfComponent]
    });
    fixture = TestBed.createComponent(CtfComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
