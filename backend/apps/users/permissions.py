from rest_framework.permissions import BasePermission

from .models import Role


class IsAdministrator(BasePermission):
    """Доступ только для пользователей с ролью Администратор"""

    message = "Требуется роль Администратор"

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.has_role(Role.ADMINISTRATOR)
        )


class IsSigner(BasePermission):
    """Доступ только для пользователей с ролью Подписант"""

    message = "Требуется роль Подписант"

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.has_role(Role.SIGNER)
        )


class IsEmployee(BasePermission):
    """Доступ для любого аутентифицированного сотрудника"""

    message = "Требуется роль Сотрудник или выше"

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.roles.exists()
