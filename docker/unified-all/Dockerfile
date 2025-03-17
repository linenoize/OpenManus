# Multi-stage build for OpenManus
# Stage 1: Build the Next.js frontend
FROM node:20-slim AS frontend-builder

WORKDIR /app

# Copy package.json and install dependencies
COPY package.json ./
RUN npm install

# Copy the rest of the frontend code
COPY next.config.js ./
COPY public ./public
COPY styles ./styles
COPY pages ./pages
COPY components ./components

# Build the Next.js application
RUN npm run build

# Stage 2: Python base image for final container
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get -y install --no-install-recommends \
    tree \
    nginx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the built Next.js app from the frontend builder
COPY --from=frontend-builder /app/.next ./.next
COPY --from=frontend-builder /app/public ./public
COPY --from=frontend-builder /app/node_modules ./node_modules
COPY --from=frontend-builder /app/package.json ./package.json

# Copy the Python backend code and nginx config
COPY src ./src
COPY docker/unified-all/start.sh ./start.sh
COPY docker/unified-all/nginx.conf /etc/nginx/nginx.conf

# Create error pages directory
RUN mkdir -p /app/errors
COPY docker/unified-all/errors/* /app/errors/

# Prepare startup script
RUN chmod +x ./start.sh

# Expose only port 80 for the nginx proxy
EXPOSE 80

# Start all services
CMD ["/app/start.sh"]