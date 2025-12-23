export interface ContactForm {
  name: string;
  email: string;
  projectType: ProjectType;
  message: string;
}

export type ProjectType = 'web' | 'security' | 'ctf' | 'other';

export interface ContactInfo {
  type: 'email' | 'linkedin' | 'github' | 'twitter';
  label: string;
  value: string;
  url: string;
  icon: string;
}
