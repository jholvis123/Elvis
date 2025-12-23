# Política de Seguridad

## 🔒 Versiones Soportadas

| Versión | Soportada          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## 🚨 Reportar una Vulnerabilidad

Si descubres una vulnerabilidad de seguridad en este proyecto, por favor sigue estos pasos:

### NO hagas:
- ❌ Abrir un issue público en GitHub
- ❌ Divulgar la vulnerabilidad públicamente antes de que sea corregida

### SÍ haz:
1. **Envía un correo al mantenedor** a: `yhon.elvis.49@gmail.com` con el asunto: `[SECURITY] Reporte de Vulnerabilidad`
2. **Incluye la siguiente información:**
   - Tipo de vulnerabilidad
   - Rutas completas de los archivos afectados
   - Ubicación del código fuente afectado (tag/branch/commit o URL directa)
   - Instrucciones paso a paso para reproducir el problema
   - Código de prueba de concepto o exploit (si es posible)
   - Impacto del problema

### Qué esperar:
- ✅ Confirmación de recepción de tu reporte en **48 horas**
- ✅ Una evaluación inicial en **1 semana**
- ✅ Actualizaciones regulares sobre el progreso
- ✅ Crédito en el aviso de seguridad (si lo deseas)

## 🛡️ Medidas de Seguridad

Este proyecto implementa las siguientes medidas de seguridad:

### Backend (FastAPI/Python)
- Autenticación con tokens JWT y claves secretas seguras
- Hash de contraseñas con bcrypt
- Validación de entrada con Pydantic
- Prevención de inyección SQL mediante SQLAlchemy ORM
- Límite de peticiones en endpoints sensibles
- Configuración de CORS
- Middleware de cabeceras de seguridad

### Frontend (Angular)
- Protección XSS mediante sanitización integrada de Angular
- Tokens CSRF en formularios
- Cookies HTTP-only seguras para tokens
- Cabeceras de Política de Seguridad de Contenido

### Infraestructura
- Contenedores Docker con usuarios no-root (recomendado)
- Actualizaciones regulares de dependencias vía Dependabot
- Escaneo de seguridad automatizado en CI/CD
- Detección de secretos en commits

## 🔐 Buenas Prácticas de Seguridad para Colaboradores

1. **Nunca hagas commit de secretos** - Usa variables de entorno
2. **Mantén las dependencias actualizadas** - Revisa los PRs de Dependabot prontamente
3. **Sigue las guías de código seguro**
4. **Prueba las implicaciones de seguridad** de tus cambios

## 📋 Lista de Verificación de Seguridad para PRs

- [ ] Sin credenciales o secretos hardcodeados
- [ ] Validación de entrada en todos los datos de usuario
- [ ] Consultas parametrizadas (sin SQL crudo)
- [ ] Verificaciones de autenticación/autorización apropiadas
- [ ] Datos sensibles no registrados en logs
- [ ] Dependencias solo de fuentes confiables
