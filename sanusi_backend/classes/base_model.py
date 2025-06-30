from django.db import models


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class BaseModel(models.Model):
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    is_deleted = models.BooleanField(default=False)

    objects = ActiveManager()  # Default: only non-deleted
    all_objects = models.Manager()  # Includes soft-deleted

    class Meta:
        abstract = True
