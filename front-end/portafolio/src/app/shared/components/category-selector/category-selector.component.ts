/**
 * Category Selector Component
 * Selector visual de categorías con iconos y descripción
 */

import { 
  Component, 
  Input, 
  Output, 
  EventEmitter,
  forwardRef
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { 
  CTFCategory, 
  CTF_CATEGORIES,
  CATEGORY_ATTACHMENT_CONFIG
} from '@core/models/ctf.model';

interface CategoryOption {
  value: CTFCategory;
  label: string;
  icon: string;
  description: string;
  attachmentInfo: string;
}

@Component({
  selector: 'app-category-selector',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './category-selector.component.html',
  styleUrls: ['./category-selector.component.scss'],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => CategorySelectorComponent),
      multi: true
    }
  ]
})
export class CategorySelectorComponent implements ControlValueAccessor {
  @Input() label: string = 'Categoría';
  @Input() required: boolean = true;
  @Input() disabled: boolean = false;
  @Input() showAttachmentInfo: boolean = true;
  @Input() compact: boolean = false;
  
  @Output() categoryChange = new EventEmitter<CTFCategory>();
  
  selectedCategory: CTFCategory | null = null;
  
  private onChange: (value: CTFCategory | null) => void = () => {};
  private onTouched: () => void = () => {};
  
  // Categorías con información de adjuntos
  get categories(): CategoryOption[] {
    return CTF_CATEGORIES.map(cat => ({
      ...cat,
      attachmentInfo: this.getAttachmentInfo(cat.value)
    }));
  }
  
  // ============================================
  // SELECCIÓN
  // ============================================
  
  selectCategory(category: CTFCategory): void {
    if (this.disabled) return;
    
    this.selectedCategory = category;
    this.onChange(category);
    this.onTouched();
    this.categoryChange.emit(category);
  }
  
  isSelected(category: CTFCategory): boolean {
    return this.selectedCategory === category;
  }
  
  // ============================================
  // INFORMACIÓN DE ADJUNTOS
  // ============================================
  
  private getAttachmentInfo(category: CTFCategory): string {
    const config = CATEGORY_ATTACHMENT_CONFIG[category];
    if (!config) return '';
    
    const types = config.requiredTypes.map(t => {
      switch(t) {
        case 'file': return '📎 Archivos';
        case 'url': return '🔗 URL';
        case 'docker': return '🐳 Docker';
        default: return t;
      }
    });
    
    return types.join(' · ');
  }
  
  getSelectedInfo(): string {
    if (!this.selectedCategory) return '';
    return this.getAttachmentInfo(this.selectedCategory);
  }
  
  // ============================================
  // CONTROL VALUE ACCESSOR
  // ============================================
  
  writeValue(value: CTFCategory | null): void {
    this.selectedCategory = value;
  }
  
  registerOnChange(fn: (value: CTFCategory | null) => void): void {
    this.onChange = fn;
  }
  
  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }
  
  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }
}
