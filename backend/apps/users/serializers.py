from rest_framework import serializers

from .models import PublicKey, Role, User


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "description"]


class UserSerializer(serializers.ModelSerializer):
    """Чтение профиля пользователя"""

    roles = RoleSerializer(many=True, read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "surname", "name", "patronymic", "full_name",
            "position", "is_active", "registered_at", "last_login_at", "roles",
        ]
        read_only_fields = ["id", "registered_at", "last_login_at"]

    def get_full_name(self, obj):
        return obj.get_full_name()


class UserCreateSerializer(serializers.Serializer):
    """Создание нового пользователя администратором"""

    email = serializers.EmailField()
    surname = serializers.CharField(max_length=32)
    name = serializers.CharField(max_length=32)
    patronymic = serializers.CharField(max_length=32, default="")
    position = serializers.CharField(max_length=255, default="")
    password = serializers.CharField(min_length=8, write_only=True)
    role_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value

    def validate_role_ids(self, value):
        if value:
            existing = Role.objects.filter(id__in=value).values_list("id", flat=True)
            missing = set(value) - set(existing)
            if missing:
                raise serializers.ValidationError(f"Роли не найдены: {missing}")
        return value


class UserUpdateSerializer(serializers.ModelSerializer):
    """Обновление профиля пользователя"""

    class Meta:
        model = User
        fields = ["surname", "name", "patronymic", "position", "is_active"]


class RoleAssignSerializer(serializers.Serializer):
    """Назначение / снятие роли"""

    role_id = serializers.IntegerField()

    def validate_role_id(self, value):
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError("Роль не найдена")
        return value


class PublicKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicKey
        fields = ["id", "public_key", "created_at"]
        read_only_fields = ["id", "created_at"]
