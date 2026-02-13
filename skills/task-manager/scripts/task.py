#!/usr/bin/env python3
"""Task Manager CLI - Main Entry Point"""

import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import (
    init_db, add_task, get_tasks, update_task, 
    delete_task, get_task_by_id, backup_to_json, get_stats
)

def print_header():
    """Print task table header"""
    print("─" * 90)
    print(f"{'ID':<4} {'Status':<12} {'Priority':<8} {'Project':<15} {'Title':<40} {'Created':<12}")
    print("─" * 90)

def format_status(status: str) -> str:
    """Color format for status"""
    colors = {
        'In progress': '🔄 In progress',
        'Todo': '📋 Todo',
        'Backlog': '📦 Backlog',
        'Done': '✅ Done',
        'Canceled': '❌ Canceled'
    }
    return colors.get(status, status)

def format_priority(priority: str) -> str:
    """Color format for priority"""
    colors = {
        'Urgent': '🔴 Urgent',
        'High': '🟠 High',
        'Medium': '🟡 Medium',
        'Low': '🟢 Low'
    }
    return colors.get(priority, priority)

def cmd_add(args):
    """Add a new task"""
    title = args.title
    priority = getattr(args, 'priority', 'Medium')
    status = getattr(args, 'status', 'Backlog')
    project = getattr(args, 'project', '')
    description = getattr(args, 'description', '')
    
    task_id = add_task(title, priority, status, project, description)
    print(f"✅ Added task #{task_id}: {title}")

def cmd_list(args):
    """List tasks"""
    show_done = getattr(args, 'all', False)
    project_filter = getattr(args, 'project', None)
    tg_mode = getattr(args, 'tg', False)
    
    tasks = get_tasks(status_filter=project_filter, show_done=show_done)
    
    if not tasks:
        if show_done:
            print("📭 No tasks found")
        else:
            print("📭 No active tasks (Backlog/Todo/In progress)")
            print("   Use 'task list --all' to show Done/Canceled tasks")
        return
    
    stats = get_stats()
    
    if tg_mode:
        # Telegram-friendly format
        print_telegram_format(tasks, stats, show_done)
    else:
        # Default table format
        print(f"\n📊 Tasks: {stats['total']} total | 🔄 {stats['In progress']} | 📋 {stats['Todo']} | 📦 {stats['Backlog']} | ✅ {stats['Done']} | ❌ {stats['Canceled']}\n")
        
        print_header()
        for task in tasks:
            status_display = format_status(task['status'])
            priority_display = format_priority(task['priority'])
            project = task['project'][:15] + '..' if len(task['project']) > 15 else task['project']
            title = task['title'][:40] + '..' if len(task['title']) > 40 else task['title']
            created = task['created_at'][:10]
            
            print(f"{task['id']:<4} {status_display:<16} {priority_display:<12} {project:<17} {title:<40} {created:<12}")
        print()


def print_telegram_format(tasks, stats, show_done):
    """Print tasks in Telegram-friendly format"""
    # Header with stats
    msg = "📋 Task List\n\n"
    msg += f"📊 {stats['total']} total | 🔄{stats['In progress']} 📋{stats['Todo']} 📦{stats['Backlog']} ✅{stats['Done']} ❌{stats['Canceled']}\n"
    msg += "\n" + "─" * 30 + "\n\n"
    
    # Group by status
    in_progress = [t for t in tasks if t['status'] == 'In progress']
    todo = [t for t in tasks if t['status'] == 'Todo']
    backlog = [t for t in tasks if t['status'] == 'Backlog']
    
    def format_task_line(t):
        emoji = "🔴" if t['priority'] == 'Urgent' else "🟠" if t['priority'] == 'High' else "🟡"
        proj = f"[{t['project']}] " if t['project'] else ""
        desc = f"\n   📝 {t['description']}" if t['description'] else ""
        return f"{emoji} `{t['id']}` {proj}{t['title']}{desc}\n"
    
    # In Progress
    if in_progress:
        msg += "🔄 In Progress\n"
        for t in in_progress:
            msg += format_task_line(t)
        msg += "\n"
    
    # Todo
    if todo:
        msg += "📋 Todo\n"
        for t in todo:
            msg += format_task_line(t)
        msg += "\n"
    
    # Backlog
    if backlog:
        msg += "📦 Backlog\n"
        for t in backlog:
            msg += format_task_line(t)
    
    # Footer
    msg += "\n" + "─" * 30 + "\n"
    msg += "💡 `task done <id>` 完成 | `task todo <id>` 待办"
    
    print(msg)

def cmd_done(args):
    """Mark task as done"""
    task_id = args.id
    task = get_task_by_id(task_id)
    if not task:
        print(f"❌ Task #{task_id} not found")
        return
    
    update_task(task_id, status='Done')
    print(f"✅ Task #{task_id} marked as Done: {task['title']}")

def cmd_cancel(args):
    """Cancel a task"""
    task_id = args.id
    task = get_task_by_id(task_id)
    if not task:
        print(f"❌ Task #{task_id} not found")
        return
    
    update_task(task_id, status='Canceled')
    print(f"❌ Task #{task_id} canceled: {task['title']}")

def cmd_todo(args):
    """Move task to Todo"""
    task_id = args.id
    task = get_task_by_id(task_id)
    if not task:
        print(f"❌ Task #{task_id} not found")
        return
    
    update_task(task_id, status='Todo')
    print(f"📋 Task #{task_id} moved to Todo: {task['title']}")

def cmd_update(args):
    """Update task fields"""
    task_id = args.id
    task = get_task_by_id(task_id)
    if not task:
        print(f"❌ Task #{task_id} not found")
        return
    
    updates = {}
    if hasattr(args, 'priority') and args.priority:
        updates['priority'] = args.priority
    if hasattr(args, 'status') and args.status:
        updates['status'] = args.status
    if hasattr(args, 'project') and args.project is not None:
        updates['project'] = args.project
    if hasattr(args, 'title') and args.title:
        updates['title'] = args.title
    if hasattr(args, 'description') and args.description is not None:
        updates['description'] = args.description
    
    if updates:
        update_task(task_id, **updates)
        print(f"✅ Task #{task_id} updated")
    else:
        print("ℹ️  No updates provided")

def cmd_delete(args):
    """Delete a task"""
    task_id = args.id
    task = get_task_by_id(task_id)
    if not task:
        print(f"❌ Task #{task_id} not found")
        return
    
    confirm = input(f"🗑️  Delete task #{task_id} '{task['title']}'? [y/N]: ")
    if confirm.lower() == 'y':
        delete_task(task_id)
        print(f"✅ Task #{task_id} deleted")
    else:
        print("❎ Delete cancelled")

def cmd_backup(args):
    """Backup database to JSON"""
    backup_path = backup_to_json()
    print(f"💾 Backup saved to: {backup_path}")

def cmd_stats(args):
    """Show task statistics"""
    stats = get_stats()
    print("\n📊 Task Statistics")
    print("─" * 30)
    print(f"  In progress: {stats['In progress']}")
    print(f"  Todo:       {stats['Todo']}")
    print(f"  Backlog:    {stats['Backlog']}")
    print(f"  Done:       {stats['Done']}")
    print(f"  Canceled:   {stats['Canceled']}")
    print(f"  ─────────────────")
    print(f"  Total:      {stats['total']}")
    print()

def cmd_show_done(args):
    """Show only Done and Canceled tasks"""
    tasks = get_tasks(show_done=True)
    done_tasks = [t for t in tasks if t['status'] in ('Done', 'Canceled')]
    
    if not done_tasks:
        print("📭 No Done/Canceled tasks")
        return
    
    print_header()
    for task in done_tasks:
        status_display = format_status(task['status'])
        priority_display = format_priority(task['priority'])
        project = task['project'][:15] + '..' if len(task['project']) > 15 else task['project']
        title = task['title'][:40] + '..' if len(task['title']) > 40 else task['title']
        created = task['created_at'][:10]
        
        print(f"{task['id']:<4} {status_display:<16} {priority_display:<12} {project:<17} {title:<40} {created:<12}")
    print()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='🗂️ Personal Task Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  task add "Learn Python"                           # Add to Backlog, Medium priority
  task add "Urgent fix" --priority urgent          # Add with Urgent priority
  task add "Project X" --project "MyProject"       # Add with project tag
  task list                                        # Show active tasks
  task list --all                                  # Show all tasks including Done
  task list --project "MyProject"                 # Filter by project
  task done 1                                      # Mark task #1 as Done
  task cancel 1                                    # Cancel task #1
  task todo 1                                      # Move to Todo
  task update 1 --priority high                    # Update priority
  task delete 1                                   # Delete task #1
  task show-done                                  # Show only Done/Canceled
  task stats                                      # Show statistics
  task backup                                     # Backup to JSON
        '''
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # add
    p_add = subparsers.add_parser('add', help='Add a new task')
    p_add.add_argument('title', help='Task title')
    p_add.add_argument('--priority', choices=['Urgent', 'High', 'Medium', 'Low'], default='Medium', help='Priority (default: Medium)')
    p_add.add_argument('--status', choices=['Backlog', 'Todo', 'In progress', 'Done', 'Canceled'], default='Backlog', help='Status (default: Backlog)')
    p_add.add_argument('--project', default='', help='Project name')
    p_add.add_argument('--description', default='', help='Task description')
    
    # list
    p_list = subparsers.add_parser('list', help='List tasks')
    p_list.add_argument('--all', action='store_true', help='Show all tasks including Done/Canceled')
    p_list.add_argument('--project', help='Filter by project')
    p_list.add_argument('--tg', action='store_true', help='Telegram-friendly format')
    
    # done
    p_done = subparsers.add_parser('done', help='Mark task as Done')
    p_done.add_argument('id', type=int, help='Task ID')
    
    # cancel
    p_cancel = subparsers.add_parser('cancel', help='Cancel a task')
    p_cancel.add_argument('id', type=int, help='Task ID')
    
    # todo
    p_todo = subparsers.add_parser('todo', help='Move task to Todo')
    p_todo.add_argument('id', type=int, help='Task ID')
    
    # update
    p_update = subparsers.add_parser('update', help='Update task')
    p_update.add_argument('id', type=int, help='Task ID')
    p_update.add_argument('--priority', choices=['Urgent', 'High', 'Medium', 'Low'], help='New priority')
    p_update.add_argument('--status', choices=['Backlog', 'Todo', 'In progress', 'Done', 'Canceled'], help='New status')
    p_update.add_argument('--project', help='New project name')
    p_update.add_argument('--title', help='New title')
    p_update.add_argument('--description', help='New description')
    
    # delete
    p_delete = subparsers.add_parser('delete', help='Delete a task')
    p_delete.add_argument('id', type=int, help='Task ID')
    
    # show-done
    subparsers.add_parser('show-done', help='Show Done/Canceled tasks only')
    
    # stats
    subparsers.add_parser('stats', help='Show task statistics')
    
    # backup
    subparsers.add_parser('backup', help='Backup database to JSON')
    
    args = parser.parse_args()
    
    # Initialize database
    init_db()
    
    # Route command
    commands = {
        'add': cmd_add,
        'list': cmd_list,
        'done': cmd_done,
        'cancel': cmd_cancel,
        'todo': cmd_todo,
        'update': cmd_update,
        'delete': cmd_delete,
        'show-done': cmd_show_done,
        'stats': cmd_stats,
        'backup': cmd_backup,
    }
    
    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
