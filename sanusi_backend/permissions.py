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


# Chat Permissions
class ChatPermissions:
    class CanViewChat(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.CHAT_VIEW)

    class CanCreateChat(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.CHAT_CREATE)

    class CanUpdateChat(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.CHAT_UPDATE)

    class CanDeleteChat(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.CHAT_DELETE)

    class CanRespondToChat(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.CHAT_RESPOND)


# Order Permissions
class OrderPermissions:
    class CanViewOrder(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.ORDER_VIEW)

    class CanCreateOrder(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.ORDER_CREATE)

    class CanUpdateOrder(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.ORDER_UPDATE)

    class CanDeleteOrder(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.ORDER_DELETE)

    class CanProcessOrder(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.ORDER_PROCESS)


# Product Permissions
class ProductPermissions:
    class CanViewProduct(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.PRODUCT_VIEW)

    class CanCreateProduct(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.PRODUCT_CREATE)

    class CanUpdateProduct(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.PRODUCT_UPDATE)

    class CanDeleteProduct(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.PRODUCT_DELETE)

    class CanManageInventory(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.PRODUCT_MANAGE_INVENTORY)


# Customer Permissions
class CustomerPermissions:
    class CanViewCustomer(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.CUSTOMER_VIEW)

    class CanCreateCustomer(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.CUSTOMER_CREATE)

    class CanUpdateCustomer(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.CUSTOMER_UPDATE)

    class CanDeleteCustomer(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.CUSTOMER_DELETE)


# Business Permissions
class BusinessPermissions:
    class CanViewBusiness(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.BUSINESS_VIEW)

    class CanCreateBusiness(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.BUSINESS_CREATE)

    class CanUpdateBusiness(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.BUSINESS_UPDATE)

    class CanDeleteBusiness(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.BUSINESS_DELETE)


# Category Permissions
class CategoryPermissions:
    class CanViewCategory(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.PRODUCT_VIEW)

    class CanCreateCategory(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.PRODUCT_CREATE)

    class CanUpdateCategory(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.PRODUCT_UPDATE)

    class CanDeleteCategory(BasePermission):
        def has_permission(self, request, view):
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
            return request.user.has_module_permission(Permissions.ANALYTICS_VIEW)

    class CanExportAnalytics(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.ANALYTICS_EXPORT)


# System Permissions
class SystemPermissions:
    class IsSystemAdmin(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.SYSTEM_ADMIN)

    class CanManageSettings(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.SYSTEM_SETTINGS)


# Convenience Permission Classes
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
