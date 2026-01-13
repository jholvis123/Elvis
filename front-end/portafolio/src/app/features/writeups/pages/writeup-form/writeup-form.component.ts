import { Component, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CtfService } from '@core/services/ctf.service';
import { CTFChallenge } from '@core/models/ctf.model';
import { FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { WriteupForm, WriteupsService } from '@features/writeups/services/writeups.service';
import { NotificationService } from '@core/services/notification.service';
import { MarkdownEditorComponent } from '../../../../shared/components/markdown-editor/markdown-editor.component';
import { Subject, debounceTime, distinctUntilChanged, takeUntil } from 'rxjs';


@Component({
    selector: 'app-writeup-form',
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule, RouterLink, MarkdownEditorComponent],
    templateUrl: './writeup-form.component.html',
    styleUrls: ['./writeup-form.component.scss']
})
export class WriteupFormComponent implements OnInit {
    @ViewChild(MarkdownEditorComponent) markdownEditor!: MarkdownEditorComponent;
    
    writeupForm!: FormGroup;
    loading = false;
    error = '';
    isEditMode = false;
    writeupId: string | null = null;
    ctfs: CTFChallenge[] = [];
    
    private destroy$ = new Subject<void>();
    private autosave$ = new Subject<string>();
    autosaveEnabled = true;

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
        this.setupAutosave();

        if (this.isEditMode && this.writeupId) {
            this.loadWriteup(this.writeupId);
        } else {
            // Cargar draft desde localStorage
            this.loadDraft();
        }
    }
    
    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    initForm(): void {
        this.writeupForm = this.fb.group({
            title: ['', [Validators.required, Validators.minLength(5)]],
            ctf_id: [''],
            summary: ['', [Validators.maxLength(500)]],
            content: ['', [Validators.required, Validators.minLength(100)]],
            tools_used: this.fb.array([]),
            techniques: this.fb.array([])
        });
    }
    
    private setupAutosave(): void {
        this.autosave$.pipe(
            takeUntil(this.destroy$),
            debounceTime(3000),
            distinctUntilChanged()
        ).subscribe(() => {
            if (!this.isEditMode && this.autosaveEnabled) {
                this.saveDraft();
            }
        });
    }
    
    private saveDraft(): void {
        const draft = this.writeupForm.value;
        localStorage.setItem('writeup_draft', JSON.stringify(draft));
    }
    
    private loadDraft(): void {
        const draftStr = localStorage.getItem('writeup_draft');
        if (draftStr) {
            try {
                const draft = JSON.parse(draftStr);
                this.writeupForm.patchValue({
                    title: draft.title || '',
                    ctf_id: draft.ctf_id || '',
                    summary: draft.summary || '',
                    content: draft.content || ''
                });
                
                // Cargar tools
                this.tools.clear();
                (draft.tools_used || []).forEach((tool: string) => {
                    if (tool) this.tools.push(this.fb.control(tool, Validators.required));
                });
                
                // Cargar techniques
                this.techniques.clear();
                (draft.techniques || []).forEach((tech: string) => {
                    if (tech) this.techniques.push(this.fb.control(tech, Validators.required));
                });
                
                this.notificationService.info('Borrador recuperado');
            } catch (e) {
                console.error('Error loading draft:', e);
            }
        }
    }
    
    private clearDraft(): void {
        localStorage.removeItem('writeup_draft');
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
    
    // Handler para el editor Markdown
    onContentChange(content: string): void {
        this.writeupForm.patchValue({ content });
        this.autosave$.next(content);
    }
    
    onEditorSave(content: string): void {
        // Autosave triggered by editor
        if (!this.isEditMode) {
            this.saveDraft();
            this.notificationService.info('Borrador guardado automáticamente');
        }
    }

    loadWriteup(id: string): void {
        this.loading = true;

        this.writeupsService.getWriteupById(id).subscribe({
            next: (writeup) => {
                this.writeupForm.patchValue({
                    title: writeup.title,
                    ctf_id: writeup.ctf_id || '',
                    summary: writeup.summary || '',
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
            this.notificationService.error('Por favor, corrige los errores del formulario');
            return;
        }

        this.loading = true;
        this.error = '';

        const formData: WriteupForm = {
            ...this.writeupForm.value,
            ctf_id: this.writeupForm.value.ctf_id || undefined,
            tools_used: this.tools.value.filter((t: string) => t.trim()),
            techniques: this.techniques.value.filter((t: string) => t.trim())
        };

        const request = this.isEditMode && this.writeupId
            ? this.writeupsService.updateWriteup(this.writeupId, formData)
            : this.writeupsService.createWriteup(formData);

        request.subscribe({
            next: (writeup) => {
                const message = this.isEditMode ? 'Writeup actualizado exitosamente' : 'Writeup creado exitosamente';
                this.notificationService.success(message);
                this.clearDraft();
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
