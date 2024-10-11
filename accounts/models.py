import uuid as uuid_lib

from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as DefaultUserManager
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.conf import settings

from business.models import Business


# Create your models here.
class UserManager(BaseUserManager):
    def filter_by_business(self, business):
        return self.filter(businesses=business)
    
    def filter_by_role(self, role_name):
        return self.filter(groups__name=role_name)
    
    def get_active_users(self):
        return self.filter(is_active=True)
    
    def get_superusers(self):
        return self.filter(is_superuser=True)



class User(AbstractBaseUser, PermissionsMixin):
    uuid = models.UUIDField(unique=True, default=uuid_lib.uuid4)
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    password_reset_otp_secret = models.CharField(max_length=32, blank=True)
  
    # Reference to one or more businesses
    businesses = models.ManyToManyField(
        Business,
        related_name='user_businesses',
        blank=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []


    # Use the custom manager for this model
    objects = UserManager()
    
    class Meta:
        # Specify the default ordering for user queries
        ordering = ['first_name']

        # Define a user-friendly verbose name for the model
        verbose_name = 'User'
        verbose_name_plural = 'Users'

        # Set the app label for the model (used in admin interface)
        app_label = 'accounts'

        # Define permissions for the model (if needed)
        # permissions = [
        #     ('can_view_user', 'Can view user details'),
        #     ('can_edit_user', 'Can edit user details'),
        #     # Define additional permissions as required
        # ]

    def save(self):
        self.uuid = None

    # Define related_name for groups and user_permissions


class EmailAddress(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid_lib.uuid4)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="email_addresses",
        on_delete=models.CASCADE,
    )
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

    def confirm(self):
        self.is_verified = True
        self.save(update_fields=["is_verified"])
        self.user.save()