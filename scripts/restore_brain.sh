#!/bin/bash

# Configuration
CONTAINER_NAME="postgres"
DB_NAME="brain"
DB_USER="ai"

if [ -z "$1" ]; then
  echo "Usage: ./scripts/restore_brain.sh <backup_file.sql>"
  exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "❌ File not found: $BACKUP_FILE"
  exit 1
fi

echo "⚠️  WARNING: This will OVERWRITE the '$DB_NAME' database."
echo "Press CTRL+C to cancel or ENTER to continue..."
read

echo "🧠 Restoring '$DB_NAME' from $BACKUP_FILE..."

# Drop and recreate database to ensure clean state
echo "💣 Resetting database..."
docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;"

# Restore
echo "📥 Importing data..."
cat "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME"

if [ $? -eq 0 ]; then
  echo "✅ Restore successful!"
else
  echo "❌ Restore failed!"
  exit 1
fi
