#!/bin/bash

# Start the Celery worker
celery -A tasks worker --loglevel=info
