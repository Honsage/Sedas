import pytest

from apps.workflows.models import StepAssignment


@pytest.mark.django_db
class TestDocumentWorkflowGetCurrentStep:
    def test_returns_pending_assignment(self, document_workflow, step_assignment):
        current = document_workflow.get_current_step()
        assert current == step_assignment

    def test_returns_none_when_all_decided(self, document_workflow, step_assignment):
        step_assignment.decision = StepAssignment.Decision.APPROVED
        step_assignment.save(update_fields=["decision"])
        assert document_workflow.get_current_step() is None

    def test_returns_lowest_step_order_pending(self, db, document_under_review, workflow_two_steps, user_employee, user_signer):
        from apps.workflows.models import DocumentWorkflow, StepAssignment
        dw = DocumentWorkflow.objects.create(document=document_under_review, workflow=workflow_two_steps)
        step1 = workflow_two_steps.steps.get(step_order=1)
        step2 = workflow_two_steps.steps.get(step_order=2)
        a1 = StepAssignment.objects.create(document_workflow=dw, workflow_step=step1, assigned_user=user_employee)
        a2 = StepAssignment.objects.create(document_workflow=dw, workflow_step=step2, assigned_user=user_signer)
        assert dw.get_current_step() == a1

    def test_returns_none_when_no_assignments(self, document_workflow):
        assert document_workflow.get_current_step() is None


@pytest.mark.django_db
class TestDocumentWorkflowIsComplete:
    def test_true_when_all_steps_approved(self, document_workflow, step_assignment):
        step_assignment.decision = StepAssignment.Decision.APPROVED
        step_assignment.save(update_fields=["decision"])
        assert document_workflow.is_complete() is True

    def test_false_when_pending_assignment(self, document_workflow, step_assignment):
        assert document_workflow.is_complete() is False

    def test_false_when_no_assignments(self, document_workflow):
        assert document_workflow.is_complete() is False

    def test_false_when_only_rejected(self, document_workflow, step_assignment):
        step_assignment.decision = StepAssignment.Decision.REJECTED
        step_assignment.save(update_fields=["decision"])
        assert document_workflow.is_complete() is False
