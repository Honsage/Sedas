from django.conf import settings
from django.db import models


class Workflow(models.Model):
    """Шаблон маршрута согласования"""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "workflows_workflow"
        verbose_name = "Маршрут"
        verbose_name_plural = "Маршруты"

    def __str__(self):
        return self.name


class WorkflowStep(models.Model):
    """Шаг маршрута — роль, которая должна одобрить документ"""

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="steps")
    step_order = models.PositiveIntegerField()
    role = models.ForeignKey("users.Role", on_delete=models.PROTECT, related_name="workflow_steps")

    class Meta:
        db_table = "workflows_step"
        verbose_name = "Шаг маршрута"
        verbose_name_plural = "Шаги маршрута"
        unique_together = [("workflow", "step_order")]
        ordering = ["step_order"]

    def __str__(self):
        return f"{self.workflow.name}: шаг {self.step_order} ({self.role})"


class DocumentWorkflow(models.Model):
    """Экземпляр процесса: документ, идущий по конкретному маршруту"""

    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="document_workflows",
    )
    workflow = models.ForeignKey(Workflow, on_delete=models.PROTECT, related_name="document_workflows")

    class Meta:
        db_table = "workflows_document_workflow"
        verbose_name = "Процесс согласования"
        verbose_name_plural = "Процессы согласования"
        unique_together = [("document", "workflow")]

    def __str__(self):
        return f"{self.document} / {self.workflow}"

    def get_current_step(self):
        """Возвращает текущий активный шаг"""
        return (
            self.assignments
            .filter(decision__isnull=True)
            .order_by("workflow_step__step_order")
            .first()
        )

    def is_complete(self):
        """Все ли шаги согласования пройдены"""
        total_steps = self.workflow.steps.count()
        approved = self.assignments.filter(decision=StepAssignment.Decision.APPROVED).count()
        return approved >= total_steps


class StepAssignment(models.Model):
    """Назначение пользователя на шаг и его решение"""

    class Decision(models.TextChoices):
        APPROVED = "approved", "Одобрено"
        REJECTED = "rejected", "Отклонено"
        REVISION = "revision", "На доработку"

    document_workflow = models.ForeignKey(
        DocumentWorkflow,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    workflow_step = models.ForeignKey(WorkflowStep, on_delete=models.PROTECT, related_name="assignments")
    assigned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="step_assignments",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    decision = models.CharField(max_length=20, choices=Decision.choices, null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "workflows_step_assignment"
        verbose_name = "Назначение"
        verbose_name_plural = "Назначения"

    def __str__(self):
        return f"{self.assigned_user} / шаг {self.workflow_step.step_order}: {self.decision or 'ожидает'}"
