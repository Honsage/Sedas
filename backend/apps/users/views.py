from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from . import services
from .models import Role, User
from .permissions import IsAdministrator
from .serializers import (
    RoleAssignSerializer,
    RoleSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class LoginView(TokenObtainPairView):
    """
    Получение JWT-токенов (access + refresh).
    Обновляет last_login_at при успешной аутентификации
    """

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            try:
                user = User.objects.get(email=request.data.get("email"))
                user.last_login_at = timezone.now()
                user.save(update_fields=["last_login_at"])
            except User.DoesNotExist:
                pass
        return response


class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD пользователей. Доступен только Администратору.
    DELETE деактивирует пользователя (is_active=False), не удаляет запись
    """

    permission_classes = [IsAdministrator]

    def get_queryset(self):
        return User.objects.prefetch_related("roles").order_by("id")

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ("update", "partial_update"):
            return UserUpdateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.create_user(serializer.validated_data, request.user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        services.deactivate_user(user, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="assign-role")
    def assign_role(self, request, pk=None):
        """Назначить роль пользователю"""
        user = self.get_object()
        serializer = RoleAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = Role.objects.get(id=serializer.validated_data["role_id"])
        services.assign_role(user, role, request.user)
        return Response(UserSerializer(user).data)

    @action(detail=True, methods=["post"], url_path="remove-role")
    def remove_role(self, request, pk=None):
        """Снять роль с пользователя"""
        user = self.get_object()
        serializer = RoleAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = Role.objects.get(id=serializer.validated_data["role_id"])
        services.remove_role(user, role, request.user)
        return Response(UserSerializer(user).data)


class RoleViewSet(viewsets.ModelViewSet):
    """
    CRUD ролей. Чтение доступно всем аутентифицированным.
    Создание/изменение/удаление — только Администратору
    """

    queryset = Role.objects.all()
    serializer_class = RoleSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdministrator()]
        return super().get_permissions()
