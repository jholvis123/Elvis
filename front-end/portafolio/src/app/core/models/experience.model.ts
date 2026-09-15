/** Alineado a ExperienceItemDTO (PR #48 / GET /portfolio/experience). */
export type ExperienceKind = 'project' | 'training' | 'security' | string;

export interface ExperienceLinks {
  github?: string | null;
  demo?: string | null;
}

export interface ExperienceItem {
  id: string;
  title: string;
  organization?: string | null;
  kind: ExperienceKind;
  location?: string | null;
  /** YYYY-MM */
  start_date: string;
  /** YYYY-MM o null */
  end_date: string | null;
  current: boolean;
  summary: string;
  highlights: string[];
  technologies: string[];
  links: ExperienceLinks;
  order: number;
}

export interface ExperienceListResponse {
  items: ExperienceItem[];
}

/** Alineado a CapabilitySkillDTO. */
export interface CapabilitySkill {
  name: string;
  category: string;
}

/** Alineado a CapabilitiesDTO (GET /portfolio/capabilities). */
export interface CapabilitiesResponse {
  roles: string[];
  skills: CapabilitySkill[];
}

/** Vista FE: chips derivados solo del endpoint de capabilities (no inventar stack). */
export interface CapabilityChip {
  label: string;
  kind: 'role' | 'skill';
  category?: string;
}
