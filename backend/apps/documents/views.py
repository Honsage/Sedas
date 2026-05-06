from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsEmployee
from apps.workflows.models import StepAssignment

from . import services
from .models import Document, DocumentVersion
from .permissions import CanAccessDocument
from .serializers import (
    DocumentCreateSerializer,
    DocumentSerializer,
    DocumentUpdateSerializer,
    DocumentVersionCreateSerializer,
    DocumentVersionSerializer,
)


def _get_user_documents_queryset(user):
    """Возвращает queryset документов, доступных пользователю"""
    authored_document_ids = DocumentVersion.objects.filter(
        author=user,
    ).values_list("document_id", flat=True)

    assigned_document_ids = StepAssignment.objects.filter(
        assigned_user=user,
    ).values_list("document_workflow__document_id", flat=True)

    accessible_ids = set(authored_document_ids) | set(assigned_document_ids)

    return Document.objects.filter(id__in=accessible_ids).prefetch_related("versions")


def _check_document_access(request, view, document):
    """Проверяет доступ пользователя к документу и выбрасывает 403 при отказе"""
    permission = CanAccessDocument()
    if not permission.has_object_permission(request, view, document):
        raise PermissionDenied(permission.message)


class DocumentViewSet(viewsets.ViewSet):
    """Набор представлений для просмотра и создания документов"""

    permission_classes = [IsEmployee]

    def list(self, request):
        """Возвращает список документов, доступных текущему пользователю"""
        queryset = _get_user_documents_queryset(request.user)
        serializer = DocumentSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Возвращает детальную информацию о документе"""
        document = get_object_or_404(Document, pk=pk)
        _check_document_access(request, self, document)
        serializer = DocumentSerializer(document)
        return Response(serializer.data)

    def create(self, request):
        """Создаёт новый документ с первой версией"""
        serializer = DocumentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        document = services.create_document(
            title=data["title"],
            description=data.get("description", ""),
            file=data["file"],
            author=request.user,
        )

        return Response(DocumentSerializer(document).data, status=status.HTTP_201_CREATED)


class DocumentUpdateView(APIView):
    """Представление для обновления метаданных черновика документа"""

    permission_classes = [IsEmployee]

    def patch(self, request, pk):
        """Обновляет title и description черновика документа"""
        document = get_object_or_404(Document, pk=pk)
        _check_document_access(request, self, document)

        serializer = DocumentUpdateSerializer(document, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        document = services.update_document(
            document=document,
            title=data.get("title", document.title),
            description=data.get("description", document.description),
            actor=request.user,
        )

        return Response(DocumentSerializer(document).data)


class DocumentVersionViewSet(viewsets.ViewSet):
    """Набор представлений для работы с версиями документа"""

    permission_classes = [IsEmployee]

    def list(self, request, document_pk=None):
        """Возвращает все версии указанного документа"""
        document = get_object_or_404(Document, pk=document_pk)
        _check_document_access(request, self, document)

        versions = document.versions.all()
        serializer = DocumentVersionSerializer(versions, many=True)
        return Response(serializer.data)

    def create(self, request, document_pk=None):
        """Добавляет новую версию к существующему документу"""
        document = get_object_or_404(Document, pk=document_pk)
        _check_document_access(request, self, document)

        serializer = DocumentVersionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        version = services.add_version(
            document=document,
            file=serializer.validated_data["file"],
            author=request.user,
        )

        return Response(DocumentVersionSerializer(version).data, status=status.HTTP_201_CREATED)


class DocumentSubmitForReviewView(APIView):
    """Представление для отправки документа на согласование"""

    permission_classes = [IsEmployee]

    def post(self, request, pk):
        """Переводит документ из статуса 'Черновик' в 'На согласовании'"""
        document = get_object_or_404(Document, pk=pk)
        _check_document_access(request, self, document)

        try:
            services.submit_for_review(document=document, actor=request.user)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(DocumentSerializer(document).data)


class DocumentArchiveView(APIView):
    """Представление для архивации подписанного документа"""

    permission_classes = [IsEmployee]

    def post(self, request, pk):
        """Переводит документ из статуса 'Подписан' в 'Архив'"""
        document = get_object_or_404(Document, pk=pk)
        _check_document_access(request, self, document)

        try:
            services.archive_document(document=document, actor=request.user)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(DocumentSerializer(document).data)
