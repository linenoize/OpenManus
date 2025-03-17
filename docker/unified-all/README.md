# OpenManus Unified Container

This directory contains the configuration for the unified Docker container that runs all OpenManus services in a single container.

## Features

- Single container deployment for the entire OpenManus stack
- Multi-stage build to optimize container size
- Nginx reverse proxy for single port access to all services
- Health checks and graceful service startup/shutdown
- Error handling and custom error pages
- Automatic environment file creation if not mounted

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

To start the unified container:

```bash
docker-compose -f docker-compose.unified.yml up
```

This will build and start the container, exposing port 80 for all services.

## Development Mode

For development, you can mount your local source directories into the container:

```yaml
volumes:
  - ./src:/app/src
  - ./data:/app/data
  - ./.env:/app/.env
```

This allows you to make changes to the source code without rebuilding the container.

## Environment Variables

You can provide environment variables through a mounted `.env` file. If no file is provided, an empty one will be created automatically.

## Implementation Details

- Multi-stage build with Node.js to build the Next.js application
- Python base image for the final container
- Nginx reverse proxy to route requests to the appropriate service
- Startup script that manages service startup, health checks, and graceful shutdown