
export type CTFCategory = 'web' | 'crypto' | 'forensics' | 'pwn' | 'reverse' | 'misc' | 'osint' | 'stego';

export type CTFDifficulty = 'easy' | 'medium' | 'hard' | 'insane';

export type AttachmentType = 'file' | 'url' | 'docker';

// INTERFACES PRINCIPALES

export interface CTFChallenge {
  id: string;
  title: string;
  description: string;
  category: CTFCategory;
  difficulty: CTFDifficulty;
  points: number;
  skills: string[];
  hints?: string[];
  flag?: string;              // Solo visible para admin
  author: string;
  createdAt: Date;
  solvedCount: number;
  isActive: boolean;
  solved?: boolean;           // Estado de resolución para el usuario actual
  attachments?: CTFAttachment[];
}

export interface CTFAttachment {
  id: string;
  name: string;
  type: AttachmentType;
  url: string;
  size?: number;              // bytes (solo para archivos)
  mimeType?: string;          // MIME type del archivo
  uploadedAt?: Date;
}

export interface CTFSubmission {
  challengeId: string;
  flag: string;
  userId?: string;
  submittedAt: Date;
  isCorrect?: boolean;
}

export interface CTFFilter {
  category?: CTFCategory | 'all';
  difficulty?: CTFDifficulty | 'all';
  search?: string;
  showSolved?: boolean;
}

export interface CTFStats {
  totalChallenges: number;
  solvedChallenges: number;
  totalPoints: number;
  earnedPoints: number;
}

// Form para crear/editar retos (admin)
export interface CTFChallengeForm {
  title: string;
  description: string;
  category: CTFCategory;
  difficulty: CTFDifficulty;
  platform: string;
  points: number;
  skills: string[];
  hints: string[];
  flag: string;
  isActive: boolean;
  attachments: CTFAttachment[];
}

// Resultado de validación
export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

// ============================================
// CONFIGURACIÓN DE ADJUNTOS POR CATEGORÍA
// ============================================

export interface CategoryAttachmentConfig {
  category: CTFCategory;
  label: string;
  description: string;
  requiredTypes: AttachmentType[];
  allowedMimeTypes: string[];
  maxFileSize: number;        // bytes
  maxFiles: number;
  allowedExtensions: string[];
  urlPatterns?: RegExp[];
}

export const CATEGORY_ATTACHMENT_CONFIG: Record<CTFCategory, CategoryAttachmentConfig> = {
  web: {
    category: 'web',
    label: 'Web',
    description: 'Retos de seguridad web: SQL injection, XSS, CSRF, etc.',
    requiredTypes: ['url'],
    allowedMimeTypes: [],
    maxFileSize: 0,
    maxFiles: 0,
    allowedExtensions: [],
    urlPatterns: [/^https?:\/\/.+/]
  },
  crypto: {
    category: 'crypto',
    label: 'Criptografía',
    description: 'Cifrado, hashing, criptoanálisis',
    requiredTypes: ['file'],
    allowedMimeTypes: ['text/plain', 'application/octet-stream', 'application/json'],
    maxFileSize: 5 * 1024 * 1024,  // 5MB
    maxFiles: 3,
    allowedExtensions: ['.txt', '.enc', '.bin', '.json', '.pem', '.key']
  },
  stego: {
    category: 'stego',
    label: 'Esteganografía',
    description: 'Datos ocultos en imágenes, audio o video',
    requiredTypes: ['file'],
    allowedMimeTypes: ['image/*', 'audio/*', 'video/*'],
    maxFileSize: 50 * 1024 * 1024,  // 50MB
    maxFiles: 5,
    allowedExtensions: ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.wav', '.mp3', '.mp4', '.avi']
  },
  forensics: {
    category: 'forensics',
    label: 'Forense',
    description: 'Análisis de memoria, tráfico de red, sistemas de archivos',
    requiredTypes: ['file'],
    allowedMimeTypes: [
      'image/*',
      'application/vnd.tcpdump.pcap',
      'application/x-pcapng',
      'application/octet-stream',
      'audio/*'
    ],
    maxFileSize: 100 * 1024 * 1024,  // 100MB
    maxFiles: 5,
    allowedExtensions: ['.pcap', '.pcapng', '.raw', '.mem', '.img', '.dd', '.E01', '.png', '.jpg', '.wav']
  },
  reverse: {
    category: 'reverse',
    label: 'Ingeniería Inversa',
    description: 'Análisis de binarios, malware, crackmes',
    requiredTypes: ['file'],
    allowedMimeTypes: [
      'application/x-executable',
      'application/x-dosexec',
      'application/x-elf',
      'application/octet-stream',
      'application/x-msdownload'
    ],
    maxFileSize: 50 * 1024 * 1024,  // 50MB
    maxFiles: 2,
    allowedExtensions: ['.exe', '.elf', '.bin', '.so', '.dll', '.apk', '.jar']
  },
  pwn: {
    category: 'pwn',
    label: 'Pwn/Exploit',
    description: 'Buffer overflow, ROP chains, explotación de binarios',
    requiredTypes: ['file', 'docker'],
    allowedMimeTypes: ['application/x-executable', 'application/x-elf', 'application/octet-stream'],
    maxFileSize: 50 * 1024 * 1024,  // 50MB
    maxFiles: 2,
    allowedExtensions: ['.elf', '.bin', '.c', '.py']
  },
  misc: {
    category: 'misc',
    label: 'Miscelánea',
    description: 'Retos variados que no encajan en otras categorías',
    requiredTypes: ['file', 'url'],
    allowedMimeTypes: ['*/*'],
    maxFileSize: 20 * 1024 * 1024,  // 20MB
    maxFiles: 5,
    allowedExtensions: ['*']
  },
  osint: {
    category: 'osint',
    label: 'OSINT',
    description: 'Investigación de fuentes abiertas',
    requiredTypes: ['url'],
    allowedMimeTypes: ['image/*'],
    maxFileSize: 10 * 1024 * 1024,  // 10MB para imágenes de referencia
    maxFiles: 3,
    allowedExtensions: ['.png', '.jpg', '.jpeg'],
    urlPatterns: [/^https?:\/\/.+/]
  }
};

// ============================================
// CONSTANTES DE CATEGORÍAS Y DIFICULTADES
// ============================================

// Constantes útiles
export const CTF_CATEGORIES: { value: CTFCategory; label: string; icon: string; description: string }[] = [
  { value: 'web', label: 'Web', icon: '🌐', description: 'Seguridad web' },
  { value: 'crypto', label: 'Criptografía', icon: '🔐', description: 'Cifrado y hashing' },
  { value: 'stego', label: 'Esteganografía', icon: '🖼️', description: 'Datos ocultos' },
  { value: 'forensics', label: 'Forense', icon: '🔍', description: 'Análisis digital' },
  { value: 'pwn', label: 'Pwn/Exploit', icon: '💥', description: 'Explotación' },
  { value: 'reverse', label: 'Reversing', icon: '⚙️', description: 'Ingeniería inversa' },
  { value: 'misc', label: 'Miscelánea', icon: '🎲', description: 'Retos variados' },
  { value: 'osint', label: 'OSINT', icon: '🕵️', description: 'Inteligencia abierta' }
];

export const CTF_DIFFICULTIES: { value: CTFDifficulty; label: string; color: string; points: number }[] = [
  { value: 'easy', label: 'Fácil', color: 'emerald', points: 100 },
  { value: 'medium', label: 'Medio', color: 'amber', points: 250 },
  { value: 'hard', label: 'Difícil', color: 'orange', points: 500 },
  { value: 'insane', label: 'Insano', color: 'red', points: 1000 }
];
