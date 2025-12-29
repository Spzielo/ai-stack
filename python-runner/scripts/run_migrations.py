#!/usr/bin/env python3
"""
Database Migration Runner
Executes SQL migration files in order and tracks which have been applied.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db import get_db_connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_migrations_table(conn):
    """Create the migrations tracking table if it doesn't exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS migrations_applied (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL UNIQUE,
                applied_at TIMESTAMP NOT NULL DEFAULT NOW(),
                checksum VARCHAR(64)
            )
        """)
        conn.commit()
        logger.info("✓ Migrations tracking table ready")


def get_applied_migrations(conn):
    """Get set of already-applied migration filenames."""
    with conn.cursor() as cur:
        cur.execute("SELECT filename FROM migrations_applied")
        return {row[0] for row in cur.fetchall()}


def get_migration_files():
    """Get all .sql files from migrations directory, sorted by name."""
    migrations_dir = Path(__file__).parent.parent / "migrations"
    
    if not migrations_dir.exists():
        logger.error(f"❌ Migrations directory not found: {migrations_dir}")
        return []
    
    sql_files = sorted(migrations_dir.glob("*.sql"))
    logger.info(f"Found {len(sql_files)} migration files")
    
    return sql_files


def execute_migration(conn, filepath):
    """Execute a single migration file."""
    filename = filepath.name
    
    logger.info(f"▶ Executing migration: {filename}")
    
    try:
        # Read migration file
        with open(filepath, 'r') as f:
            sql_content = f.read()
        
        # Execute in a transaction
        with conn.cursor() as cur:
            cur.execute(sql_content)
            
            # Record successful migration
            cur.execute(
                "INSERT INTO migrations_applied (filename) VALUES (%s)",
                (filename,)
            )
        
        conn.commit()
        logger.info(f"✓ Successfully applied: {filename}")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Failed to apply {filename}: {e}")
        raise


def run_migrations():
    """Main migration runner."""
    logger.info("=" * 60)
    logger.info("DATABASE MIGRATION RUNNER")
    logger.info("=" * 60)
    
    try:
        # Connect to database
        logger.info("Connecting to database...")
        conn = get_db_connection()
        logger.info("✓ Database connection established")
        
        # Ensure migrations tracking table exists
        create_migrations_table(conn)
        
        # Get already-applied migrations
        applied = get_applied_migrations(conn)
        logger.info(f"Already applied: {len(applied)} migrations")
        
        # Get migration files
        migration_files = get_migration_files()
        
        if not migration_files:
            logger.warning("⚠ No migration files found")
            return
        
        # Execute pending migrations
        pending_count = 0
        for filepath in migration_files:
            filename = filepath.name
            
            if filename in applied:
                logger.info(f"⊘ Skipping (already applied): {filename}")
                continue
            
            execute_migration(conn, filepath)
            pending_count += 1
        
        # Summary
        logger.info("=" * 60)
        if pending_count == 0:
            logger.info("✓ All migrations already applied - database is up to date")
        else:
            logger.info(f"✓ Successfully applied {pending_count} new migration(s)")
        logger.info("=" * 60)
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_migrations()
