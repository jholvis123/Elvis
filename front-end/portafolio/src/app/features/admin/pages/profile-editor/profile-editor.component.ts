import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
    AbstractControl,
    FormArray,
    FormBuilder,
    FormGroup,
    ReactiveFormsModule,
    Validators
} from '@angular/forms';
import { RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { PortfolioService } from '../../../../core/services/portfolio.service';
import { NotificationService } from '../../../../core/services/notification.service';
import { ApiError } from '../../../../core/services/api.service';
import {
    PortfolioHighlight,
    PortfolioProfile,
    PortfolioSocialLinks
} from '../../../../core/models/portfolio.model';
import { IconComponent, IconName, HIGHLIGHT_ICON_NAMES } from '@shared/icons/icon.component';
import { ConfirmDialogComponent } from '@shared/components/confirm-dialog/confirm-dialog.component';
import { DynamicListComponent } from '@shared/components/dynamic-list/dynamic-list.component';

@Component({
    selector: 'app-profile-editor',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        RouterLink,
        IconComponent,
        ConfirmDialogComponent,
        DynamicListComponent
    ],
    templateUrl: './profile-editor.component.html'
})
export class ProfileEditorComponent implements OnInit {
    private readonly fb = inject(FormBuilder);
    private readonly portfolioService = inject(PortfolioService);
    private readonly notificationService = inject(NotificationService);
    private readonly destroyRef = inject(DestroyRef);

    readonly highlightIcons: IconName[] = [...HIGHLIGHT_ICON_NAMES];

    form: FormGroup = this.fb.group({
        name: ['', [Validators.required, Validators.minLength(2)]],
        title: ['', [Validators.required, Validators.minLength(2)]],
        bio: [''],
        avatar_url: [''],
        roles: this.fb.control<string[]>([]),
        stack_items: this.fb.control<string[]>([]),
        about_points: this.fb.control<string[]>([]),
        highlights: this.fb.array([]),
        email: ['', [Validators.email]],
        github: [''],
        linkedin: ['']
    });

    loading = true;
    saving = false;
    errorMessage = '';
    saveError = '';
    showConfirm = false;
    loaded = false;

    ngOnInit(): void {
        this.loadProfile();
    }

    get highlights(): FormArray {
        return this.form.get('highlights') as FormArray;
    }

    highlightGroup(control: AbstractControl): FormGroup {
        return control as FormGroup;
    }

    isKnownIcon(name: string | null | undefined): name is IconName {
        return !!name && (HIGHLIGHT_ICON_NAMES as readonly string[]).includes(name);
    }

    previewIcon(control: AbstractControl): IconName {
        const name = (control as FormGroup).get('icon')?.value as string | null;
        return this.isKnownIcon(name) ? name : 'folder';
    }

    loadProfile(): void {
        this.loading = true;
        this.errorMessage = '';
        this.saveError = '';
        this.loaded = false;

        this.portfolioService.getProfile().pipe(
            takeUntilDestroyed(this.destroyRef)
        ).subscribe({
            next: (profile) => {
                this.applyProfile(profile);
                this.loaded = true;
                this.loading = false;
            },
            error: (err: unknown) => {
                this.loading = false;
                this.loaded = false;
                this.errorMessage = this.humanLoadError(err);
            }
        });
    }

    addHighlight(): void {
        this.highlights.push(this.buildHighlightGroup());
        this.form.markAsDirty();
    }

    removeHighlight(index: number): void {
        this.highlights.removeAt(index);
        this.form.markAsDirty();
    }

    requestSave(): void {
        if (this.form.invalid) {
            this.form.markAllAsTouched();
            this.saveError = 'Revisa los campos marcados antes de guardar.';
            return;
        }
        this.saveError = '';
        this.showConfirm = true;
    }

    cancelSave(): void {
        this.showConfirm = false;
    }

    executeSave(): void {
        if (this.form.invalid) {
            this.showConfirm = false;
            return;
        }

        const body = this.toPutBody();
        this.saving = true;
        this.saveError = '';

        this.portfolioService.updateProfile(body).pipe(
            takeUntilDestroyed(this.destroyRef)
        ).subscribe({
            next: (saved) => {
                this.saving = false;
                this.showConfirm = false;
                this.applyProfile(saved);
                this.form.markAsPristine();
                this.notificationService.success('Perfil actualizado');
            },
            error: (err: unknown) => {
                this.saving = false;
                this.showConfirm = false;
                this.saveError = this.humanSaveError(err);
            }
        });
    }

    private applyProfile(profile: PortfolioProfile): void {
        this.highlights.clear();
        const highlights = profile.highlights ?? [];
        highlights.forEach((h) => this.highlights.push(this.buildHighlightGroup(h)));

        const social = profile.social_links || {};
        this.form.patchValue({
            name: profile.name || '',
            title: profile.title || '',
            bio: profile.bio || '',
            avatar_url: profile.avatar_url || '',
            roles: profile.roles || [],
            stack_items: profile.stack_items || [],
            about_points: profile.about_points || [],
            email: social.email || '',
            github: social.github || '',
            linkedin: social.linkedin || ''
        });
        this.form.markAsPristine();
    }

    private buildHighlightGroup(h?: PortfolioHighlight): FormGroup {
        const icon = h?.icon || 'folder';
        if (icon && !this.highlightIcons.includes(icon as IconName)) {
            this.highlightIcons.push(icon as IconName);
        }
        return this.fb.group({
            label: [h?.label || '', Validators.required],
            value: [h?.value || '', Validators.required],
            icon: [icon]
        });
    }

    private toPutBody(): PortfolioProfile {
        const raw = this.form.getRawValue() as {
            name: string;
            title: string;
            bio: string;
            avatar_url: string;
            roles: string[];
            stack_items: string[];
            about_points: string[];
            email: string;
            github: string;
            linkedin: string;
        };

        const highlights: PortfolioHighlight[] = this.highlights.controls.map((ctrl) => {
            const value = (ctrl as FormGroup).getRawValue() as PortfolioHighlight;
            const icon = (value.icon || '').trim();
            return {
                label: (value.label || '').trim(),
                value: (value.value || '').trim(),
                icon: icon || null
            };
        });

        const social_links: PortfolioSocialLinks = {
            email: (raw.email || '').trim(),
            github: (raw.github || '').trim(),
            linkedin: (raw.linkedin || '').trim()
        };

        return {
            name: raw.name.trim(),
            title: raw.title.trim(),
            bio: (raw.bio || '').trim() || null,
            avatar_url: (raw.avatar_url || '').trim() || null,
            roles: (raw.roles || []).map((item) => item.trim()).filter(Boolean),
            stack_items: (raw.stack_items || []).map((item) => item.trim()).filter(Boolean),
            about_points: (raw.about_points || []).map((item) => item.trim()).filter(Boolean),
            highlights,
            social_links
        };
    }

    private humanLoadError(err: unknown): string {
        if (err instanceof ApiError) {
            if (err.status === 404) {
                return 'No se encontró el perfil del portafolio.';
            }
            if (err.status === 401) {
                return err.message || 'Sesión expirada. Inicia sesión de nuevo.';
            }
            if (err.status === 403) {
                return err.message || 'No tienes permisos para ver este perfil.';
            }
            return err.message || 'No se pudo cargar el perfil.';
        }
        if (err instanceof Error && err.message) {
            return err.message;
        }
        return 'No se pudo cargar el perfil.';
    }

    private humanSaveError(err: unknown): string {
        if (err instanceof ApiError) {
            if (err.status === 404) {
                return 'La actualización de perfil aún no está disponible. El servidor no expone PUT /portfolio/profile (backend PR #34).';
            }
            if (err.status === 401) {
                return err.message || 'Sesión expirada. Inicia sesión de nuevo.';
            }
            if (err.status === 403) {
                return err.message || 'No tienes permisos de administrador para actualizar el perfil.';
            }
            if (err.status === 422) {
                return err.message || 'Los datos del perfil no son válidos. Revisa los campos.';
            }
            return err.message || 'No se pudo guardar el perfil.';
        }
        if (err instanceof Error && err.message) {
            return err.message;
        }
        return 'No se pudo guardar el perfil.';
    }
}
