# OpenManus Unified Container

This directory contains the configuration for the unified Docker container that runs all OpenManus services in a single container.

## Features

- Single container deployment for the entire OpenManus stack
- Multi-stage build to optimize container size
- Nginx reverse proxy for single port access to all services
- Health checks and graceful service startup/shutdown
- Error handling and custom error pages
- Automatic environment file creation if not mounted
- Development mode with hot-reloading
- Production mode with optimized image size and security enhancements

## Services

The unified container runs the following services:

- Next.js frontend (port 3000 internally)
- Flask API server (port 5000 internally)
- Tools server (port 5001 internally)
- Nginx reverse proxy (port 80 exposed)

## URL Structure

When accessing the unified container:

- `/` - Next.js frontend
- `/api/` - Flask API endpoints
- `/tools/` - Tools server endpoints
- `/health` - Container health check endpoint

## Usage

### Production Mode

To start the unified container in production mode:

```bash
docker-compose -f docker-compose.unified.yml up
```

This will build and start the container with optimized settings for production use.

### Development Mode

For development with hot-reloading of code changes:

```bash
docker-compose -f docker-compose.dev.yml up
```

This will start the container with:
- Next.js development server (with hot module replacement)
- Flask development server with auto-reload
- Tools server with watchdog for auto-restart on file changes

## Environment Variables

You can provide environment variables through a mounted `.env` file. If no file is provided, an empty one will be created automatically.

## Development Workflow

The development container mounts your local source directories:

```yaml
volumes:
  - ./src:/app/src        # Python backend code
  - ./data:/app/data      # Data directory
  - ./public:/app/public  # Next.js public assets
  - ./pages:/app/pages    # Next.js page components
  - ./components:/app/components  # React components
  - ./styles:/app/styles  # CSS/SCSS files
  - ./.env:/app/.env      # Environment variables
```

This allows you to make changes to the source code that will be automatically detected and reloaded without rebuilding the container.

## Implementation Details

### Production Container
- Three-stage build process for minimal image size:
  1. Build Next.js frontend with Node.js
  2. Install Python dependencies in a separate layer
  3. Final runtime image with only necessary components
- Non-root user for enhanced security
- Optimized dependency installation

### Development Container
- Single-stage build with all development tools
- Node.js and Python in the same container
- Watchdog for auto-reloading Python services
- Interactive terminal support