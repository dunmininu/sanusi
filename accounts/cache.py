from django.core.cache import cache
from django.contrib.auth import get_user_model
from typing import List, Optional, Dict, Any
from .models import Permissions

User = get_user_model()

# Cache configuration
PERMISSION_CACHE_TIMEOUT = 3600  # 1 hour
USER_PERMISSIONS_CACHE_KEY = "user_permissions_{}"
USER_ROLES_CACHE_KEY = "user_roles_{}"
ROLE_PERMISSIONS_CACHE_KEY = "role_permissions_{}"


class PermissionCache:
    """Cache manager for user permissions and roles."""
    
    @staticmethod
    def get_user_permissions_cache_key(user_id: str) -> str:
        """Get cache key for user permissions."""
        return USER_PERMISSIONS_CACHE_KEY.format(user_id)
    
    @staticmethod
    def get_user_roles_cache_key(user_id: str) -> str:
        """Get cache key for user roles."""
        return USER_ROLES_CACHE_KEY.format(user_id)
    
    @staticmethod
    def get_role_permissions_cache_key(role_name: str) -> str:
        """Get cache key for role permissions."""
        return ROLE_PERMISSIONS_CACHE_KEY.format(role_name)
    
    @staticmethod
    def get_user_permissions(user_id: str) -> Optional[List[str]]:
        """Get cached user permissions."""
        cache_key = PermissionCache.get_user_permissions_cache_key(user_id)
        return cache.get(cache_key)
    
    @staticmethod
    def set_user_permissions(user_id: str, permissions: List[str]) -> None:
        """Cache user permissions."""
        cache_key = PermissionCache.get_user_permissions_cache_key(user_id)
        cache.set(cache_key, permissions, PERMISSION_CACHE_TIMEOUT)
    
    @staticmethod
    def get_user_roles(user_id: str) -> Optional[List[str]]:
        """Get cached user roles."""
        cache_key = PermissionCache.get_user_roles_cache_key(user_id)
        return cache.get(cache_key)
    
    @staticmethod
    def set_user_roles(user_id: str, roles: List[str]) -> None:
        """Cache user roles."""
        cache_key = PermissionCache.get_user_roles_cache_key(user_id)
        cache.set(cache_key, roles, PERMISSION_CACHE_TIMEOUT)
    
    @staticmethod
    def get_role_permissions(role_name: str) -> Optional[List[str]]:
        """Get cached role permissions."""
        cache_key = PermissionCache.get_role_permissions_cache_key(role_name)
        return cache.get(cache_key)
    
    @staticmethod
    def set_role_permissions(role_name: str, permissions: List[str]) -> None:
        """Cache role permissions."""
        cache_key = PermissionCache.get_role_permissions_cache_key(role_name)
        cache.set(cache_key, permissions, PERMISSION_CACHE_TIMEOUT)
    
    @staticmethod
    def invalidate_user_cache(user_id: str) -> None:
        """Invalidate all cache entries for a user."""
        cache.delete(PermissionCache.get_user_permissions_cache_key(user_id))
        cache.delete(PermissionCache.get_user_roles_cache_key(user_id))
    
    @staticmethod
    def invalidate_role_cache(role_name: str) -> None:
        """Invalidate cache entries for a role."""
        cache.delete(PermissionCache.get_role_permissions_cache_key(role_name))
    
    @staticmethod
    def clear_all_permission_cache() -> None:
        """Clear all permission-related cache entries."""
        # This is a simple approach - in production you might want to use cache versioning
        # or more sophisticated cache invalidation
        cache.clear()


class CachedUserPermissionManager:
    """Cached version of UserPermissionManager with performance optimizations."""
    
    @staticmethod
    def has_permission(user: User, permission_code: str) -> bool:
        """Check if a user has a specific permission (cached)."""
        # Check cache first
        user_id = str(user.id)
        cached_permissions = PermissionCache.get_user_permissions(user_id)
        
        if cached_permissions is None:
            # Cache miss - get from database and cache
            permissions = list(user.get_user_permissions())
            PermissionCache.set_user_permissions(user_id, permissions)
            cached_permissions = permissions
        
        return permission_code in cached_permissions
    
    @staticmethod
    def has_any_permission(user: User, permission_codes: List[str]) -> bool:
        """Check if a user has any of the specified permissions (cached)."""
        user_id = str(user.id)
        cached_permissions = PermissionCache.get_user_permissions(user_id)
        
        if cached_permissions is None:
            permissions = list(user.get_user_permissions())
            PermissionCache.set_user_permissions(user_id, permissions)
            cached_permissions = permissions
        
        return any(code in cached_permissions for code in permission_codes)
    
    @staticmethod
    def has_all_permissions(user: User, permission_codes: List[str]) -> bool:
        """Check if a user has all of the specified permissions (cached)."""
        user_id = str(user.id)
        cached_permissions = PermissionCache.get_user_permissions(user_id)
        
        if cached_permissions is None:
            permissions = list(user.get_user_permissions())
            PermissionCache.set_user_permissions(user_id, permissions)
            cached_permissions = permissions
        
        return all(code in cached_permissions for code in permission_codes)
    
    @staticmethod
    def get_user_permissions(user: User) -> List[str]:
        """Get all permissions for a user (cached)."""
        user_id = str(user.id)
        cached_permissions = PermissionCache.get_user_permissions(user_id)
        
        if cached_permissions is None:
            permissions = list(user.get_user_permissions())
            PermissionCache.set_user_permissions(user_id, permissions)
            return permissions
        
        return cached_permissions
    
    @staticmethod
    def get_user_roles(user: User) -> List[str]:
        """Get all roles for a user (cached)."""
        user_id = str(user.id)
        cached_roles = PermissionCache.get_user_roles(user_id)
        
        if cached_roles is None:
            roles = list(user.get_user_roles())
            PermissionCache.set_user_roles(user_id, roles)
            return roles
        
        return cached_roles
    
    @staticmethod
    def is_admin(user: User) -> bool:
        """Check if a user is an admin (cached)."""
        return CachedUserPermissionManager.has_permission(user, Permissions.SYSTEM_ADMIN) or user.roles.filter(is_owner=True).exists()
    
    @staticmethod
    def is_sales_agent(user: User) -> bool:
        """Check if a user is a sales agent (cached)."""
        return "sales_agent" in CachedUserPermissionManager.get_user_roles(user)
    
    @staticmethod
    def is_inventory_admin(user: User) -> bool:
        """Check if a user is an inventory admin (cached)."""
        return "inventory_admin" in CachedUserPermissionManager.get_user_roles(user)
    
    @staticmethod
    def can_access_chat(user: User) -> bool:
        """Check if a user can access chat functionality (cached)."""
        return CachedUserPermissionManager.has_permission(user, Permissions.CHAT_VIEW)
    
    @staticmethod
    def can_respond_to_chat(user: User) -> bool:
        """Check if a user can respond to chat messages (cached)."""
        return CachedUserPermissionManager.has_permission(user, Permissions.CHAT_RESPOND)
    
    @staticmethod
    def can_view_orders(user: User) -> bool:
        """Check if a user can view orders (cached)."""
        return CachedUserPermissionManager.has_permission(user, Permissions.ORDER_VIEW)
    
    @staticmethod
    def can_process_orders(user: User) -> bool:
        """Check if a user can process orders (cached)."""
        return CachedUserPermissionManager.has_permission(user, Permissions.ORDER_PROCESS)
    
    @staticmethod
    def can_view_products(user: User) -> bool:
        """Check if a user can view products (cached)."""
        return CachedUserPermissionManager.has_permission(user, Permissions.PRODUCT_VIEW)
    
    @staticmethod
    def can_edit_products(user: User) -> bool:
        """Check if a user can edit products (cached)."""
        return CachedUserPermissionManager.has_permission(user, Permissions.PRODUCT_UPDATE)
    
    @staticmethod
    def can_manage_inventory(user: User) -> bool:
        """Check if a user can manage inventory (cached)."""
        return CachedUserPermissionManager.has_permission(user, Permissions.PRODUCT_MANAGE_INVENTORY)
    
    @staticmethod
    def invalidate_user_cache(user: User) -> None:
        """Invalidate cache for a specific user."""
        PermissionCache.invalidate_user_cache(str(user.id))


class CachedRoleManager:
    """Cached version of RoleManager with performance optimizations."""
    
    @staticmethod
    def get_role_permissions(role_name: str) -> List[str]:
        """Get all permissions for a specific role (cached)."""
        cached_permissions = PermissionCache.get_role_permissions(role_name)
        
        if cached_permissions is None:
            from .models import Role
            try:
                role = Role.objects.get(name=role_name, is_active=True)
                permissions = list(role.permissions.filter(is_active=True).values_list('code', flat=True))
                PermissionCache.set_role_permissions(role_name, permissions)
                return permissions
            except Role.DoesNotExist:
                return []
        
        return cached_permissions
    
    @staticmethod
    def invalidate_role_cache(role_name: str) -> None:
        """Invalidate cache for a specific role."""
        PermissionCache.invalidate_role_cache(role_name)


# Cache middleware for automatic cache invalidation
class PermissionCacheMiddleware:
    """Middleware to automatically invalidate permission cache when user roles change."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Invalidate cache for the current user if they're authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Only invalidate on certain actions that might change permissions
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                # This is a simple approach - in production you might want to be more specific
                # about which endpoints should trigger cache invalidation
                CachedUserPermissionManager.invalidate_user_cache(request.user)
        
        return response 