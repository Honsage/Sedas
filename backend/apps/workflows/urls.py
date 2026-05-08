from django.urls import path

from .views import (
    DocumentWorkflowListView,
    StartWorkflowView,
    StepAssignmentListView,
    StepDecisionView,
    WorkflowStepDetailView,
    WorkflowStepListView,
    WorkflowViewSet,
)

urlpatterns = [
    # Шаблоны маршрутов
    path(
        "workflows/",
        WorkflowViewSet.as_view({"get": "list", "post": "create"}),
        name="workflow-list",
    ),
    path(
        "workflows/<int:pk>/",
        WorkflowViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="workflow-detail",
    ),

    # Шаги маршрута
    path(
        "workflows/<int:workflow_pk>/steps/",
        WorkflowStepListView.as_view(),
        name="workflow-step-list",
    ),
    path(
        "workflows/<int:workflow_pk>/steps/<int:step_pk>/",
        WorkflowStepDetailView.as_view(),
        name="workflow-step-detail",
    ),

    # Процессы согласования по документу
    path(
        "documents/<int:document_pk>/document-workflows/",
        DocumentWorkflowListView.as_view(),
        name="document-workflow-list",
    ),
    path(
        "documents/<int:document_pk>/start-workflow/",
        StartWorkflowView.as_view(),
        name="document-start-workflow",
    ),

    # Назначения внутри процесса
    path(
        "document-workflows/<int:document_workflow_pk>/assignments/",
        StepAssignmentListView.as_view(),
        name="step-assignment-list",
    ),

    # Решение по назначению
    path(
        "assignments/<int:assignment_pk>/decide/",
        StepDecisionView.as_view(),
        name="step-decision",
    ),
]
