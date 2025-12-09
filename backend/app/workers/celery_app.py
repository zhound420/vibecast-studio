"""Celery application configuration."""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "vibecast",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.tasks.generation",
        "app.workers.tasks.export",
    ],
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Concurrency - only one GPU task at a time
    worker_concurrency=1,

    # Task routing
    task_routes={
        "app.workers.tasks.generation.*": {"queue": "generation"},
        "app.workers.tasks.export.*": {"queue": "export"},
    },

    # Task timeouts
    task_time_limit=7200,  # 2 hours max for long-form generation
    task_soft_time_limit=6900,  # Soft limit at 1h55m

    # Result expiration
    result_expires=86400,  # 24 hours

    # Prefetch one task at a time (important for GPU memory)
    worker_prefetch_multiplier=1,

    # Task acknowledgement
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-old-files": {
            "task": "app.workers.tasks.cleanup.cleanup_old_files",
            "schedule": 3600.0,  # Every hour
        },
    },
)


# Optional: Task base class with model manager
class GPUTask(celery_app.Task):
    """Base task class for GPU-bound tasks."""

    _model_manager = None

    @property
    def model_manager(self):
        """Lazy-load the model manager."""
        if self._model_manager is None:
            from app.services.vibevoice import ModelManager
            self._model_manager = ModelManager()
        return self._model_manager
