from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    Полиморфный журнал действий. FK на target намеренно отсутствует —
    запись сохраняется даже после удаления целевого объекта
    """

    class ActionType(models.TextChoices):
        # Пользователи
        CREATE_USER = "create_user", "Создание пользователя"
        DEACTIVATE_USER = "deactivate_user", "Деактивация пользователя"
        ASSIGN_ROLE = "assign_role", "Назначение роли"
        REMOVE_ROLE = "remove_role", "Снятие роли"
        # Документы
        CREATE_DOCUMENT = "create_document", "Создание документа"
        UPDATE_DOCUMENT = "update_document", "Обновление документа"
        ADD_VERSION = "add_version", "Добавление версии"
        SUBMIT_FOR_REVIEW = "submit_for_review", "Отправка на согласование"
        RETURN_FOR_REVISION = "return_for_revision", "Возврат на доработку"
        ARCHIVE_DOCUMENT = "archive_document", "Архивация документа"
        # Согласование
        START_WORKFLOW = "start_workflow", "Запуск маршрута"
        APPROVE_STEP = "approve_step", "Одобрение шага"
        REJECT_STEP = "reject_step", "Отклонение шага"
        # ЭЦП
        SIGN_DOCUMENT = "sign_document", "Подписание документа"
        REGISTER_KEY = "register_key", "Регистрация публичного ключа"

    class TargetType(models.TextChoices):
        USER = "User", "Пользователь"
        DOCUMENT = "Document", "Документ"
        DOCUMENT_VERSION = "DocumentVersion", "Версия документа"
        WORKFLOW = "Workflow", "Маршрут"
        DOCUMENT_WORKFLOW = "DocumentWorkflow", "Процесс согласования"
        STEP_ASSIGNMENT = "StepAssignment", "Назначение"
        SIGNATURE = "Signature", "Подпись"
        PUBLIC_KEY = "PublicKey", "Публичный ключ"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
    )
    action_type = models.CharField(max_length=100, choices=ActionType.choices)
    target_type = models.CharField(max_length=50, choices=TargetType.choices)
    target_id = models.BigIntegerField()
    done_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_log"
        verbose_name = "Запись аудита"
        verbose_name_plural = "Журнал аудита"
        ordering = ["-done_at"]

    def __str__(self):
        return f"{self.done_at:%Y-%m-%d %H:%M} | {self.action_type} | {self.target_type}#{self.target_id}"
