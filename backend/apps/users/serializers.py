from rest_framework import serializers

from .models import PublicKey, Role, User


class RoleSerializer(serializers.ModelSerializer):
    """Сериализатор бизнес-роли"""

    class Meta:
        model = Role
        fields = ["id", "name", "description"]


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор профиля пользователя (на чтение)"""

    roles = RoleSerializer(many=True, read_only=True)
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "surname", "name", "patronymic", "full_name",
            "position", "is_active", "registered_at", "last_login_at", "roles",
        ]
        read_only_fields = ["id", "registered_at", "last_login_at"]


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор на создание пользователя"""

    # patronymic необязателен при создании
    patronymic = serializers.CharField(max_length=32, required=False, default="")
    # password принимается при создании, но никогда не возвращается
    password = serializers.CharField(min_length=8, write_only=True)
    role_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list, write_only=True
    )

    class Meta:
        model = User
        fields = ["email", "surname", "name", "patronymic", "position", "password", "role_ids"]

    def validate_email(self, value):
        """Проверяет уникальность email"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value

    def validate_role_ids(self, value):
        """Проверяет, что все переданные ID ролей существуют в системе"""
        if value:
            existing_ids = set(Role.objects.filter(id__in=value).values_list("id", flat=True))
            missing = set(value) - existing_ids
            if missing:
                raise serializers.ValidationError(f"Роли не найдены: {missing}")
        return value


class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор на обновление профиля пользователя"""

    class Meta:
        model = User
        fields = ["surname", "name", "patronymic", "position", "is_active"]


class PublicKeySerializer(serializers.ModelSerializer):
    """Сериализатор публичного ключа пользователя"""

    class Meta:
        model = PublicKey
        fields = ["id", "public_key", "created_at"]
        read_only_fields = ["id", "created_at"]
