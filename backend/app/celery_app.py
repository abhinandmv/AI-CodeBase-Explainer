from celery import Celery
from .config import settings

celery = Celery(
    "app",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    imports=("app.tasks",),   # <-- IMPORTANT: force import
)

# OR autodiscover (also works)
celery.autodiscover_tasks(["app"])