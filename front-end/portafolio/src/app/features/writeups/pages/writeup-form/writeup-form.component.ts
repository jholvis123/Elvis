import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CtfService } from '@core/services/ctf.service';
import { CTFChallenge } from '@core/models/ctf.model';
import { FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { WriteupForm, WriteupsService } from '@features/writeups/services/writeups.service';
import { NotificationService } from '@core/services/notification.service';


@Component({
    selector: 'app-writeup-form',
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule, RouterLink],
    templateUrl: './writeup-form.component.html',
    styleUrls: ['./writeup-form.component.scss']
})
export class WriteupFormComponent implements OnInit {
    writeupForm!: FormGroup;
    loading = false;
    error = '';
    isEditMode = false;
    writeupId: string | null = null;
    ctfs: CTFChallenge[] = [];

    constructor(
        private fb: FormBuilder,
        private route: ActivatedRoute,
        private router: Router,
        private writeupsService: WriteupsService,
        private ctfService: CtfService,
        private notificationService: NotificationService
    ) { }

    ngOnInit(): void {
        this.writeupId = this.route.snapshot.paramMap.get('id');
        this.isEditMode = !!this.writeupId;

        this.initForm();
        this.loadCtfs();

        if (this.isEditMode && this.writeupId) {
            this.loadWriteup(this.writeupId);
        }
    }

    initForm(): void {
        this.writeupForm = this.fb.group({
            title: ['', [Validators.required, Validators.minLength(5)]],
            ctf_id: [''],  // ✅ Opcional
            summary: ['', [Validators.required, Validators.maxLength(300)]],
            content: ['', [Validators.required, Validators.minLength(100)]],
            tools_used: this.fb.array([], Validators.required),
            techniques: this.fb.array([], Validators.required)
        });
    }

    loadCtfs(): void {
        this.ctfService.getChallengesFromApi({ showSolved: true }).subscribe({
            next: (ctfs) => {
                this.ctfs = ctfs.filter(c => c.isActive);
            },
            error: () => {
                console.error('Error loading CTFs');
                this.ctfs = [];
            }
        });
    }

    get tools(): FormArray {
        return this.writeupForm.get('tools_used') as FormArray;
    }

    get techniques(): FormArray {
        return this.writeupForm.get('techniques') as FormArray;
    }

    addTool(): void {
        this.tools.push(this.fb.control('', Validators.required));
    }

    removeTool(index: number): void {
        this.tools.removeAt(index);
    }

    addTechnique(): void {
        this.techniques.push(this.fb.control('', Validators.required));
    }

    removeTechnique(index: number): void {
        this.techniques.removeAt(index);
    }

    loadWriteup(id: string): void {
        this.loading = true;

        this.writeupsService.getWriteupById(id).subscribe({
            next: (writeup) => {
                this.writeupForm.patchValue({
                    title: writeup.title,
                    ctf_id: writeup.ctf_id,
                    summary: writeup.summary,
                    content: writeup.content
                });

                // Clear arrays first
                this.tools.clear();
                this.techniques.clear();

                writeup.tools_used.forEach(tool => {
                    this.tools.push(this.fb.control(tool, Validators.required));
                });

                writeup.techniques.forEach(technique => {
                    this.techniques.push(this.fb.control(technique, Validators.required));
                });

                this.loading = false;
            },
            error: () => {
                this.error = 'Error al cargar el writeup';
                this.loading = false;
            }
        });
    }

    onSubmit(): void {
        if (this.writeupForm.invalid) {
            this.markFormGroupTouched(this.writeupForm);
            return;
        }

        this.loading = true;
        this.error = '';

        const formData: WriteupForm = this.writeupForm.value;

        const request = this.isEditMode && this.writeupId
            ? this.writeupsService.updateWriteup(this.writeupId, formData)
            : this.writeupsService.createWriteup(formData);

        request.subscribe({
            next: (writeup) => {
                const message = this.isEditMode ? 'Writeup actualizado exitosamente' : 'Writeup creado exitosamente';
                this.notificationService.success(message);
                this.router.navigate(['/writeups', writeup.id]);
            },
            error: (err) => {
                this.error = err.message || 'Error al guardar el writeup';
                this.notificationService.error(this.error);
                this.loading = false;
            }
        });
    }

    private markFormGroupTouched(formGroup: FormGroup): void {
        Object.keys(formGroup.controls).forEach(key => {
            const control = formGroup.get(key);
            control?.markAsTouched();

            if (control instanceof FormGroup) {
                this.markFormGroupTouched(control);
            } else if (control instanceof FormArray) {
                control.controls.forEach(c => c.markAsTouched());
            }
        });
    }
}
