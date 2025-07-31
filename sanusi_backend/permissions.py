from rest_framework.permissions import BasePermission
from accounts.models import Permissions


class HasScopes(BasePermission):
    """
    Check if user has all required scopes.
    """
    required_scopes: list[str] = []

    def has_permission(self, request, view):
        scopes = getattr(view, "required_scopes", self.required_scopes)
        if not scopes:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.has_all_permissions(scopes)


class HasAnyScope(BasePermission):
    """
    Check if user has any of the required scopes.
    """
    required_scopes: list[str] = []

    def has_permission(self, request, view):
        scopes = getattr(view, "required_scopes", self.required_scopes)
        if not scopes:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.has_any_permission(scopes)


class HasAllScopes(BasePermission):
    """
    Check if user has all of the required scopes.
    """
    required_scopes: list[str] = []

    def has_permission(self, request, view):
        scopes = getattr(view, "required_scopes", self.required_scopes)
        if not scopes:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.has_all_permissions(scopes)


class IsBusinessOwner(BasePermission):
    """
    Check if user is the owner of the business being accessed.
    Business owners automatically have all permissions.
    """
    
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        
        # Get business from URL parameters or view context
        business_id = self._get_business_id(request, view)
        if not business_id:
            return False
        
        # Check if user owns this business
        from business.utils import is_business_owner
        from business.models import Business
        
        try:
            business = Business.objects.get(id=business_id)
            return is_business_owner(user, business)
        except Business.DoesNotExist:
            return False
    
    def _get_business_id(self, request, view):
        """Extract business ID from request or view context"""
        # Try to get from URL parameters
        business_id = request.data.get('business_id') or request.query_params.get('business_id')
        
        # Try to get from URL path parameters
        if not business_id:
            business_id = request.resolver_match.kwargs.get('company_id') or request.resolver_match.kwargs.get('business_id')
        
        # Try to get from view context
        if not business_id and hasattr(view, 'get_business_id'):
            business_id = view.get_business_id(request)
        
        return business_id


# Chat Permissions
class ChatPermissions:
    class CanViewChat(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.CHAT_VIEW)

    class CanCreateChat(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.CHAT_CREATE)

    class CanUpdateChat(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.CHAT_UPDATE)

    class CanDeleteChat(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.CHAT_DELETE)

    class CanRespondToChat(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.CHAT_RESPOND)


# Order Permissions
class OrderPermissions:
    class CanViewOrder(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.ORDER_VIEW)

    class CanCreateOrder(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.ORDER_CREATE)

    class CanUpdateOrder(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.ORDER_UPDATE)

    class CanDeleteOrder(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.ORDER_DELETE)

    class CanProcessOrder(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.ORDER_PROCESS)


# Product Permissions
class ProductPermissions:
    class CanViewProduct(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.PRODUCT_VIEW)

    class CanCreateProduct(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.PRODUCT_CREATE)

    class CanUpdateProduct(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.PRODUCT_UPDATE)

    class CanDeleteProduct(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.PRODUCT_DELETE)

    class CanManageInventory(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.PRODUCT_MANAGE_INVENTORY)


# Customer Permissions
class CustomerPermissions:
    class CanViewCustomer(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.CUSTOMER_VIEW)

    class CanCreateCustomer(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.CUSTOMER_CREATE)

    class CanUpdateCustomer(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.CUSTOMER_UPDATE)

    class CanDeleteCustomer(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.CUSTOMER_DELETE)


# Business Permissions
class BusinessPermissions:
    class CanViewBusiness(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.BUSINESS_VIEW)

    class CanCreateBusiness(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.BUSINESS_CREATE)

    class CanUpdateBusiness(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.BUSINESS_UPDATE)

    class CanDeleteBusiness(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.BUSINESS_DELETE)


# Category Permissions
class CategoryPermissions:
    class CanViewCategory(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.PRODUCT_VIEW)

    class CanCreateCategory(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.PRODUCT_CREATE)

    class CanUpdateCategory(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.PRODUCT_UPDATE)

    class CanDeleteCategory(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.PRODUCT_DELETE)


# User Management Permissions
class UserPermissions:
    class CanViewUser(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.USER_VIEW)

    class CanCreateUser(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.USER_CREATE)

    class CanUpdateUser(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.USER_UPDATE)

    class CanDeleteUser(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.USER_DELETE)

    class CanInviteUser(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.USER_INVITE)


# Analytics Permissions
class AnalyticsPermissions:
    class CanViewAnalytics(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.ANALYTICS_VIEW)

    class CanExportAnalytics(BasePermission):
        def has_permission(self, request, view):
            # Business owners have all permissions
            if IsBusinessOwner().has_permission(request, view):
                return True
            return request.user.has_module_permission(Permissions.ANALYTICS_EXPORT)


# System Permissions
class SystemPermissions:
    class IsSystemAdmin(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.SYSTEM_ADMIN)

    class CanManageSettings(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.SYSTEM_SETTINGS)


class SalesAgentPermissions(BasePermission):
    """
    Check if user has sales agent capabilities.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        required_permissions = [
            Permissions.CHAT_VIEW, Permissions.CHAT_RESPOND,
            Permissions.ORDER_VIEW, Permissions.ORDER_PROCESS,
            Permissions.PRODUCT_VIEW,
            Permissions.CUSTOMER_VIEW, Permissions.CUSTOMER_CREATE, Permissions.CUSTOMER_UPDATE,
            Permissions.BUSINESS_VIEW,
        ]
        return user.has_any_permission(required_permissions)


class InventoryAdminPermissions(BasePermission):
    """
    Check if user has inventory admin capabilities.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        required_permissions = [
            Permissions.CHAT_VIEW, Permissions.CHAT_RESPOND,
            Permissions.ORDER_VIEW, Permissions.ORDER_PROCESS,
            Permissions.PRODUCT_VIEW, Permissions.PRODUCT_CREATE, Permissions.PRODUCT_UPDATE, Permissions.PRODUCT_DELETE, Permissions.PRODUCT_MANAGE_INVENTORY,
            Permissions.CUSTOMER_VIEW, Permissions.CUSTOMER_CREATE, Permissions.CUSTOMER_UPDATE,
            Permissions.BUSINESS_VIEW,
        ]
        return user.has_any_permission(required_permissions)


class AdminPermissions(BasePermission):
    """
    Check if user has admin capabilities.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.has_module_permission(Permissions.SYSTEM_ADMIN) or user.roles.filter(is_owner=True).exists()
