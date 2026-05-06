from rest_framework.permissions import BasePermission

from apps.workflows.models import StepAssignment

from .models import DocumentVersion


class CanAccessDocument(BasePermission):
    """Разрешение на уровне объекта — доступ к конкретному документу"""

    message = "У вас нет доступа к этому документу"

    def has_object_permission(self, request, view, obj):
        """
        Разрешает доступ, если пользователь является автором любой версии документа
        или назначен на шаг согласования по этому документу
        """
        user = request.user

        is_version_author = DocumentVersion.objects.filter(
            document=obj,
            author=user,
        ).exists()

        if is_version_author:
            return True

        is_assigned = StepAssignment.objects.filter(
            document_workflow__document=obj,
            assigned_user=user,
        ).exists()

        return is_assigned
