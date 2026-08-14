# Use Node.js official image as base
FROM node:25-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files for dependency installation
COPY contentflow-web/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY contentflow-web/. .

# Create dynamic .env file
RUN echo "VITE_API_BASE_URL=API_URL" > .env && \
    echo "VITE_OTHER_CONFIG=OTHER_CONFIG" >> .env

# Build the application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine AS production

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Create nginx configuration for serving static files only
RUN echo 'server { \
    listen 8080; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Create entrypoint script to write browser runtime configuration
RUN printf '#!/bin/sh\ncat > /usr/share/nginx/html/env-config.js <<EOF\nwindow.__CONTENTFLOW_CONFIG__ = {\n  apiBaseUrl: "${VITE_API_BASE_URL:-http://localhost:8090/api/}"\n};\nEOF\nexec nginx -g "daemon off;"\n' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Expose port 8080
EXPOSE 8080

# Start nginx with custom entrypoint
ENTRYPOINT ["/entrypoint.sh"]