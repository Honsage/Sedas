import pytest

from apps.audit.models import AuditLog
from apps.documents.models import DocumentStatus
from apps.workflows import services
from apps.workflows.models import DocumentWorkflow, StepAssignment


@pytest.mark.django_db
class TestStartWorkflow:
    def test_creates_document_workflow(self, document_under_review, workflow, user_employee):
        dw = services.start_workflow(document_under_review, workflow, actor=user_employee)
        assert DocumentWorkflow.objects.filter(id=dw.id).exists()

    def test_raises_when_not_under_review(self, document_draft, workflow, user_employee):
        with pytest.raises(ValueError):
            services.start_workflow(document_draft, workflow, actor=user_employee)

    def test_raises_when_signed(self, document_signed, workflow, user_employee):
        with pytest.raises(ValueError):
            services.start_workflow(document_signed, workflow, actor=user_employee)

    def test_writes_audit_log(self, document_under_review, workflow, user_employee):
        dw = services.start_workflow(document_under_review, workflow, actor=user_employee)
        assert AuditLog.objects.filter(
            action_type=AuditLog.ActionType.START_WORKFLOW,
            target_id=dw.pk,
        ).exists()


@pytest.mark.django_db
class TestAssignUserToStep:
    def test_creates_assignment(self, document_workflow, user_employee):
        step = document_workflow.workflow.steps.first()
        assignment = services.assign_user_to_step(
            document_workflow, step, user_employee, actor=user_employee
        )
        assert StepAssignment.objects.filter(id=assignment.id).exists()

    def test_assigns_correct_user(self, document_workflow, user_employee):
        step = document_workflow.workflow.steps.first()
        assignment = services.assign_user_to_step(
            document_workflow, step, user_employee, actor=user_employee
        )
        assert assignment.assigned_user == user_employee

    def test_writes_audit_log(self, document_workflow, user_employee):
        step = document_workflow.workflow.steps.first()
        assignment = services.assign_user_to_step(
            document_workflow, step, user_employee, actor=user_employee
        )
        assert AuditLog.objects.filter(
            action_type=AuditLog.ActionType.ASSIGN_STEP,
            target_id=assignment.pk,
        ).exists()


@pytest.mark.django_db
class TestMakeDecision:
    def test_approved_not_last_step_no_status_change(
        self, db, document_under_review, workflow_two_steps, user_employee, user_signer
    ):
        dw = DocumentWorkflow.objects.create(document=document_under_review, workflow=workflow_two_steps)
        step1 = workflow_two_steps.steps.get(step_order=1)
        assignment = StepAssignment.objects.create(
            document_workflow=dw, workflow_step=step1, assigned_user=user_employee
        )
        services.make_decision(assignment, StepAssignment.Decision.APPROVED, actor=user_employee)
        document_under_review.refresh_from_db()
        assert document_under_review.status == DocumentStatus.UNDER_REVIEW

    def test_approved_last_step_signs_document(self, document_workflow, step_assignment, user_employee):
        services.make_decision(step_assignment, StepAssignment.Decision.APPROVED, actor=user_employee)
        document_workflow.document.refresh_from_db()
        assert document_workflow.document.status == DocumentStatus.SIGNED

    def test_revision_returns_document_to_draft(self, document_workflow, step_assignment, user_employee):
        services.make_decision(step_assignment, StepAssignment.Decision.REVISION, actor=user_employee)
        document_workflow.document.refresh_from_db()
        assert document_workflow.document.status == DocumentStatus.DRAFT

    def test_rejected_no_status_change(self, document_workflow, step_assignment, user_employee):
        services.make_decision(step_assignment, StepAssignment.Decision.REJECTED, actor=user_employee)
        document_workflow.document.refresh_from_db()
        assert document_workflow.document.status == DocumentStatus.UNDER_REVIEW

    def test_raises_when_already_decided(self, document_workflow, step_assignment, user_employee):
        services.make_decision(step_assignment, StepAssignment.Decision.APPROVED, actor=user_employee)
        with pytest.raises(ValueError):
            services.make_decision(step_assignment, StepAssignment.Decision.APPROVED, actor=user_employee)

    def test_saves_decision_and_decided_at(self, document_workflow, step_assignment, user_employee):
        services.make_decision(step_assignment, StepAssignment.Decision.REJECTED, actor=user_employee)
        step_assignment.refresh_from_db()
        assert step_assignment.decision == StepAssignment.Decision.REJECTED
        assert step_assignment.decided_at is not None

    def test_writes_audit_log_approve(self, document_workflow, step_assignment, user_employee):
        services.make_decision(step_assignment, StepAssignment.Decision.APPROVED, actor=user_employee)
        assert AuditLog.objects.filter(action_type=AuditLog.ActionType.APPROVE_STEP).exists()

    def test_writes_audit_log_reject(self, document_workflow, step_assignment, user_employee):
        services.make_decision(step_assignment, StepAssignment.Decision.REJECTED, actor=user_employee)
        assert AuditLog.objects.filter(action_type=AuditLog.ActionType.REJECT_STEP).exists()
