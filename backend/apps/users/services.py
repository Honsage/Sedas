from apps.audit.models import AuditLog

from .models import Role, User, UserRole


def create_user(validated_data: dict, created_by: User) -> User:
    role_ids = validated_data.pop("role_ids", [])
    password = validated_data.pop("password")

    user = User(**validated_data)
    user.set_password(password)
    user.save()

    if role_ids:
        roles = Role.objects.filter(id__in=role_ids)
        UserRole.objects.bulk_create([UserRole(user=user, role=r) for r in roles])

    AuditLog.objects.create(
        user=created_by,
        action_type=AuditLog.ActionType.CREATE_USER,
        target_type=AuditLog.TargetType.USER,
        target_id=user.pk,
    )
    return user


def assign_role(user: User, role: Role, assigned_by: User) -> None:
    _, created = UserRole.objects.get_or_create(user=user, role=role)
    if created:
        AuditLog.objects.create(
            user=assigned_by,
            action_type=AuditLog.ActionType.ASSIGN_ROLE,
            target_type=AuditLog.TargetType.USER,
            target_id=user.pk,
        )


def remove_role(user: User, role: Role, removed_by: User) -> None:
    deleted, _ = UserRole.objects.filter(user=user, role=role).delete()
    if deleted:
        AuditLog.objects.create(
            user=removed_by,
            action_type=AuditLog.ActionType.REMOVE_ROLE,
            target_type=AuditLog.TargetType.USER,
            target_id=user.pk,
        )


def deactivate_user(user: User, deactivated_by: User) -> None:
    user.is_active = False
    user.save(update_fields=["is_active"])
    AuditLog.objects.create(
        user=deactivated_by,
        action_type=AuditLog.ActionType.DEACTIVATE_USER,
        target_type=AuditLog.TargetType.USER,
        target_id=user.pk,
    )
