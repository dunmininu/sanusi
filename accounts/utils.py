from typing import List, Optional
from django.contrib.auth import get_user_model
from .models import Role, ModulePermission, Permissions, Roles

User = get_user_model()


class RoleManager:
    """Utility class for managing roles and permissions."""
    
    @staticmethod
    def get_role_by_name(role_name: str) -> Optional[Role]:
        """Get a role by name."""
        try:
            return Role.objects.get(name=role_name, is_active=True)
        except Role.DoesNotExist:
            return None
    
    @staticmethod
    def get_all_roles() -> List[Role]:
        """Get all active roles."""
        return list(Role.objects.filter(is_active=True))
    
    @staticmethod
    def get_system_roles() -> List[Role]:
        """Get all system roles."""
        return list(Role.objects.filter(is_system_role=True, is_active=True))
    
    @staticmethod
    def create_custom_role(name: str, description: str = "", permissions: List[str] = None) -> Role:
        """Create a custom role with specified permissions."""
        if permissions is None:
            permissions = []
        
        role = Role.objects.create(
            name=name,
            description=description,
            is_system_role=False,
            is_active=True
        )
        
        if permissions:
            perms = ModulePermission.objects.filter(code__in=permissions, is_active=True)
            role.permissions.set(perms)
        
        return role
    
    @staticmethod
    def assign_role_to_user(user: User, role_name: str) -> bool:
        """Assign a role to a user."""
        try:
            role = Role.objects.get(name=role_name, is_active=True)
            user.roles.add(role)
            return True
        except Role.DoesNotExist:
            return False
    
    @staticmethod
    def remove_role_from_user(user: User, role_name: str) -> bool:
        """Remove a role from a user."""
        try:
            role = Role.objects.get(name=role_name)
            user.roles.remove(role)
            return True
        except Role.DoesNotExist:
            return False
    
    @staticmethod
    def get_user_roles(user: User) -> List[Role]:
        """Get all roles for a user."""
        return list(user.roles.filter(is_active=True))
    
    @staticmethod
    def get_user_role_names(user: User) -> List[str]:
        """Get all role names for a user."""
        return list(user.get_user_roles())


class PermissionManager:
    """Utility class for managing permissions."""
    
    @staticmethod
    def get_permission_by_code(code: str) -> Optional[ModulePermission]:
        """Get a permission by code."""
        try:
            return ModulePermission.objects.get(code=code, is_active=True)
        except ModulePermission.DoesNotExist:
            return None
    
    @staticmethod
    def get_permissions_by_module(module: str) -> List[ModulePermission]:
        """Get all permissions for a specific module."""
        return list(ModulePermission.objects.filter(module=module, is_active=True))
    
    @staticmethod
    def get_all_permissions() -> List[ModulePermission]:
        """Get all active permissions."""
        return list(ModulePermission.objects.filter(is_active=True))
    
    @staticmethod
    def create_permission(code: str, name: str, description: str = "", module: str = "") -> ModulePermission:
        """Create a new permission."""
        return ModulePermission.objects.create(
            code=code,
            name=name,
            description=description,
            module=module,
            is_active=True
        )


class UserPermissionManager:
    """Utility class for managing user permissions."""
    
    @staticmethod
    def has_permission(user: User, permission_code: str) -> bool:
        """Check if a user has a specific permission."""
        return user.has_module_permission(permission_code)
    
    @staticmethod
    def has_any_permission(user: User, permission_codes: List[str]) -> bool:
        """Check if a user has any of the specified permissions."""
        return user.has_any_permission(permission_codes)
    
    @staticmethod
    def has_all_permissions(user: User, permission_codes: List[str]) -> bool:
        """Check if a user has all of the specified permissions."""
        return user.has_all_permissions(permission_codes)
    
    @staticmethod
    def get_user_permissions(user: User) -> List[str]:
        """Get all permissions for a user."""
        return list(user.get_user_permissions())
    
    @staticmethod
    def is_admin(user: User) -> bool:
        """Check if a user is an admin."""
        return user.has_module_permission(Permissions.SYSTEM_ADMIN) or user.roles.filter(is_owner=True).exists()
    
    @staticmethod
    def is_sales_agent(user: User) -> bool:
        """Check if a user is a sales agent."""
        return user.roles.filter(name=Roles.SALES_AGENT, is_active=True).exists()
    
    @staticmethod
    def is_inventory_admin(user: User) -> bool:
        """Check if a user is an inventory admin."""
        return user.roles.filter(name=Roles.INVENTORY_ADMIN, is_active=True).exists()
    
    @staticmethod
    def can_access_chat(user: User) -> bool:
        """Check if a user can access chat functionality."""
        return user.has_module_permission(Permissions.CHAT_VIEW)
    
    @staticmethod
    def can_respond_to_chat(user: User) -> bool:
        """Check if a user can respond to chat messages."""
        return user.has_module_permission(Permissions.CHAT_RESPOND)
    
    @staticmethod
    def can_view_orders(user: User) -> bool:
        """Check if a user can view orders."""
        return user.has_module_permission(Permissions.ORDER_VIEW)
    
    @staticmethod
    def can_process_orders(user: User) -> bool:
        """Check if a user can process orders."""
        return user.has_module_permission(Permissions.ORDER_PROCESS)
    
    @staticmethod
    def can_view_products(user: User) -> bool:
        """Check if a user can view products."""
        return user.has_module_permission(Permissions.PRODUCT_VIEW)
    
    @staticmethod
    def can_edit_products(user: User) -> bool:
        """Check if a user can edit products."""
        return user.has_module_permission(Permissions.PRODUCT_UPDATE)
    
    @staticmethod
    def can_manage_inventory(user: User) -> bool:
        """Check if a user can manage inventory."""
        return user.has_module_permission(Permissions.PRODUCT_MANAGE_INVENTORY)


def get_role_permissions(role_name: str) -> List[str]:
    """Get all permissions for a specific role."""
    try:
        role = Role.objects.get(name=role_name, is_active=True)
        return list(role.permissions.filter(is_active=True).values_list('code', flat=True))
    except Role.DoesNotExist:
        return []


def assign_user_to_role(user_email: str, role_name: str) -> bool:
    """Assign a user to a role by email."""
    try:
        user = User.objects.get(email=user_email)
        role = Role.objects.get(name=role_name, is_active=True)
        user.roles.add(role)
        return True
    except (User.DoesNotExist, Role.DoesNotExist):
        return False


def create_user_with_role(email: str, password: str, role_name: str, **user_fields) -> Optional[User]:
    """Create a user and assign them to a role."""
    try:
        user = User.objects.create_user(email=email, password=password, **user_fields)
        role = Role.objects.get(name=role_name, is_active=True)
        user.roles.add(role)
        return user
    except Role.DoesNotExist:
        return None 