# Portfolio Frontend

Frontend del portafolio personal construido con Angular 16 y Tailwind CSS.

## 🚀 Características

- ✅ Sistema de autenticación completo con JWT
- ✅ Visualización de proyectos del portafolio
- ✅ Módulo de CTF (Capture The Flag)
- ✅ Writeups de soluciones CTF
- ✅ Formulario de contacto
- ✅ Panel de administración (para gestión de contenido)
- ✅ Diseño responsive y moderno
- ✅ Guards y interceptors configurados

## 📋 Requisitos

- Node.js 18+ y npm
- Angular CLI 16

## 🔧 Instalación

### 1. Instalar dependencias

```bash
npm install
```

### 2. Configurar variables de entorno

Edita `src/environments/environment.ts`:

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1' // URL de tu backend
};
```

Para producción, edita `src/environments/environment.prod.ts`.

### 3. Ejecutar servidor de desarrollo

```bash
npm start
# o
ng serve
```

La aplicación estará disponible en: `http://localhost:4200`

## 🗂️ Estructura del Proyecto

```
src/app/
├── core/                           # Módulo principal
│   ├── guards/                     # Guards de rutas
│   │   ├── auth.guard.ts           # Protección autenticación
│   │   └── admin.guard.ts          # Protección admin
│   │
│   ├── interceptors/               # Interceptors HTTP
│   │   ├── auth.interceptor.ts     # Agrega JWT a requests
│   │   └── error.interceptor.ts    # Manejo global de errores
│   │
│   ├── services/                   # Servicios globales
│   │   ├── api.service.ts          # Servicio HTTP base
│   │   ├── auth.service.ts         # Autenticación
│   │   ├── cache.service.ts        # Caché de respuestas
│   │   ├── notification.service.ts # Notificaciones toast
│   │   └── error-handler.service.ts # Manejo de errores
│   │
│   └── layout/                     # Componentes de layout
│       └── main-layout.component   # Layout principal
│
├── features/                       # Módulos de funcionalidades
│   ├── auth/                       # Autenticación
│   │   ├── pages/
│   │   │   ├── login/
│   │   │   └── register/
│   │   └── auth.routes.ts
│   │
│   ├── home/                       # Página de inicio
│   │   ├── sections/               # Secciones de la home
│   │   └── home.component.ts
│   │
│   ├── projects/                   # Proyectos
│   │   ├── pages/
│   │   │   ├── project-list/
│   │   │   ├── project-detail/
│   │   │   └── project-form/       # Formulario admin
│   │   ├── services/
│   │   │   └── projects.service.ts
│   │   └── projects.routes.ts
│   │
│   ├── ctf/                        # CTF Challenges
│   │   ├── pages/
│   │   │   ├── ctf-list/
│   │   │   ├── ctf-detail/
│   │   │   └── ctf-upload/         # Upload admin
│   │   ├── services/
│   │   │   └── ctf.service.ts
│   │   └── ctf.routes.ts
│   │
│   └── writeups/                   # Writeups CTF
│       ├── pages/
│       │   ├── writeup-list/
│       │   ├── writeup-detail/
│       │   └── writeup-form/       # Formulario admin
│       ├── services/
│       │   └── writeups.service.ts
│       └── writeups.routes.ts
│
├── shared/                         # Componentes reutilizables
│   └── components/
│       ├── pagination/
│       ├── loading-spinner/
│       └── error-message/
│
└── app.routes.ts                   # Configuración de rutas
```

## 🎨 Tecnologías Utilizadas

- **Angular 16** - Framework principal
- **Tailwind CSS** - Estilos y diseño
- **TypeScript** - Lenguaje de programación
- **RxJS** - Programación reactiva
- **Standalone Components** - Arquitectura moderna de Angular

## 🔐 Autenticación

La autenticación se maneja mediante JWT tokens:

1. El usuario inicia sesión en `/auth/login`
2. Se recibe un access_token y refresh_token
3. El `authInterceptor` agrega automáticamente el token a todas las requests
4. El `errorInterceptor` maneja errores 401 y redirige al login si es necesario

### Rutas Protegidas

```typescript
// Requiere autenticación
{
  path: 'admin',
  canActivate: [AuthGuard]
}

// Requiere ser administrador
{
  path: 'admin/new',
  canActivate: [AuthGuard, AdminGuard]
}
```

## 📡 Servicios Principales

### ApiService
Servicio base para todas las llamadas HTTP:
```typescript
this.api.get<Project[]>('/projects')
this.api.post<Project>('/projects', data)
```

### AuthService
Gestión de autenticación:
```typescript
authService.login(credentials)
authService.logout()
authService.isAuthenticated  // boolean
authService.isAdmin          // boolean
```

### CacheService
Caché de respuestas HTTP con TTL:
```typescript
cacheService.get('projects', () => this.api.get('/projects'), 60000)
```

## 🧪 Testing

```bash
# Tests unitarios
ng test

# Tests E2E
ng e2e

# Con cobertura
ng test --code-coverage
```

## 🏗️ Build

### Desarrollo
```bash
ng build
```

### Producción
```bash
ng build --configuration production
```

Los archivos compilados estarán en `dist/portafolio/`.

## 🌐 Despliegue

### Netlify / Vercel
1. Build: `ng build --configuration production`
2. Publish directory: `dist/portafolio`
3. Configurar variable de entorno `API_URL`

### Docker
```bash
#Build
docker build -t portfolio-frontend .

# Run
docker run -p 80:80 portfolio-frontend
```

## 📝 Scripts Disponibles

```bash
npm start          # Servidor de desarrollo
npm run build      # Build de producción
npm test           # Ejecutar tests
npm run lint       # Linter
npm run format     # Formatear código
```

## 🎨 Guía de Estilos

### Componentes
- Usar standalone components
- Imports explícitos de CommonModule y módulos necesarios
- Preferir OnPush change detection cuando sea posible

### Servicios
- Inyectar mediante constructor o `inject()`
- Usar `providedIn: 'root'` para servicios singleton
- Manejar errores con `catchError`

### Rutas
- Usar lazy loading con `loadChildren` o `loadComponent`
- Proteger rutas sensibles con guards
- Definir rutas en archivos `.routes.ts` separados

## 🐛 Debugging

### Errores Comunes

**Error: Cannot find module '@core/...'**
- Verifica que los path aliases estén configurados en `tsconfig.json`

**Error de CORS**
- Verifica que el backend tenga configurado el origen correcto en CORS

**Token expirado**
- El interceptor debería manejar esto automáticamente y redirigir al login

## 👥 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -m 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

## 📄 Licencia

[Especificar licencia]

## 📧 Contacto

[Tu información de contacto]
