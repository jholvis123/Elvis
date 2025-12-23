/**
 * Dynamic List Component
 * Componente reutilizable para listas dinámicas (skills, hints, tags, etc.)
 */

import { 
  Component, 
  Input, 
  Output, 
  EventEmitter,
  forwardRef
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { 
  ControlValueAccessor, 
  NG_VALUE_ACCESSOR,
  FormsModule
} from '@angular/forms';

@Component({
  selector: 'app-dynamic-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './dynamic-list.component.html',
  styleUrls: ['./dynamic-list.component.scss'],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => DynamicListComponent),
      multi: true
    }
  ]
})
export class DynamicListComponent implements ControlValueAccessor {
  // Configuración
  @Input() label: string = 'Items';
  @Input() placeholder: string = 'Nuevo item...';
  @Input() emptyMessage: string = 'No hay items';
  @Input() addButtonText: string = 'Agregar';
  @Input() maxItems: number = 10;
  @Input() minLength: number = 2;
  @Input() maxLength: number = 100;
  @Input() itemIcon: string = '•';
  @Input() showIndex: boolean = false;
  @Input() disabled: boolean = false;
  @Input() required: boolean = false;
  
  // Variantes visuales
  @Input() variant: 'default' | 'compact' | 'tags' = 'default';
  
  // Eventos
  @Output() itemsChange = new EventEmitter<string[]>();
  @Output() itemAdded = new EventEmitter<string>();
  @Output() itemRemoved = new EventEmitter<{ item: string; index: number }>();
  
  // Estado
  items: string[] = [];
  newItem: string = '';
  error: string = '';
  
  private onChange: (value: string[]) => void = () => {};
  private onTouched: () => void = () => {};
  
  // ============================================
  // GETTERS
  // ============================================
  
  get canAddMore(): boolean {
    return this.items.length < this.maxItems;
  }
  
  get isValidInput(): boolean {
    const trimmed = this.newItem.trim();
    return trimmed.length >= this.minLength && trimmed.length <= this.maxLength;
  }
  
  get itemCount(): string {
    return `${this.items.length}/${this.maxItems}`;
  }
  
  // ============================================
  // ACCIONES
  // ============================================
  
  addItem(): void {
    this.error = '';
    const value = this.newItem.trim();
    
    if (!value) return;
    
    // Validar longitud mínima
    if (value.length < this.minLength) {
      this.error = `Mínimo ${this.minLength} caracteres`;
      return;
    }
    
    // Validar longitud máxima
    if (value.length > this.maxLength) {
      this.error = `Máximo ${this.maxLength} caracteres`;
      return;
    }
    
    // Validar límite
    if (!this.canAddMore) {
      this.error = `Máximo ${this.maxItems} items`;
      return;
    }
    
    // Validar duplicados
    if (this.items.some(i => i.toLowerCase() === value.toLowerCase())) {
      this.error = 'Este item ya existe';
      return;
    }
    
    // Agregar
    this.items = [...this.items, value];
    this.newItem = '';
    this.updateValue();
    this.itemAdded.emit(value);
    this.onTouched();
  }
  
  removeItem(index: number): void {
    const removed = this.items[index];
    this.items.splice(index, 1);
    this.items = [...this.items];
    this.updateValue();
    this.itemRemoved.emit({ item: removed, index });
    this.onTouched();
  }
  
  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter') {
      event.preventDefault();
      this.addItem();
    }
  }
  
  clearAll(): void {
    this.items = [];
    this.newItem = '';
    this.error = '';
    this.updateValue();
    this.onTouched();
  }
  
  // ============================================
  // CONTROL VALUE ACCESSOR
  // ============================================
  
  writeValue(value: string[]): void {
    this.items = value || [];
  }
  
  registerOnChange(fn: (value: string[]) => void): void {
    this.onChange = fn;
  }
  
  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }
  
  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }
  
  private updateValue(): void {
    this.onChange(this.items);
    this.itemsChange.emit(this.items);
  }
}
