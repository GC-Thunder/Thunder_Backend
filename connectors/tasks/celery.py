from celery import Celery

# Create Celery app
app = Celery(
    'connectors',  # This is the app name that should match the package
    broker='redis://localhost:6379/0',
    backend='redis://localhost',
    include=['connectors.tasks.cricket_tasks']  # Full import path to your tasks module
)

# Load custom configuration from celeryconfig.py
app.config_from_object('connectors.tasks.celeryconfig')

if __name__ == '__main__':
    app.start()
