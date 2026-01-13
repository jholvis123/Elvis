import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormArray } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ProjectsService, ProjectForm } from '../../services/projects.service';
import { NotificationService } from '../../../../core/services/notification.service';

@Component({
    selector: 'app-project-form',
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule, RouterLink],
    templateUrl: './project-form.component.html',
    styleUrls: ['./project-form.component.scss']
})
export class ProjectFormComponent implements OnInit {
    projectForm!: FormGroup;
    loading = false;
    error = '';
    isEditMode = false;
    projectId: string | null = null;

    constructor(
        private fb: FormBuilder,
        private route: ActivatedRoute,
        private router: Router,
        private projectsService: ProjectsService,
        private notificationService: NotificationService
    ) { }

    ngOnInit(): void {
        this.projectId = this.route.snapshot.paramMap.get('id');
        this.isEditMode = !!this.projectId;

        this.initForm();

        if (this.isEditMode && this.projectId) {
            this.loadProject(this.projectId);
        }
    }

    initForm(): void {
        this.projectForm = this.fb.group({
            title: ['', [Validators.required, Validators.minLength(3)]],
            short_description: ['', [Validators.required, Validators.maxLength(200)]],
            description: ['', [Validators.required, Validators.minLength(50)]],
            image_url: ['', [Validators.required]],
            github_url: [''],
            demo_url: [''],
            technologies: this.fb.array([], Validators.required),
            highlights: this.fb.array([]),
            featured: [false],
            order: [0]
        });
    }

    get technologies(): FormArray {
        return this.projectForm.get('technologies') as FormArray;
    }

    get highlights(): FormArray {
        return this.projectForm.get('highlights') as FormArray;
    }

    addTechnology(): void {
        this.technologies.push(this.fb.control('', Validators.required));
    }

    removeTechnology(index: number): void {
        this.technologies.removeAt(index);
    }

    addHighlight(): void {
        this.highlights.push(this.fb.control('', Validators.required));
    }

    removeHighlight(index: number): void {
        this.highlights.removeAt(index);
    }

    loadProject(id: string): void {
        this.loading = true;

        this.projectsService.getProjectById(id).subscribe({
            next: (project) => {
                this.projectForm.patchValue({
                    title: project.title,
                    short_description: project.short_description,
                    description: project.description,
                    image_url: project.image_url,
                    github_url: project.github_url || '',
                    demo_url: project.demo_url || '',
                    featured: project.featured,
                    order: project.order
                });

                // Load technologies
                project.technologies.forEach(tech => {
                    this.technologies.push(this.fb.control(tech, Validators.required));
                });

                // Load highlights
                project.highlights.forEach(highlight => {
                    this.highlights.push(this.fb.control(highlight, Validators.required));
                });

                this.loading = false;
            },
            error: () => {
                this.error = 'Error al cargar el proyecto';
                this.loading = false;
            }
        });
    }

    onSubmit(): void {
        if (this.projectForm.invalid) {
            this.markFormGroupTouched(this.projectForm);
            return;
        }

        this.loading = true;
        this.error = '';

        const formData: ProjectForm = this.projectForm.value;

        const request = this.isEditMode && this.projectId
            ? this.projectsService.updateProject(this.projectId, formData)
            : this.projectsService.createProject(formData);

        request.subscribe({
            next: (project) => {
                const message = this.isEditMode ? 'Proyecto actualizado exitosamente' : 'Proyecto creado exitosamente';
                this.notificationService.success(message);
                // Redirigir al panel de admin ya que los proyectos nuevos están en draft
                this.router.navigate(['/admin/projects']);
            },
            error: (err) => {
                this.error = err.message || 'Error al guardar el proyecto';
                this.notificationService.error(this.error);
                this.loading = false;
            }
        });
    }

    publishProject(): void {
        if (!this.projectId) return;

        this.projectsService.publishProject(this.projectId).subscribe({
            next: (project) => {
                this.notificationService.success('Proyecto publicado exitosamente');
                // Ahora sí podemos ir a la página pública porque está publicado
                this.router.navigate(['/projects', project.id]);
            },
            error: (err) => {
                this.notificationService.error('Error al publicar el proyecto');
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
                control.controls.forEach(c => {
                    c.markAsTouched();
                });
            }
        });
    }
}
