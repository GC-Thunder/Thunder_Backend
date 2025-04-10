# Async background jobs to scrape data

from celery import Celery
from connectors.espn_scraper import ESPNConnector

app = Celery("tasks", broker="redis://localhost:6379/0")
connector = ESPNConnector()

@app.task
def fetch_live_scores():
    scores = connector.load_live_scores()
    # send to database, log, or print
    print("Fetched scores:", scores)
