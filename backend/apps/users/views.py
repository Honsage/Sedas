from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from . import services
from .models import Role, User
from .permissions import IsAdministrator
from .serializers import RoleSerializer, UserCreateSerializer, UserSerializer, UserUpdateSerializer


class LoginView(TokenObtainPairView):
    """Представление для получения JWT-токенов"""

    def post(self, request, *args, **kwargs):
        """Выдаёт access и refresh токены, обновляет время последнего входа"""
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            User.objects.filter(email=request.data.get("email")).update(
                last_login_at=timezone.now()
            )
        return response


class UserViewSet(viewsets.ModelViewSet):
    """Набор представлений для управления пользователями (только Администратор)"""

    permission_classes = [IsAdministrator]

    def get_queryset(self):
        """Возвращает список всех пользователей с предзагрузкой ролей"""
        return User.objects.prefetch_related("roles").order_by("id")

    def get_serializer_class(self):
        """Возвращает класс сериализатора в зависимости от действия"""
        if self.action in ("update", "partial_update"):
            return UserUpdateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        """Создаёт нового пользователя"""
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.create_user(serializer.validated_data, request.user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Деактивирует пользователя вместо физического удаления"""
        user = self.get_object()
        services.deactivate_user(user, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserAssignRoleView(APIView):
    """Представление для назначения роли пользователю"""

    permission_classes = [IsAdministrator]

    def post(self, request, pk):
        """Назначает роль указанному пользователю"""
        user = get_object_or_404(User, pk=pk)
        role = get_object_or_404(Role, id=request.data.get("role_id"))
        services.assign_role(user, role, request.user)
        return Response(UserSerializer(user).data)


class UserRemoveRoleView(APIView):
    """Представление для снятия роли с пользователя"""

    permission_classes = [IsAdministrator]

    def post(self, request, pk):
        """Снимает роль с указанного пользователя"""
        user = get_object_or_404(User, pk=pk)
        role = get_object_or_404(Role, id=request.data.get("role_id"))
        services.remove_role(user, role, request.user)
        return Response(UserSerializer(user).data)


class RoleViewSet(viewsets.ModelViewSet):
    """Набор представлений для управления ролями"""

    queryset = Role.objects.all()
    serializer_class = RoleSerializer

    def get_permissions(self):
        """Возвращает разрешения: запись только Администратору, чтение — всем авторизованным"""
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdministrator()]
        return super().get_permissions()
