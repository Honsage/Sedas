from django.contrib import admin

from .models import DocumentWorkflow, StepAssignment, Workflow, WorkflowStep


class WorkflowStepInline(admin.TabularInline):
    model = WorkflowStep
    extra = 1


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)
    inlines = [WorkflowStepInline]


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = ("workflow", "step_order", "role")
    list_filter = ("workflow", "role")


class StepAssignmentInline(admin.TabularInline):
    model = StepAssignment
    extra = 0
    readonly_fields = ("assigned_at", "decided_at")


@admin.register(DocumentWorkflow)
class DocumentWorkflowAdmin(admin.ModelAdmin):
    list_display = ("document", "workflow")
    inlines = [StepAssignmentInline]


@admin.register(StepAssignment)
class StepAssignmentAdmin(admin.ModelAdmin):
    list_display = ("document_workflow", "workflow_step", "assigned_user", "decision", "decided_at")
    list_filter = ("decision",)
    readonly_fields = ("assigned_at", "decided_at")
