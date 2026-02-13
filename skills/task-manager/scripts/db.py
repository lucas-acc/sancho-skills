#!/usr/bin/env python3
"""Task Manager SQLite Database Operations"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "db" / "tasks.db"
BACKUP_DIR = Path(__file__).parent.parent / "db" / "backup"

def get_connection():
    """Get SQLite database connection"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database schema"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'Backlog',
            priority TEXT DEFAULT 'Medium',
            project TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_task(title: str, priority: str = 'Medium', status: str = 'Backlog', project: str = '', description: str = ''):
    """Add a new task"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tasks (title, description, status, priority, project)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, description, status, priority, project))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_tasks(status_filter: str = None, show_done: bool = False):
    """Get tasks with proper sorting"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Status order for sorting
    status_order = {
        'In progress': 1,
        'Todo': 2,
        'Backlog': 3,
        'Done': 4,
        'Canceled': 5
    }
    priority_order = {
        'Urgent': 1,
        'High': 2,
        'Medium': 3,
        'Low': 4
    }
    
    if status_filter:
        cursor.execute('SELECT * FROM tasks WHERE project = ? ORDER BY status_order', (status_filter,))
    else:
        if show_done:
            query = '''
                SELECT * FROM tasks 
                ORDER BY 
                    CASE status 
                        WHEN 'In progress' THEN 1 
                        WHEN 'Todo' THEN 2 
                        WHEN 'Backlog' THEN 3 
                        WHEN 'Done' THEN 4 
                        WHEN 'Canceled' THEN 5 
                    END,
                    CASE priority 
                        WHEN 'Urgent' THEN 1 
                        WHEN 'High' THEN 2 
                        WHEN 'Medium' THEN 3 
                        WHEN 'Low' THEN 4 
                    END
            '''
            cursor.execute(query)
        else:
            cursor.execute('''
                SELECT * FROM tasks 
                WHERE status NOT IN ('Done', 'Canceled')
                ORDER BY 
                    CASE status 
                        WHEN 'In progress' THEN 1 
                        WHEN 'Todo' THEN 2 
                        WHEN 'Backlog' THEN 3 
                    END,
                    CASE priority 
                        WHEN 'Urgent' THEN 1 
                        WHEN 'High' THEN 2 
                        WHEN 'Medium' THEN 3 
                        WHEN 'Low' THEN 4 
                    END
            ''')
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_task(task_id: int, **kwargs):
    """Update a task"""
    valid_fields = ['title', 'description', 'status', 'priority', 'project']
    updates = []
    values = []
    
    for field, value in kwargs.items():
        if field in valid_fields:
            updates.append(f"{field} = ?")
            values.append(value)
    
    if not updates:
        return False
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(task_id)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f'''
        UPDATE tasks SET {', '.join(updates)} WHERE id = ?
    ''', values)
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

def delete_task(task_id: int):
    """Delete a task"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

def get_task_by_id(task_id: int):
    """Get a single task by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def backup_to_json():
    """Backup database to JSON"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks')
    rows = cursor.fetchall()
    conn.close()
    
    tasks = [dict(row) for row in rows]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = BACKUP_DIR / f"tasks_{timestamp}.json"
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
    
    return str(backup_path)

def get_stats():
    """Get task statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    for status in ['Backlog', 'Todo', 'In progress', 'Done', 'Canceled']:
        cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = ?', (status,))
        stats[status] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM tasks')
    stats['total'] = cursor.fetchone()[0]
    
    conn.close()
    return stats

# Initialize on import
if __name__ == '__main__':
    init_db()
    print("Database initialized at:", DB_PATH)
