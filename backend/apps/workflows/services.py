from django.utils import timezone

from apps.audit.models import AuditLog
from apps.documents.models import Document
from apps.users.models import User

from .models import DocumentWorkflow, StepAssignment, Workflow, WorkflowStep


def start_workflow(document: Document, workflow: Workflow, actor: User) -> DocumentWorkflow:
    """Создаёт экземпляр процесса согласования для документа, записывает в аудит"""
    if document.status != "under_review":
        raise ValueError("Запустить маршрут можно только для документа со статусом 'На согласовании'")

    document_workflow = DocumentWorkflow.objects.create(
        document=document,
        workflow=workflow,
    )

    AuditLog.objects.create(
        user=actor,
        action_type=AuditLog.ActionType.START_WORKFLOW,
        target_type=AuditLog.TargetType.DOCUMENT_WORKFLOW,
        target_id=document_workflow.pk,
    )

    return document_workflow


def assign_user_to_step(
    document_workflow: DocumentWorkflow,
    workflow_step: WorkflowStep,
    user: User,
    actor: User,
) -> StepAssignment:
    """Назначает пользователя на шаг процесса, записывает в аудит"""
    assignment = StepAssignment.objects.create(
        document_workflow=document_workflow,
        workflow_step=workflow_step,
        assigned_user=user,
    )

    AuditLog.objects.create(
        user=actor,
        action_type=AuditLog.ActionType.ASSIGN_STEP,
        target_type=AuditLog.TargetType.STEP_ASSIGNMENT,
        target_id=assignment.pk,
    )

    return assignment


def make_decision(
    assignment: StepAssignment,
    decision: str,
    actor: User,
) -> StepAssignment:
    """Фиксирует решение по назначению и продвигает процесс согласования"""
    if assignment.decision is not None:
        raise ValueError("Решение по этому назначению уже вынесено")

    assignment.decision = decision
    assignment.decided_at = timezone.now()
    assignment.save(update_fields=["decision", "decided_at"])

    action_type = (
        AuditLog.ActionType.APPROVE_STEP
        if decision == StepAssignment.Decision.APPROVED
        else AuditLog.ActionType.REJECT_STEP
    )
    AuditLog.objects.create(
        user=actor,
        action_type=action_type,
        target_type=AuditLog.TargetType.STEP_ASSIGNMENT,
        target_id=assignment.pk,
    )

    _advance_workflow(assignment, decision)

    return assignment


def _advance_workflow(assignment: StepAssignment, decision: str) -> None:
    """Продвигает процесс: одобрение — следующий шаг; revision — возврат в черновик"""
    if decision == StepAssignment.Decision.REVISION:
        assignment.document_workflow.document.return_for_revision()
        return

    if decision == StepAssignment.Decision.APPROVED:
        document_workflow = assignment.document_workflow
        if document_workflow.is_complete():
            document_workflow.document.approve()
