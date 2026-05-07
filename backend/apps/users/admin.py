from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import PublicKey, Role, User, UserRole


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "surname", "name", "position", "is_active", "registered_at")
    list_filter = ("is_active", "is_staff")
    search_fields = ("email", "surname", "name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Личные данные", {"fields": ("surname", "name", "patronymic", "position")}),
        ("Права", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Даты", {"fields": ("registered_at", "last_login_at")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "surname", "name", "patronymic", "password1", "password2"),
        }),
    )
    readonly_fields = ("registered_at", "last_login_at")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)


@admin.register(PublicKey)
class PublicKeyAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    readonly_fields = ("created_at",)
