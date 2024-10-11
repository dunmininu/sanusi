from django.db import models

# Create your models here.
class Lead(models.Model):
    first_name = models.CharField(max_length=256, default="", blank=True)
    last_name = models.CharField(max_length=256, default="", blank=True)
    phone_number = models.CharField(max_length=256, default="", blank=True)
    email = models.EmailField(max_length=256, null=True, blank=True)
