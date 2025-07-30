from django.contrib import admin

from .models import ModulePermission, Role


@admin.register(ModulePermission)
class ModulePermissionAdmin(admin.ModelAdmin):
    list_display = ("name", "code")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "is_owner")
    filter_horizontal = ("permissions",)
