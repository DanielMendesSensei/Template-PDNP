import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('PROJECT_NAME')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery configuration
app.conf.update(
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_reject_on_worker_lost=True,
    
    # Task routing
    task_routes={
        'apps.downloads.tasks.process_download': {'queue': 'downloads'},
        'apps.downloads.tasks.cleanup_old_files': {'queue': 'cleanup'},
        'apps.downloads.tasks.generate_thumbnail': {'queue': 'media'},
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-old-downloads': {
            'task': 'apps.downloads.tasks.cleanup_old_files',
            'schedule': 3600.0,  # Every hour
        },
        'update-ytdlp': {
            'task': 'apps.downloads.tasks.update_ytdlp',
            'schedule': 86400.0,  # Every day
        },
        'clear-redis-cache': {
            'task': 'apps.downloads.tasks.clear_expired_cache',
            'schedule': 1800.0,  # Every 30 minutes
        },
    },
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')