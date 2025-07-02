from django.db import models
from sanusi_backend.classes.base_model import BaseModel


# Create your models here.
class Lead(BaseModel):
    # id = models.UUIDField(
    #     default=uuid.uuid4, unique=True, db_index=True, primary_key=True
    # )
    first_name = models.CharField(max_length=256, default="", blank=True)
    last_name = models.CharField(max_length=256, default="", blank=True)
    phone_number = models.CharField(max_length=256, default="", blank=True)
    email = models.EmailField(max_length=256, null=True, blank=True)
