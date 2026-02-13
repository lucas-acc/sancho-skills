# Task Manager Skill

Personal task management system integrated with OpenClaw. Track, prioritize, and manage your personal tasks with SQLite storage and daily reminders.

## Features

- **SQLite Storage**: Fast, reliable local database with JSON backup
- **Priority System**: Urgent → High → Medium → Low
- **Status Workflow**: Backlog → Todo → In progress → Done/Canceled
- **Project Tagging**: Organize tasks by project
- **Daily Reminders**: Automatic reminder in your main session
- **CLI Interface**: Simple command-line interface

## Commands

### Add a Task
```bash
task add "Task title"                           # Backlog, Medium
task add "Urgent task" --priority urgent        # Urgent priority
task add "Project task" --project "MyProject"    # With project tag
task add "Todo item" --status todo              # Start in Todo
```

### List Tasks
```bash
task list                                        # Active tasks only (default)
task list --all                                  # Show all including Done/Canceled
task list --project "MyProject"                   # Filter by project
task show-done                                   # Show Done/Canceled only
```

### Update Tasks
```bash
task done 1                                      # Mark as Done
task cancel 1                                    # Cancel task
task todo 1                                      # Move to Todo
task update 1 --priority high                    # Update priority
task update 1 --status "In progress"             # Update status
task update 1 --project "NewProject"             # Update project
```

### Manage Tasks
```bash
task delete 1                                    # Delete task (with confirmation)
task stats                                       # Show statistics
task backup                                     # Backup to JSON
```

## Priority & Status

### Priority Order
```
🔴 Urgent  →  🟠 High  →  🟡 Medium  →  🟢 Low
```

### Status Order (for sorting)
```
🔄 In progress  →  📋 Todo  →  📦 Backlog  →  ✅ Done  →  ❌ Canceled
```

## Database Location

- **SQLite**: `~/.openclaw/workspace/skills/task-manager/db/tasks.db`
- **JSON Backup**: `~/.openclaw/workspace/skills/task-manager/db/backup/`

## Daily Reminder

Daily reminders are sent to your main OpenClaw session via cron. The reminder includes:
- All active tasks grouped by status
- Statistics summary
- Suggestions for next actions

### Configure Reminder Time

Use OpenClaw's cron command to configure:

```bash
openclaw cron add --name "daily-tasks" \
  --schedule "0 9 * * *" \
  --session main \
  --payload "Daily Task Reminder"
```

## Integration with OpenClaw

This skill integrates with OpenClaw via:

1. **CLI Commands**: Run `task` commands directly
2. **Cron Integration**: Daily automated reminders
3. **Message Delivery**: Reminders sent to your main session

## Examples

### Daily Workflow
```bash
# Morning: Check tasks
task list

# Work: Start something
task todo 3 && task update 3 --status "In progress"

# Done: Complete it
task done 3

# Evening: Review
task stats
```

### Project Management
```bash
# Add project tasks
task add "Design DB schema" --project "TaskManager"
task add "Write CLI" --project "TaskManager" --priority high
task add "Write tests" --project "TaskManager"

# Filter by project
task list --project "TaskManager"

# Complete project
task done 1 && task done 2 && task done 3
```

## Troubleshooting

### Command not found
Ensure `scripts/` is in your PATH or run with full path:
```bash
python /Users/lucas-acc/.openclaw/workspace/skills/task-manager/scripts/task.py list
```

### Database issues
Run backup and check:
```bash
task backup
sqlite3 ~/.openclaw/workspace/skills/task-manager/db/tasks.db "SELECT * FROM tasks;"
```
