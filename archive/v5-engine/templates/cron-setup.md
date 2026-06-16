# Cron Setup for Fable Orchestrator

This template helps you set up automatic execution so Fable tasks run while you sleep.

## Quick Setup

```bash
# 1. Run the quickstart wizard (recommended)
python3 ~/.hermes/skills/fable-orchestrator/quickstart.py

# 2. Or manually edit your crontab
crontab -e

# 3. Add this line (runs every 15 minutes)
*/15 * * * * python3 /home/case/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --tick --output-dir /home/case/fable-outputs --state-db /home/case/.hermes/fable_state.db

# 4. Save and exit
```

## What This Does

Every 15 minutes, your computer checks if there are any running Fable tasks and executes the next tick. This means:

- You can start a task and close your laptop
- The task continues running in the background
- When you come back, the task is done
- If your computer restarts, the task resumes automatically

## Adjusting the Frequency

| Frequency | Cron line | Use case |
|-----------|-----------|----------|
| Every 15 min | `*/15 * * * *` | Default. Good for most tasks. |
| Every 10 min | `*/10 * * * *` | Faster tasks. More API calls. |
| Every 5 min | `*/5 * * * *` | Urgent tasks. Higher API usage. |
| Every hour | `0 * * * *` | Slow tasks. Lower API usage. |

## Checking If Cron Is Running

```bash
# List your cron jobs
crontab -l

# Check if the cron daemon is running
systemctl status cron

# Or on some systems
service cron status
```

## Removing the Cron Job

```bash
# Edit crontab
crontab -e

# Delete the line with fable_daemon.py
# Save and exit
```

## Troubleshooting

### "Cron job not running"

Check if cron is installed and running:
```bash
which cron
systemctl status cron
```

### "Tasks not progressing"

Check the status:
```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --status --state-db ~/.hermes/fable_state.db
```

If tasks are stuck, they might be waiting for dependencies. Check the work log:
```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --tail TASK_ID --state-db ~/.hermes/fable_state.db
```

### "Too many API calls"

Increase the interval. Change `*/15` to `*/30` or `0 *` in the cron line.
