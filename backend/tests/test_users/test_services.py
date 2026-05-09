import pytest

from apps.audit.models import AuditLog
from apps.users import services
from apps.users.models import PublicKey, Role, User, UserRole


@pytest.mark.django_db
class TestCreateUser:
    def test_creates_user(self, user_admin, role_employee):
        data = {
            "email": "new@test.com",
            "surname": "Новый",
            "name": "Пользователь",
            "patronymic": "",
            "password": "securepass123",
        }
        user = services.create_user(data, created_by=user_admin)
        assert User.objects.filter(email="new@test.com").exists()
        assert user.check_password("securepass123")

    def test_assigns_roles_on_creation(self, user_admin, role_employee):
        data = {
            "email": "new@test.com",
            "surname": "Новый",
            "name": "Пользователь",
            "patronymic": "",
            "password": "securepass123",
            "role_ids": [role_employee.id],
        }
        user = services.create_user(data, created_by=user_admin)
        assert user.roles.filter(id=role_employee.id).exists()

    def test_writes_audit_log(self, user_admin):
        data = {
            "email": "audit@test.com",
            "surname": "Аудит",
            "name": "Тест",
            "patronymic": "",
            "password": "pass12345",
        }
        user = services.create_user(data, created_by=user_admin)
        assert AuditLog.objects.filter(
            action_type=AuditLog.ActionType.CREATE_USER,
            target_id=user.pk,
        ).exists()


@pytest.mark.django_db
class TestAssignRole:
    def test_assigns_role(self, user_admin, user_plain, role_employee):
        services.assign_role(user_plain, role_employee, assigned_by=user_admin)
        assert user_plain.roles.filter(id=role_employee.id).exists()

    def test_idempotent_no_duplicate_audit(self, user_admin, user_plain, role_employee):
        services.assign_role(user_plain, role_employee, assigned_by=user_admin)
        services.assign_role(user_plain, role_employee, assigned_by=user_admin)
        count = AuditLog.objects.filter(
            action_type=AuditLog.ActionType.ASSIGN_ROLE,
            target_id=user_plain.pk,
        ).count()
        assert count == 1

    def test_writes_audit_log(self, user_admin, user_plain, role_employee):
        services.assign_role(user_plain, role_employee, assigned_by=user_admin)
        assert AuditLog.objects.filter(
            action_type=AuditLog.ActionType.ASSIGN_ROLE,
            target_id=user_plain.pk,
        ).exists()


@pytest.mark.django_db
class TestRemoveRole:
    def test_removes_role(self, user_admin, user_employee, role_employee):
        services.remove_role(user_employee, role_employee, removed_by=user_admin)
        assert not user_employee.roles.filter(id=role_employee.id).exists()

    def test_no_error_when_role_not_assigned(self, user_admin, user_plain, role_employee):
        services.remove_role(user_plain, role_employee, removed_by=user_admin)

    def test_no_audit_when_role_not_assigned(self, user_admin, user_plain, role_employee):
        services.remove_role(user_plain, role_employee, removed_by=user_admin)
        assert not AuditLog.objects.filter(action_type=AuditLog.ActionType.REMOVE_ROLE).exists()

    def test_writes_audit_log(self, user_admin, user_employee, role_employee):
        services.remove_role(user_employee, role_employee, removed_by=user_admin)
        assert AuditLog.objects.filter(
            action_type=AuditLog.ActionType.REMOVE_ROLE,
            target_id=user_employee.pk,
        ).exists()


@pytest.mark.django_db
class TestDeactivateUser:
    def test_sets_inactive(self, user_admin, user_employee):
        services.deactivate_user(user_employee, deactivated_by=user_admin)
        user_employee.refresh_from_db()
        assert not user_employee.is_active

    def test_writes_audit_log(self, user_admin, user_employee):
        services.deactivate_user(user_employee, deactivated_by=user_admin)
        assert AuditLog.objects.filter(
            action_type=AuditLog.ActionType.DEACTIVATE_USER,
            target_id=user_employee.pk,
        ).exists()


@pytest.mark.django_db
class TestRegisterPublicKey:
    def test_creates_public_key(self, user_signer):
        key = services.register_public_key(user_signer, "-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----", user_signer)
        assert PublicKey.objects.filter(id=key.id, user=user_signer).exists()

    def test_writes_audit_log(self, user_signer):
        key = services.register_public_key(user_signer, "-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----", user_signer)
        assert AuditLog.objects.filter(
            action_type=AuditLog.ActionType.REGISTER_KEY,
            target_id=key.pk,
        ).exists()
