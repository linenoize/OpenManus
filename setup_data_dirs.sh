#!/bin/bash

# Script to set up data directories for OpenManus with proper permissions

# Create base data directories
echo "Creating data directories..."
mkdir -p data/files/local
mkdir -p data/files/git

# Set permissions (make writable for all users)
echo "Setting permissions..."
chmod -R 777 data

# Create a README explaining the directory structure
cat > data/README.md << EOF
# OpenManus Data Directory

This directory contains data files used by OpenManus:

- \`files/\`: Storage location for user files
  - \`local/\`: Local storage backend
  - \`git/\`: Git-backed storage backend
EOF

echo "Done! Data directories created with proper permissions."
echo "You can now run the Docker containers using:"
echo "  docker-compose -f docker-compose.unified.yml up"
echo "or for development:"
echo "  docker-compose -f docker-compose.dev.yml up"