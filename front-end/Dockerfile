# ============================================
# Portfolio Frontend - Production Dockerfile
# ============================================
# Multi-stage build: Angular 16 + Nginx Alpine
# ============================================

# Stage 1: Build Angular application
FROM node:22-alpine AS builder

# Labels
LABEL stage="builder"

WORKDIR /app

# Copy package files first (better caching)
COPY portafolio/package*.json ./

# Install dependencies with clean install
RUN npm ci --legacy-peer-deps

# Copy source code
COPY portafolio/ .

# Build for production
RUN npm run build -- --configuration production

# Verify build output
RUN ls -la dist/portafolio/


# Stage 2: Production with Nginx
FROM nginx:1.25-alpine AS production

# Labels
LABEL maintainer="Elvis Portfolio <admin@elvisdeveloper.com>"
LABEL description="Portfolio Frontend - Angular + Nginx"
LABEL version="1.0.0"

# Install curl for healthcheck
RUN apk add --no-cache curl

# Remove default nginx config
RUN rm -rf /etc/nginx/conf.d/*

# Copy built application from builder
COPY --from=builder /app/dist/portafolio /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create nginx user and set permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
