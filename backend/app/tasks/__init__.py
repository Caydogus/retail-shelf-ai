from .training_tasks import celery_app, train_model_task, analyze_image_task

__all__ = ['celery_app', 'train_model_task', 'analyze_image_task']
