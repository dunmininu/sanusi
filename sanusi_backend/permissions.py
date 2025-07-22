from rest_framework.permissions import BasePermission


class HasScopes(BasePermission):
    """Checks user has all required module permissions."""

    required_scopes: list[str] = []

    def has_permission(self, request, view):
        scopes = getattr(view, "required_scopes", self.required_scopes)
        if not scopes:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        for scope in scopes:
            if not user.has_module_permission(scope):
                return False
        return True
