#!/bin/bash
# Script to create uploads directory structure for ATTREQ

# Create base directory
echo "Creating uploads directory structure..."

# Base directory (relative to Backend folder)
BASE_DIR="./uploads"

# Create subdirectories
mkdir -p "$BASE_DIR/originals"
mkdir -p "$BASE_DIR/processed"
mkdir -p "$BASE_DIR/thumbnails"

# Set permissions (adjust as needed for your user)
chmod -R 755 "$BASE_DIR"

echo "Directory structure created successfully!"
echo ""
echo "Structure:"
echo "$BASE_DIR/"
echo "  ├── originals/    (original uploaded images)"
echo "  ├── processed/    (background-removed images)"
echo "  └── thumbnails/   (300px thumbnails)"
echo ""
echo "Note: This directory is mounted in docker-compose.yml as ./uploads:/app/uploads"

