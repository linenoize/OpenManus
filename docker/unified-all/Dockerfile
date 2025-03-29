# Multi-stage build for OpenManus
# Stage 1: Build Next.js frontend
FROM node:20-slim AS frontend-builder

WORKDIR /app

# Copy Next.js configuration and dependencies
COPY package.json ./
COPY next.config.js ./
RUN npm install

# Copy frontend source code
COPY pages ./pages
COPY public ./public
COPY styles ./styles
COPY components ./components

# Build Next.js for production
RUN npm run build

# Stage 2: Python dependencies
FROM python:3.9-slim AS python-deps

WORKDIR /app

# Install Python dependencies for testing
RUN pip install --no-cache-dir flask requests python-dotenv nltk numpy pandas matplotlib \
    sentence-transformers faiss-cpu chromadb pymilvus Pillow PyPDF2 && \
    # Pre-download NLTK data to avoid permission issues
    python -c "import nltk; nltk.download('punkt', download_dir='/usr/local/share/nltk_data')"

# Stage 3: Final runtime image
FROM python:3.9-slim

WORKDIR /app

# Set appropriate user for running the container
USER root

# Install necessary production dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    nginx \
    nodejs \
    npm \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create cache directories with proper permissions after nginx is installed
RUN mkdir -p /.cache /.config/matplotlib /var/lib/nginx/body && \
    chmod -R 777 /.cache /.config && \
    chmod -R 777 /var/lib/nginx

# Copy Python dependencies from the python-deps stage
COPY --from=python-deps /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

# Copy the built Next.js app from the frontend builder
COPY --from=frontend-builder /app/.next ./.next
COPY --from=frontend-builder /app/public ./public
COPY --from=frontend-builder /app/node_modules ./node_modules
COPY --from=frontend-builder /app/package.json ./package.json

# Copy only necessary files
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

# Create data directories with proper permissions
RUN mkdir -p /app/data/files/local /app/data/files/git \
    /app/data/vectors/faiss /app/data/vectors/chroma /app/data/vectors/milvus

# Set default non-root user for security
RUN groupadd -r openmanus && useradd -r -g openmanus openmanus
RUN chown -R openmanus:openmanus /app /var/log/nginx /var/lib/nginx

# Ensure data directories have proper permissions
RUN chmod -R 755 /app/data

USER openmanus

# Start all services
CMD ["/app/start.sh"]