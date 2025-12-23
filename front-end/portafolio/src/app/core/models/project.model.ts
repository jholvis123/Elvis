export interface Project {
  id: string;
  title: string;
  description: string;
  tags: string[];
  cta: string;
  year: number;
  category: 'web' | 'security' | 'ctf' | 'other';
  imageUrl?: string;
  demoUrl?: string;
  repoUrl?: string;
}
