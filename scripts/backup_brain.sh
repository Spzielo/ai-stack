#!/bin/bash

# Configuration
CONTAINER_NAME="postgres"
DB_NAME="brain"
DB_USER="ai"
BACKUP_DIR="./backups"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
FILENAME="${BACKUP_DIR}/brain_${DATE}.sql"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

echo "🧠 Backing up 'brain' database..."

# Dump database
docker exec -t "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" > "$FILENAME"

if [ $? -eq 0 ]; then
  echo "✅ Backup successful: $FILENAME"
else
  echo "❌ Backup failed!"
  exit 1
fi
