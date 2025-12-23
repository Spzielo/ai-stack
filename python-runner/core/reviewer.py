"""
Reviewer Module
core/reviewer.py

Aggregates data for the Daily Briefing.
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any, List
import os

logger = logging.getLogger(__name__)

class Reviewer:
    def __init__(self):
        self.db_config = {
            "host": os.environ['BRAIN_DB_HOST'],
            "database": os.environ['BRAIN_DB_NAME'],
            "user": os.environ['BRAIN_DB_USER'],
            "password": os.environ['BRAIN_DB_PASSWORD'],
            "port": os.environ['BRAIN_DB_PORT']
        }

    def _get_connection(self):
        return psycopg2.connect(**self.db_config)

    def generate_briefing(self) -> Dict[str, Any]:
        """
        Fetches stats and pending items.
        """
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # 1. Pending Tasks (created recently or due soon)
            # For simplicity, we just list ALL 'todo' tasks for now.
            cur.execute("""
                SELECT title, priority, created_at 
                FROM tasks 
                WHERE status = 'todo' 
                ORDER BY priority DESC, created_at DESC
                LIMIT 5;
            """)
            pending_tasks = cur.fetchall()

            # 2. Recent Notes (last 24h)
            cur.execute("""
                SELECT title, created_at 
                FROM notes 
                WHERE created_at > NOW() - INTERVAL '24 hours'
                ORDER BY created_at DESC
                LIMIT 5;
            """)
            recent_notes = cur.fetchall()
            
            # 3. Counts
            cur.execute("SELECT COUNT(*) as count FROM tasks WHERE status = 'todo'")
            task_count = cur.fetchone()['count']

            cur.execute("SELECT COUNT(*) as count FROM notes WHERE created_at > NOW() - INTERVAL '24 hours'")
            note_count = cur.fetchone()['count']

            return {
                "tasks": pending_tasks,
                "notes": recent_notes,
                "stats": {
                    "pending_tasks": task_count,
                    "new_notes": note_count
                }
            }

        finally:
            cur.close()
            conn.close()

reviewer = Reviewer()
