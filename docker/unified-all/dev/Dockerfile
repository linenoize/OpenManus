# Development Dockerfile for OpenManus
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get -y install --no-install-recommends \
    curl \
    tree \
    nginx \
    gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install development tools
RUN pip install --no-cache-dir \
    watchdog \
    pytest \
    black \
    flake8

# Copy package.json and install dependencies
COPY package.json .
RUN npm install

# Copy nginx config
COPY docker/unified-all/nginx.conf /etc/nginx/nginx.conf

# Copy startup script
COPY docker/unified-all/dev/start.sh ./start.sh
RUN chmod +x ./start.sh

# Create error pages directory
RUN mkdir -p /app/errors
COPY docker/unified-all/errors/* /app/errors/

# Expose ports for development
EXPOSE 80 

# Start all services with hot reloading
CMD ["/app/start.sh"]