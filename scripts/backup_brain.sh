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
  
  # Auto-commit to Git
  echo "📦 Pushing to GitHub..."
  git add "$FILENAME"
  git commit -m "backup: auto-save brain state $(date +%Y-%m-%d)"
  git push
  
  if [ $? -eq 0 ]; then
     echo "🚀 Pushed to remote repository!"
  else
     echo "⚠️  Git push failed (is remote configured?)"
  fi
else
  echo "❌ Backup failed!"
  exit 1
fi
