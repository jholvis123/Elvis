export type ProjectStatus = 'draft' | 'published' | 'archived';

/**
 * Proyecto tal como lo expone la API. Home y cards usan el resumen
 * (`ProjectSummary`); el detalle/admin usan este modelo completo.
 */
export interface Project {
  id: string;
  title: string;
  description: string;
  short_description: string;
  image_url: string;
  github_url?: string;
  demo_url?: string;
  technologies: string[];
  highlights: string[];
  status: ProjectStatus;
  featured: boolean;
  order: number;
  created_at: string;
  updated_at: string;
}

/** Resumen para cards del Home y listados compactos. */
export interface ProjectSummary {
  id: string;
  title: string;
  short_description: string;
  image_url: string;
  technologies: string[];
  featured: boolean;
  created_at: string;
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ProjectForm {
  title: string;
  description: string;
  short_description: string;
  image_url: string;
  github_url?: string;
  demo_url?: string;
  technologies: string[];
  highlights: string[];
  featured?: boolean;
  order?: number;
  status?: ProjectStatus;
}
