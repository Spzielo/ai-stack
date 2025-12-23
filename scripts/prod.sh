#!/bin/bash

echo "🔄 Stopping current services..."
docker compose down --remove-orphans

echo "🚀 Starting AI Stack in PROD mode (Stable)..."
# Explicitly ignore override.yml by specifying base and prod files
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo ""
echo "✨ ------------------------------------------ ✨"
echo "🛡️   Mode PROD activé !"
echo "    - Hot Reload: OFF"
echo "    - Restart: Always"
echo "    - Security: Optimised"
echo "✨ ------------------------------------------ ✨"
