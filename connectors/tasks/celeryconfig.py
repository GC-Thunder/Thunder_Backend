from celery.schedules import crontab

# Broker settings.
broker_url = 'redis://localhost:6379/0'

# Modules to import when the Celery worker starts.
imports = ('connectors.tasks.cricket_tasks',)

# Backend for storing task results.
result_backend = 'redis://localhost:6379/0'

# Task result serialization
accept_content = ['json']  # Accepted content types
result_accept_content = ['json']  # Result serialization
task_serializer = 'json'  # Task serialization (can be json, pickle, etc.)

# Timezone settings
enable_utc = False
timezone = 'Asia/Kolkata'


# Task execution constraints
task_time_limit = 300  # Max run time in seconds (e.g., 5 minutes)

# Task annotations (you can set for specific tasks or use wildcard)
task_annotations = {
    '*': {'rate_limit': '20/s'},  # Default rate limit for all tasks
    'tasks.add': {'rate_limit': '10/s', 'time_limit': 60},  # Specific task override
}

# Beat Schedule: Run the match scheduler every day at 8:00 AM IST
beat_schedule = {
    'run-daily-match-scheduler': {
        'task': 'connectors.tasks.cricket_tasks.schedule_today_matches',
        'schedule': crontab(hour=8, minute=0),
    },
    'run-daily-table': {
        'task': 'connectors.tasks.cricket_tasks.schedule_today_table',
        'schedule': crontab(minute=30, hour=23),
    },
    'run-daily-mvp': {
        'task': 'connectors.tasks.cricket_tasks.schedule_today_mvp',
        'schedule': crontab(minute=30, hour=23),
    },
    'run-daily-scorecard': {
        'task': 'connectors.tasks.cricket_tasks.schedule_today_scorecard',
        'schedule': crontab(minute=30, hour=23),
    },
    'run-daily-btb': {
        'task': 'connectors.tasks.cricket_tasks.schedule_today_btb',
        'schedule': crontab(minute=30, hour=23),
    },
}

