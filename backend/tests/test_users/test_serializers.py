import pytest

from apps.users.serializers import UserCreateSerializer


@pytest.mark.django_db
class TestUserCreateSerializer:
    BASE_DATA = {
        "email": "new@test.com",
        "surname": "Новый",
        "name": "Пользователь",
        "patronymic": "",
        "password": "securepass123",
    }

    def test_valid_data(self):
        serializer = UserCreateSerializer(data=self.BASE_DATA)
        assert serializer.is_valid(), serializer.errors

    def test_duplicate_email(self, user_employee):
        data = {**self.BASE_DATA, "email": user_employee.email}
        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_password_too_short(self):
        data = {**self.BASE_DATA, "password": "short"}
        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_missing_required_fields(self):
        serializer = UserCreateSerializer(data={"email": "x@test.com"})
        assert not serializer.is_valid()
        assert "surname" in serializer.errors
        assert "name" in serializer.errors

    def test_invalid_role_ids(self, role_employee):
        data = {**self.BASE_DATA, "role_ids": [9999]}
        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "role_ids" in serializer.errors

    def test_valid_role_ids(self, role_employee):
        data = {**self.BASE_DATA, "role_ids": [role_employee.id]}
        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_patronymic_optional(self):
        data = {k: v for k, v in self.BASE_DATA.items() if k != "patronymic"}
        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
