#!/bin/bash

echo "🔄 Stopping current services..."
docker compose down --remove-orphans

echo "🔥 Starting AI Stack in DEV mode (Hot Reload)..."
# docker compose up uses docker-compose.yml AND docker-compose.override.yml by default
docker compose up -d

echo ""
echo "✨ ------------------------------------------ ✨"
echo "👨‍💻  Mode DEV activé ! "
echo "    - Hot Reload: ON (python-runner)"
echo "    - Volumes: Synced"
echo "    - Logs: 'docker compose logs -f'"
echo "✨ ------------------------------------------ ✨"
