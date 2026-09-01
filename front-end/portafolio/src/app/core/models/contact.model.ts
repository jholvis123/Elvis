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

export type ContactMessageStatus = 'pending' | 'read' | 'replied';

export interface ContactMessage {
  id: string;
  name: string;
  email: string;
  project_type: string;
  message: string;
  status: ContactMessageStatus | string;
  created_at: string;
  read_at?: string | null;
  replied_at?: string | null;
}

export interface ContactListResponse {
  items: ContactMessage[];
  total: number;
  skip: number;
  limit: number;
}

export interface ContactInfoApi {
  email: string;
  github?: string | null;
  linkedin?: string | null;
  twitter?: string | null;
}
