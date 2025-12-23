"""
Database Utility.
core/db.py
"""
import os
import psycopg2

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ['BRAIN_DB_HOST'],
        database=os.environ['BRAIN_DB_NAME'],
        user=os.environ['BRAIN_DB_USER'],
        password=os.environ['BRAIN_DB_PASSWORD'],
        port=os.environ['BRAIN_DB_PORT']
    )
    return conn
