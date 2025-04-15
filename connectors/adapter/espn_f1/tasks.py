from celery import Celery
from scrapers.f1_scraper import fetch_f1_race_data
from celery.schedules import crontab
from datetime import datetime
# Initialize celery app
app = Celery('tasks', broker='redis://localhost:6379/0')
app.config_from_object('celery_config')  # Load config from celery_config.py

# Register task
@app.task
def scrape_f1(year=None):
    # Use current year if not passed
    if year is None:
        year = datetime.utcnow().year
    return fetch_f1_race_data(year)

# Set periodic schedule
app.conf.beat_schedule = {
    'run-f1-once-a-week': {
        'task': 'tasks.scrape_f1',
        'schedule': crontab(minute='*/10'),
        'args': [],  # Defaults to current year dynamically
    },
}