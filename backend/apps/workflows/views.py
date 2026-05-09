from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.models import Document
from apps.documents.permissions import CanAccessDocument
from apps.users.permissions import IsAdministrator, IsEmployee

from . import services
from .models import DocumentWorkflow, StepAssignment, Workflow, WorkflowStep
from .serializers import (
    DecisionSerializer,
    DocumentWorkflowSerializer,
    StartWorkflowSerializer,
    StepAssignmentCreateSerializer,
    StepAssignmentSerializer,
    WorkflowCreateSerializer,
    WorkflowSerializer,
    WorkflowStepCreateSerializer,
    WorkflowStepSerializer,
)

_TAG_WF = ["Маршруты"]
_TAG_WF_STEPS = ["Шаги маршрута"]
_TAG_DOC_WF = ["Процессы согласования"]
_TAG_ASSIGNMENTS = ["Назначения"]

_RESP_400 = openapi.Response("Ошибка валидации / неверный статус", schema=openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={"detail": openapi.Schema(type=openapi.TYPE_STRING)},
))
_RESP_403 = openapi.Response("Доступ запрещён", schema=openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={"detail": openapi.Schema(type=openapi.TYPE_STRING)},
))
_RESP_404 = openapi.Response("Не найдено", schema=openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={"detail": openapi.Schema(type=openapi.TYPE_STRING)},
))
_RESP_204 = openapi.Response("Нет содержимого")


def _check_document_access(request, view, document):
    """Проверяет доступ пользователя к документу и выбрасывает 403 при отказе"""
    permission = CanAccessDocument()
    if not permission.has_object_permission(request, view, document):
        raise PermissionDenied(permission.message)


class WorkflowViewSet(viewsets.ViewSet):
    """Набор представлений для управления шаблонами маршрутов"""

    def get_permissions(self):
        """Запись — только Администратор, чтение — все авторизованные"""
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdministrator()]
        return [IsEmployee()]

    @swagger_auto_schema(
        tags=_TAG_WF,
        operation_summary="Список маршрутов",
        responses={200: WorkflowSerializer(many=True)},
    )
    def list(self, request):
        """Возвращает список всех шаблонов маршрутов"""
        workflows = Workflow.objects.prefetch_related("steps__role").all()
        return Response(WorkflowSerializer(workflows, many=True).data)

    @swagger_auto_schema(
        tags=_TAG_WF,
        operation_summary="Маршрут",
        responses={200: WorkflowSerializer, 404: _RESP_404},
    )
    def retrieve(self, request, pk=None):
        """Возвращает шаблон маршрута с шагами"""
        workflow = get_object_or_404(Workflow, pk=pk)
        return Response(WorkflowSerializer(workflow).data)

    @swagger_auto_schema(
        tags=_TAG_WF,
        operation_summary="Создать маршрут",
        request_body=WorkflowCreateSerializer,
        responses={201: WorkflowSerializer, 400: _RESP_400, 403: _RESP_403},
    )
    def create(self, request):
        """Создаёт новый шаблон маршрута"""
        serializer = WorkflowCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        workflow = serializer.save()
        return Response(WorkflowSerializer(workflow).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        tags=_TAG_WF,
        operation_summary="Обновить маршрут",
        request_body=WorkflowCreateSerializer,
        responses={200: WorkflowSerializer, 400: _RESP_400, 403: _RESP_403, 404: _RESP_404},
    )
    def update(self, request, pk=None):
        """Обновляет шаблон маршрута"""
        workflow = get_object_or_404(Workflow, pk=pk)
        serializer = WorkflowCreateSerializer(workflow, data=request.data)
        serializer.is_valid(raise_exception=True)
        workflow = serializer.save()
        return Response(WorkflowSerializer(workflow).data)

    @swagger_auto_schema(
        tags=_TAG_WF,
        operation_summary="Частично обновить маршрут",
        request_body=WorkflowCreateSerializer,
        responses={200: WorkflowSerializer, 400: _RESP_400, 403: _RESP_403, 404: _RESP_404},
    )
    def partial_update(self, request, pk=None):
        """Частично обновляет шаблон маршрута"""
        workflow = get_object_or_404(Workflow, pk=pk)
        serializer = WorkflowCreateSerializer(workflow, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        workflow = serializer.save()
        return Response(WorkflowSerializer(workflow).data)

    @swagger_auto_schema(
        tags=_TAG_WF,
        operation_summary="Удалить маршрут",
        responses={204: _RESP_204, 403: _RESP_403, 404: _RESP_404},
    )
    def destroy(self, request, pk=None):
        """Удаляет шаблон маршрута"""
        workflow = get_object_or_404(Workflow, pk=pk)
        workflow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkflowStepListView(APIView):
    """Представление для просмотра и добавления шагов маршрута"""

    def get_permissions(self):
        """Запись — только Администратор, чтение — все авторизованные"""
        if self.request.method == "POST":
            return [IsAdministrator()]
        return [IsEmployee()]

    @swagger_auto_schema(
        tags=_TAG_WF_STEPS,
        operation_summary="Список шагов маршрута",
        responses={200: WorkflowStepSerializer(many=True), 404: _RESP_404},
    )
    def get(self, request, workflow_pk):
        """Возвращает список шагов маршрута"""
        workflow = get_object_or_404(Workflow, pk=workflow_pk)
        steps = workflow.steps.select_related("role").all()
        return Response(WorkflowStepSerializer(steps, many=True).data)

    @swagger_auto_schema(
        tags=_TAG_WF_STEPS,
        operation_summary="Добавить шаг к маршруту",
        operation_description="Добавляет шаг с указанным порядковым номером и ролью. step_order должен быть уникальным",
        request_body=WorkflowStepCreateSerializer,
        responses={201: WorkflowStepSerializer, 400: _RESP_400, 403: _RESP_403, 404: _RESP_404},
    )
    def post(self, request, workflow_pk):
        """Добавляет шаг к маршруту"""
        workflow = get_object_or_404(Workflow, pk=workflow_pk)
        serializer = WorkflowStepCreateSerializer(
            data=request.data,
            context={"workflow": workflow},
        )
        serializer.is_valid(raise_exception=True)
        step = serializer.save(workflow=workflow)
        return Response(WorkflowStepSerializer(step).data, status=status.HTTP_201_CREATED)


class WorkflowStepDetailView(APIView):
    """Представление для удаления шага маршрута"""

    permission_classes = [IsAdministrator]

    @swagger_auto_schema(
        tags=_TAG_WF_STEPS,
        operation_summary="Удалить шаг маршрута",
        responses={204: _RESP_204, 403: _RESP_403, 404: _RESP_404},
    )
    def delete(self, request, workflow_pk, step_pk):
        """Удаляет шаг из маршрута"""
        workflow = get_object_or_404(Workflow, pk=workflow_pk)
        step = get_object_or_404(WorkflowStep, pk=step_pk, workflow=workflow)
        step.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentWorkflowListView(APIView):
    """Представление для просмотра процессов согласования по документу"""

    permission_classes = [IsEmployee]

    @swagger_auto_schema(
        tags=_TAG_DOC_WF,
        operation_summary="Процессы согласования документа",
        operation_description="Возвращает все запущенные маршруты по документу с текущим шагом и назначениями",
        responses={200: DocumentWorkflowSerializer(many=True), 403: _RESP_403, 404: _RESP_404},
    )
    def get(self, request, document_pk):
        """Возвращает список процессов согласования по документу"""
        document = get_object_or_404(Document, pk=document_pk)
        _check_document_access(request, self, document)
        document_workflows = (
            DocumentWorkflow.objects
            .filter(document=document)
            .prefetch_related("assignments__workflow_step__role", "assignments__assigned_user", "workflow__steps__role")
        )
        return Response(DocumentWorkflowSerializer(document_workflows, many=True).data)


class StartWorkflowView(APIView):
    """Представление для запуска маршрута согласования на документе"""

    permission_classes = [IsEmployee]

    @swagger_auto_schema(
        tags=_TAG_DOC_WF,
        operation_summary="Запустить маршрут на документе",
        operation_description="Создаёт экземпляр процесса. Документ должен быть в статусе `under_review`",
        request_body=StartWorkflowSerializer,
        responses={201: DocumentWorkflowSerializer, 400: _RESP_400, 403: _RESP_403, 404: _RESP_404},
    )
    def post(self, request, document_pk):
        """Запускает маршрут согласования для документа"""
        document = get_object_or_404(Document, pk=document_pk)
        _check_document_access(request, self, document)

        serializer = StartWorkflowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        workflow = get_object_or_404(Workflow, pk=serializer.validated_data["workflow_id"])

        try:
            document_workflow = services.start_workflow(
                document=document,
                workflow=workflow,
                actor=request.user,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            DocumentWorkflowSerializer(document_workflow).data,
            status=status.HTTP_201_CREATED,
        )


class StepAssignmentListView(APIView):
    """Представление для просмотра и создания назначений в рамках процесса"""

    permission_classes = [IsEmployee]

    @swagger_auto_schema(
        tags=_TAG_ASSIGNMENTS,
        operation_summary="Назначения в процессе согласования",
        responses={200: StepAssignmentSerializer(many=True), 403: _RESP_403, 404: _RESP_404},
    )
    def get(self, request, document_workflow_pk):
        """Возвращает список назначений процесса согласования"""
        document_workflow = get_object_or_404(DocumentWorkflow, pk=document_workflow_pk)
        _check_document_access(request, self, document_workflow.document)
        assignments = document_workflow.assignments.select_related(
            "workflow_step__role", "assigned_user"
        ).all()
        return Response(StepAssignmentSerializer(assignments, many=True).data)

    @swagger_auto_schema(
        tags=_TAG_ASSIGNMENTS,
        operation_summary="Назначить пользователя на шаг",
        operation_description="Шаг должен принадлежать маршруту данного процесса",
        request_body=StepAssignmentCreateSerializer,
        responses={201: StepAssignmentSerializer, 400: _RESP_400, 403: _RESP_403, 404: _RESP_404},
    )
    def post(self, request, document_workflow_pk):
        """Назначает пользователя на шаг процесса согласования"""
        document_workflow = get_object_or_404(DocumentWorkflow, pk=document_workflow_pk)
        _check_document_access(request, self, document_workflow.document)

        serializer = StepAssignmentCreateSerializer(
            data=request.data,
            context={"document_workflow": document_workflow},
        )
        serializer.is_valid(raise_exception=True)

        assignment = services.assign_user_to_step(
            document_workflow=document_workflow,
            workflow_step=serializer.validated_data["workflow_step"],
            user=serializer.validated_data["assigned_user"],
            actor=request.user,
        )

        return Response(StepAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)


class StepDecisionView(APIView):
    """Представление для вынесения решения по назначению"""

    permission_classes = [IsEmployee]

    @swagger_auto_schema(
        tags=_TAG_ASSIGNMENTS,
        operation_summary="Вынести решение по шагу",
        operation_description=(
            "Допустимые значения `decision`: `approved`, `rejected`, `revision`\n\n"
            "- `approved` — шаг одобрен; если последний — документ переходит в `signed`\n"
            "- `revision` — документ возвращается в `draft`\n"
            "- `rejected` — шаг отклонён, статус документа не меняется"
        ),
        request_body=DecisionSerializer,
        responses={200: StepAssignmentSerializer, 400: _RESP_400, 403: _RESP_403, 404: _RESP_404},
    )
    def post(self, request, assignment_pk):
        """Фиксирует решение назначенного пользователя по шагу согласования"""
        assignment = get_object_or_404(StepAssignment, pk=assignment_pk)

        if assignment.assigned_user != request.user:
            return Response(
                {"detail": "Вынести решение может только назначенный пользователь"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            assignment = services.make_decision(
                assignment=assignment,
                decision=serializer.validated_data["decision"],
                actor=request.user,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(StepAssignmentSerializer(assignment).data)
