from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from . import services
from .models import PublicKey, Role, User
from .permissions import IsAdministrator, IsEmployee
from .serializers import PublicKeySerializer, RoleSerializer, UserCreateSerializer, UserSerializer, UserUpdateSerializer

_TAG_AUTH = ["Аутентификация"]
_TAG_USERS = ["Пользователи"]
_TAG_ROLES = ["Роли"]
_TAG_KEYS = ["Публичные ключи"]

_RESP_400 = openapi.Response("Ошибка валидации", schema=openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={"detail": openapi.Schema(type=openapi.TYPE_STRING)},
))
_RESP_403 = openapi.Response("Доступ запрещён", schema=openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={"detail": openapi.Schema(type=openapi.TYPE_STRING)},
))
_RESP_404 = openapi.Response("Не найдено", schema=openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={"detail": openapi.Schema(type=openapi.TYPE_STRING)},
))
_RESP_204 = openapi.Response("Нет содержимого")

_ROLE_ID_BODY = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=["role_id"],
    properties={"role_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID роли")},
)


class LoginView(TokenObtainPairView):
    """Представление для получения JWT-токенов"""

    @swagger_auto_schema(
        tags=_TAG_AUTH,
        operation_summary="Получить JWT-токены",
        operation_description="Выдаёт access и refresh токены по email и паролю. Обновляет last_login_at.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "password"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, format="password"),
            },
        ),
        responses={
            200: openapi.Response("Токены выданы", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "access": openapi.Schema(type=openapi.TYPE_STRING),
                    "refresh": openapi.Schema(type=openapi.TYPE_STRING),
                },
            )),
            401: openapi.Response("Неверные учётные данные"),
        },
        security=[],
    )
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

    @swagger_auto_schema(
        tags=_TAG_USERS,
        operation_summary="Список пользователей",
        responses={200: UserSerializer(many=True), 403: _RESP_403},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=_TAG_USERS,
        operation_summary="Профиль пользователя",
        responses={200: UserSerializer, 403: _RESP_403, 404: _RESP_404},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=_TAG_USERS,
        operation_summary="Создать пользователя",
        request_body=UserCreateSerializer,
        responses={201: UserSerializer, 400: _RESP_400, 403: _RESP_403},
    )
    def create(self, request, *args, **kwargs):
        """Создаёт нового пользователя"""
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.create_user(serializer.validated_data, request.user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        tags=_TAG_USERS,
        operation_summary="Обновить пользователя",
        request_body=UserUpdateSerializer,
        responses={200: UserSerializer, 400: _RESP_400, 403: _RESP_403, 404: _RESP_404},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=_TAG_USERS,
        operation_summary="Частично обновить пользователя",
        request_body=UserUpdateSerializer,
        responses={200: UserSerializer, 400: _RESP_400, 403: _RESP_403, 404: _RESP_404},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=_TAG_USERS,
        operation_summary="Деактивировать пользователя",
        operation_description="Не удаляет запись — устанавливает is_active=False.",
        responses={204: _RESP_204, 403: _RESP_403, 404: _RESP_404},
    )
    def destroy(self, request, *args, **kwargs):
        """Деактивирует пользователя вместо физического удаления"""
        user = self.get_object()
        services.deactivate_user(user, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserAssignRoleView(APIView):
    """Представление для назначения роли пользователю"""

    permission_classes = [IsAdministrator]

    @swagger_auto_schema(
        tags=_TAG_USERS,
        operation_summary="Назначить роль пользователю",
        request_body=_ROLE_ID_BODY,
        responses={200: UserSerializer, 403: _RESP_403, 404: _RESP_404},
    )
    def post(self, request, pk):
        """Назначает роль указанному пользователю"""
        user = get_object_or_404(User, pk=pk)
        role = get_object_or_404(Role, id=request.data.get("role_id"))
        services.assign_role(user, role, request.user)
        return Response(UserSerializer(user).data)


class UserRemoveRoleView(APIView):
    """Представление для снятия роли с пользователя"""

    permission_classes = [IsAdministrator]

    @swagger_auto_schema(
        tags=_TAG_USERS,
        operation_summary="Снять роль с пользователя",
        request_body=_ROLE_ID_BODY,
        responses={200: UserSerializer, 403: _RESP_403, 404: _RESP_404},
    )
    def post(self, request, pk):
        """Снимает роль с указанного пользователя"""
        user = get_object_or_404(User, pk=pk)
        role = get_object_or_404(Role, id=request.data.get("role_id"))
        services.remove_role(user, role, request.user)
        return Response(UserSerializer(user).data)


class PublicKeyListView(APIView):
    """Представление для просмотра и добавления публичных ключей текущего пользователя"""

    permission_classes = [IsEmployee]

    @swagger_auto_schema(
        tags=_TAG_KEYS,
        operation_summary="Список публичных ключей",
        operation_description="Возвращает публичные ключи текущего авторизованного пользователя.",
        responses={200: PublicKeySerializer(many=True)},
    )
    def get(self, request):
        """Возвращает список публичных ключей текущего пользователя"""
        keys = request.user.public_keys.all()
        return Response(PublicKeySerializer(keys, many=True).data)

    @swagger_auto_schema(
        tags=_TAG_KEYS,
        operation_summary="Зарегистрировать публичный ключ",
        operation_description="Сохраняет PEM-публичный ключ. Используется для верификации RSA-SHA256 подписей.",
        request_body=PublicKeySerializer,
        responses={201: PublicKeySerializer, 400: _RESP_400},
    )
    def post(self, request):
        """Регистрирует новый публичный ключ для текущего пользователя"""
        serializer = PublicKeySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = services.register_public_key(
            user=request.user,
            public_key_pem=serializer.validated_data["public_key"],
            actor=request.user,
        )
        return Response(PublicKeySerializer(key).data, status=status.HTTP_201_CREATED)


class PublicKeyDetailView(APIView):
    """Представление для удаления публичного ключа"""

    permission_classes = [IsEmployee]

    @swagger_auto_schema(
        tags=_TAG_KEYS,
        operation_summary="Удалить публичный ключ",
        responses={204: _RESP_204, 404: _RESP_404},
    )
    def delete(self, request, key_pk):
        """Удаляет публичный ключ текущего пользователя"""
        key = get_object_or_404(PublicKey, pk=key_pk, user=request.user)
        key.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleViewSet(viewsets.ModelViewSet):
    """Набор представлений для управления ролями"""

    queryset = Role.objects.all()
    serializer_class = RoleSerializer

    def get_permissions(self):
        """Возвращает разрешения: запись только Администратору, чтение — всем авторизованным"""
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdministrator()]
        return super().get_permissions()

    @swagger_auto_schema(tags=_TAG_ROLES, operation_summary="Список ролей",
                         responses={200: RoleSerializer(many=True)})
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAG_ROLES, operation_summary="Роль",
                         responses={200: RoleSerializer, 404: _RESP_404})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAG_ROLES, operation_summary="Создать роль",
                         request_body=RoleSerializer,
                         responses={201: RoleSerializer, 400: _RESP_400, 403: _RESP_403})
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAG_ROLES, operation_summary="Обновить роль",
                         request_body=RoleSerializer,
                         responses={200: RoleSerializer, 400: _RESP_400, 403: _RESP_403, 404: _RESP_404})
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAG_ROLES, operation_summary="Частично обновить роль",
                         request_body=RoleSerializer,
                         responses={200: RoleSerializer, 400: _RESP_400, 403: _RESP_403, 404: _RESP_404})
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAG_ROLES, operation_summary="Удалить роль",
                         responses={204: _RESP_204, 403: _RESP_403, 404: _RESP_404})
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
