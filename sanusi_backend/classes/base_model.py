from django.db import models
import uuid

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class BaseModel(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, db_index=True, primary_key=True
    )
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    is_deleted = models.BooleanField(default=False)

    objects = ActiveManager()  # Default: only non-deleted
    all_objects = models.Manager()  # Includes soft-deleted

    class Meta:
        abstract = True
