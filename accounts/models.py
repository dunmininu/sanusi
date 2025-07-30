import uuid as uuid_lib

from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.conf import settings
from sanusi_backend.classes.base_model import BaseModel

from business.models import Business


# Permission constants for better organization
class Permissions:
    # Chat permissions
    CHAT_VIEW = "chat.view"
    CHAT_CREATE = "chat.create"
    CHAT_UPDATE = "chat.update"
    CHAT_DELETE = "chat.delete"
    CHAT_RESPOND = "chat.respond"
    
    # Order permissions
    ORDER_VIEW = "order.view"
    ORDER_CREATE = "order.create"
    ORDER_UPDATE = "order.update"
    ORDER_DELETE = "order.delete"
    ORDER_PROCESS = "order.process"
    
    # Product permissions
    PRODUCT_VIEW = "product.view"
    PRODUCT_CREATE = "product.create"
    PRODUCT_UPDATE = "product.update"
    PRODUCT_DELETE = "product.delete"
    PRODUCT_MANAGE_INVENTORY = "product.manage_inventory"
    
    # Customer permissions
    CUSTOMER_VIEW = "customer.view"
    CUSTOMER_CREATE = "customer.create"
    CUSTOMER_UPDATE = "customer.update"
    CUSTOMER_DELETE = "customer.delete"
    
    # Business permissions
    BUSINESS_VIEW = "business.view"
    BUSINESS_CREATE = "business.create"
    BUSINESS_UPDATE = "business.update"
    BUSINESS_DELETE = "business.delete"
    
    # User management permissions
    USER_VIEW = "user.view"
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_INVITE = "user.invite"
    
    # Analytics permissions
    ANALYTICS_VIEW = "analytics.view"
    ANALYTICS_EXPORT = "analytics.export"
    
    # System permissions
    SYSTEM_ADMIN = "system.admin"
    SYSTEM_SETTINGS = "system.settings"

    @classmethod
    def get_all_permissions(cls):
        """Get all permission codes as a list"""
        return [attr for attr in dir(cls) if not attr.startswith('_') and isinstance(getattr(cls, attr), str)]


# Role constants
class Roles:
    ADMIN = "admin"
    SALES_AGENT = "sales_agent"
    INVENTORY_ADMIN = "inventory_admin"
    
    @classmethod
    def get_all_roles(cls):
        """Get all role names as a list"""
        return [attr for attr in dir(cls) if not attr.startswith('_') and isinstance(getattr(cls, attr), str)]


# Create your models here.
class UserManager(BaseUserManager):
    def filter_by_business(self, business):
        return self.filter(businesses=business)

    def filter_by_role(self, role_name):
        return self.filter(roles__name=role_name)

    def get_active_users(self):
        return self.filter(is_active=True)

    def get_superusers(self):
        return self.filter(is_superuser=True)

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(default=uuid_lib.uuid4, unique=True, db_index=True, primary_key=True)
    # uuid = models.UUIDField(unique=True, default=uuid_lib.uuid4)
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    password_reset_otp_secret = models.CharField(max_length=32, blank=True)
    complete_on_boarding = models.BooleanField(default=False)
    step = models.IntegerField(default=0)

    # Reference to one or more businesses
    businesses = models.ManyToManyField(
        Business,
        related_name="user_businesses",
        blank=True,
    )
    settings = models.JSONField(default=dict)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    # Use the custom manager for this model
    objects = UserManager()

    # Onboarding constants
    TOTAL_ONBOARDING_STEPS = 7

    class Meta:
        # Specify the default ordering for user queries
        ordering = ["first_name"]

        # Define a user-friendly verbose name for the model
        verbose_name = "User"
        verbose_name_plural = "Users"

        # Set the app label for the model (used in admin interface)
        app_label = "accounts"

        # Define permissions for the model (if needed)
        # permissions = [
        #     ('can_view_user', 'Can view user details'),
        #     ('can_edit_user', 'Can edit user details'),
        #     # Define additional permissions as required
        # ]

    # def save(self):
    #     self.uuid = None

    def get_default_business(self):
        """Helper method to get the default business object"""
        default_business_id = self.settings.get("default_business")
        if default_business_id:
            try:
                return self.businesses.get(id=default_business_id)
            except Business.DoesNotExist:
                return None
        return self.businesses.first() if self.businesses.exists() else None

    def set_default_business(self, business):
        """Helper method to set a specific business as default"""
        if business in self.businesses.all():
            self.settings["default_business"] = str(business.id)
            self.save(update_fields=["settings"])

    def update_onboarding_step(self, step_number):
        """
        Update the user's onboarding step and check if onboarding is complete

        Args:
            step_number (int): The step number to update to (1-7)

        Returns:
            bool: True if onboarding is now complete, False otherwise
        """
        if not isinstance(step_number, int) or step_number < 0:
            raise ValueError("Step number must be a positive integer")

        if step_number > self.TOTAL_ONBOARDING_STEPS:
            raise ValueError(f"Step number cannot exceed {self.TOTAL_ONBOARDING_STEPS}")

        # Update the step only if it's moving forward
        if step_number > self.step:
            self.step = step_number

            # Check if onboarding is complete
            if self.step >= self.TOTAL_ONBOARDING_STEPS:
                self.complete_on_boarding = True

            # Save the changes
            self.save(update_fields=["step", "complete_on_boarding"])

            return self.complete_on_boarding

        return False

    def next_onboarding_step(self):
        """
        Move to the next onboarding step

        Returns:
            bool: True if onboarding is now complete, False otherwise
        """
        return self.update_onboarding_step(self.step + 1)

    def get_onboarding_progress(self):
        """
        Get the current onboarding progress

        Returns:
            dict: Dictionary containing progress information
        """
        return {
            "current_step": self.step,
            "total_steps": self.TOTAL_ONBOARDING_STEPS,
            "progress_percentage": (self.step / self.TOTAL_ONBOARDING_STEPS) * 100,
            "is_complete": self.complete_on_boarding,
            "remaining_steps": max(0, self.TOTAL_ONBOARDING_STEPS - self.step),
        }

    def reset_onboarding(self):
        """
        Reset the user's onboarding progress
        """
        self.step = 0
        self.complete_on_boarding = False
        self.save(update_fields=["step", "complete_on_boarding"])

    def is_onboarding_complete(self):
        """
        Check if the user has completed onboarding

        Returns:
            bool: True if onboarding is complete, False otherwise
        """
        return self.complete_on_boarding

    @property
    def onboarding_completion_percentage(self):
        """
        Property to get onboarding completion percentage

        Returns:
            float: Completion percentage (0-100)
        """
        return (self.step / self.TOTAL_ONBOARDING_STEPS) * 100

    def user_on_boarding(self):
        """
        Helper method for user onboarding - returns current progress

        Returns:
            dict: Current onboarding progress
        """
        return self.get_onboarding_progress()

    def save(self, *args, **kwargs):
        """
        Override save method to ensure onboarding completion is properly tracked
        """
        # Auto-complete onboarding if step reaches the total
        if self.step >= self.TOTAL_ONBOARDING_STEPS:
            self.complete_on_boarding = True

        super().save(*args, **kwargs)

    # Define related_name for groups and user_permissions


class EmailAddress(BaseModel):
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


class ModulePermission(BaseModel):
    """Permission used to control access to specific modules."""

    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    module = models.CharField(max_length=50, blank=True, help_text="Module this permission belongs to")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"
        app_label = "accounts"
        ordering = ['module', 'name']

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.name


class Role(BaseModel):
    """A group of permissions that can be assigned to users."""

    name = models.CharField(max_length=100, unique=True)
    permissions = models.ManyToManyField(ModulePermission, related_name="roles", blank=True)
    is_owner = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    is_system_role = models.BooleanField(default=False, help_text="System roles cannot be deleted")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        app_label = "accounts"
        ordering = ['name']

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.name

    def add_permission(self, permission_code):
        """Add a permission to this role by code"""
        try:
            permission = ModulePermission.objects.get(code=permission_code, is_active=True)
            self.permissions.add(permission)
            return True
        except ModulePermission.DoesNotExist:
            return False

    def remove_permission(self, permission_code):
        """Remove a permission from this role by code"""
        try:
            permission = ModulePermission.objects.get(code=permission_code)
            self.permissions.remove(permission)
            return True
        except ModulePermission.DoesNotExist:
            return False

    def has_permission(self, permission_code):
        """Check if this role has a specific permission"""
        return self.permissions.filter(code=permission_code, is_active=True).exists()


# Extend the User model with role assignments
User.add_to_class(
    "roles",
    models.ManyToManyField(
        Role,
        related_name="users",
        blank=True,
    ),
)


def user_has_module_permission(self, code: str) -> bool:
    """Check if the user has a specific module permission."""
    if self.roles.filter(is_owner=True).exists():
        return True
    return self.roles.filter(permissions__code=code, permissions__is_active=True).exists()


def user_has_any_permission(self, codes: list) -> bool:
    """Check if the user has any of the specified permissions."""
    if self.roles.filter(is_owner=True).exists():
        return True
    return self.roles.filter(permissions__code__in=codes, permissions__is_active=True).exists()


def user_has_all_permissions(self, codes: list) -> bool:
    """Check if the user has all of the specified permissions."""
    if self.roles.filter(is_owner=True).exists():
        return True
    user_permissions = set(self.roles.filter(is_active=True).values_list('permissions__code', flat=True))
    return all(code in user_permissions for code in codes)


def get_user_permissions(self) -> list:
    """Get all permissions for the user."""
    if self.roles.filter(is_owner=True).exists():
        return ModulePermission.objects.filter(is_active=True).values_list('code', flat=True)
    return list(self.roles.filter(is_active=True).values_list('permissions__code', flat=True).distinct())


def get_user_roles(self) -> list:
    """Get all roles for the user."""
    return list(self.roles.filter(is_active=True).values_list('name', flat=True))


User.add_to_class("has_module_permission", user_has_module_permission)
User.add_to_class("has_any_permission", user_has_any_permission)
User.add_to_class("has_all_permissions", user_has_all_permissions)
User.add_to_class("get_user_permissions", get_user_permissions)
User.add_to_class("get_user_roles", get_user_roles)


class Invite(BaseModel):
    """Stores user invitations with scoped roles."""

    email = models.EmailField()
    token = models.CharField(max_length=128, unique=True)
    roles = models.ManyToManyField(Role, related_name="invites", blank=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="sent_invites",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        app_label = "accounts"

    def __str__(self):  # pragma: no cover - simple representation
        return self.email
