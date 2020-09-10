CELERY_IMPORTS = ('tasks')
CELERY_IGNORE_RESULT = False
BROKER_HOST = "127.0.0.1" #IP address of the server running RabbitMQ and Celery
BROKER_PORT = 5672
BROKER_URL = 'amqp://'

from datetime import timedelta
from celery.schedules import crontab


CELERYBEAT_SCHEDULE = {
    'check_flights-every-30min': {
        'task': 'tasks.check_flights_task',
        'schedule': crontab(minute=0),
    },
    'anual_update-everyday-night': {
        'task': 'tasks.update_cache_task',
        'schedule': crontab(hour=0, minute=0),
    },
}
