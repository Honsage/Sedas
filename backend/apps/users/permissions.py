from rest_framework.permissions import BasePermission

from .models import Role


class IsAdministrator(BasePermission):
    """Разрешение для пользователей с ролью Администратор"""

    message = "Требуется роль Администратор"

    def has_permission(self, request, view):
        """Проверяет наличие роли Администратора у пользователя"""
        return request.user.is_authenticated and request.user.has_role(Role.ADMINISTRATOR)


class IsSigner(BasePermission):
    """Разрешение для пользователей с ролью Подписант"""

    message = "Требуется роль Подписант"

    def has_permission(self, request, view):
        """Проверяет наличие роли Подписанта у пользователя"""
        return request.user.is_authenticated and request.user.has_role(Role.SIGNER)


class IsEmployee(BasePermission):
    """Разрешение для пользователей с любой ролью в системе"""

    message = "Требуется наличие роли в системе"

    def has_permission(self, request, view):
        """Проверяет, назначена ли пользователю хотя бы одна роль"""
        return request.user.is_authenticated and request.user.roles.exists()
