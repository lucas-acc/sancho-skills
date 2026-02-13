#!/usr/bin/env python3
"""Daily Task Reminder - Sends reminder message to OpenClaw"""

import sys
import os
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import get_tasks, get_stats

def format_reminder_message():
    """Format the daily reminder message"""
    tasks = get_tasks(show_done=False)
    stats = get_stats()
    
    if not tasks:
        message = "📋 **Daily Task Reminder**\n\n"
        message += "📭 No active tasks!\n"
        message += f"\n📊 Stats: {stats['total']} total tasks ({stats['Done']} done, {stats['Canceled']} canceled)"
        return message
    
    # Group tasks by status
    in_progress = [t for t in tasks if t['status'] == 'In progress']
    todo = [t for t in tasks if t['status'] == 'Todo']
    backlog = [t for t in tasks if t['status'] == 'Backlog']
    
    message = "📋 **Daily Task Reminder**\n\n"
    
    # Statistics
    message += f"📊 **Statistics**: {stats['total']} total | 🔄 {stats['In progress']} | 📋 {stats['Todo']} | 📦 {stats['Backlog']} | ✅ {stats['Done']} | ❌ {stats['Canceled']}\n"
    message += f"🕐 Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    message += "\n" + "─" * 50 + "\n\n"
    
    # In Progress
    if in_progress:
        message += "🔄 **In Progress** (" + str(len(in_progress)) + ")\n"
        for task in in_progress:
            emoji = "🔴" if task['priority'] == 'Urgent' else "🟠" if task['priority'] == 'High' else "🟡"
            proj = f"[{task['project']}] " if task['project'] else ""
            message += f"  {emoji} `{task['id']:3d}` {proj}{task['title']}\n"
        message += "\n"
    
    # Todo
    if todo:
        message += "📋 **Todo** (" + str(len(todo)) + ")\n"
        for task in todo:
            emoji = "🔴" if task['priority'] == 'Urgent' else "🟠" if task['priority'] == 'High' else "🟡"
            proj = f"[{task['project']}] " if task['project'] else ""
            message += f"  {emoji} `{task['id']:3d}` {proj}{task['title']}\n"
        message += "\n"
    
    # Backlog
    if backlog:
        urgent_high = [t for t in backlog if t['priority'] in ('Urgent', 'High')]
        medium_low = [t for t in backlog if t['priority'] in ('Medium', 'Low')]
        
        if urgent_high:
            message += "📦 **Backlog - Urgent/High** (" + str(len(urgent_high)) + ")\n"
            for task in urgent_high:
                emoji = "🔴" if task['priority'] == 'Urgent' else "🟠"
                proj = f"[{task['project']}] " if task['project'] else ""
                message += f"  {emoji} `{task['id']:3d}` {proj}{task['title']}\n"
            message += "\n"
        
        if medium_low:
            count = len(medium_low)
            message += f"📦 **Backlog - Medium/Low** ({count} tasks)"
            if count <= 5:
                message += "\n"
                for task in medium_low:
                    emoji = "🟡" if task['priority'] == 'Medium' else "🟢"
                    proj = f"[{task['project']}] " if task['project'] else ""
                    message += f"  {emoji} `{task['id']:3d}` {proj}{task['title']}\n"
            else:
                message += " (use `task list` to see all)\n"
    
    message += "\n" + "─" * 50 + "\n"
    message += "💡 Use `task list` to see all active tasks\n"
    message += "💡 Use `task done <id>` to complete a task\n"
    
    return message

def main():
    """Main entry point"""
    message = format_reminder_message()
    print(message)
    
    # This script is designed to be called by cron and output the message
    # OpenClaw cron system will handle sending this to the main session

if __name__ == '__main__':
    main()
