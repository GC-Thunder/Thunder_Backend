from celery import Celery
from scraper_football import fetch_espn_match_data
from celery.schedules import crontab

# Initialize celery app
app = Celery('tasks', broker='redis://localhost:6379/0')
app.config_from_object('celery_config')  # Load config from celery_config.py

# Register task
@app.task
def run_scraper():
    return fetch_espn_match_data()

# Set periodic schedule
app.conf.beat_schedule = {
    'run-every-5-minutes': {
        'task': 'tasks.run_scraper',
        'schedule': crontab(minute='*/5'),
    },
}