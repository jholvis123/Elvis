export interface PortfolioSocialLinks {
  email?: string;
  github?: string;
  linkedin?: string;
  twitter?: string;
}

export interface PortfolioHighlight {
  label: string;
  value: string;
  icon?: string | null;
}

/** Contrato de GET/PUT /portfolio/profile (PortfolioProfileDTO). */
export interface PortfolioProfile {
  name: string;
  title: string;
  bio?: string | null;
  avatar_url?: string | null;
  roles: string[];
  stack_items: string[];
  about_points: string[];
  highlights: PortfolioHighlight[];
  social_links: PortfolioSocialLinks;
}

/** Contrato de POST /portfolio/avatar (201). No es PortfolioProfileDTO. */
export interface AvatarUploadResponse {
  avatar_url: string;
  id: string;
  filename: string;
  content_type: string;
  size: number;
}

/** Contrato de DELETE /portfolio/avatar. */
export interface AvatarDeleteResponse {
  avatar_url: null;
  message?: string;
}

