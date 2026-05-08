from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.models import Document, DocumentVersion
from apps.documents.permissions import CanAccessDocument
from apps.users.permissions import IsEmployee, IsSigner
from rest_framework.exceptions import PermissionDenied

from . import services
from .models import Signature
from .serializers import SignatureCreateSerializer, SignatureSerializer


def _check_document_access(request, view, document):
    """Проверяет доступ пользователя к документу и выбрасывает 403 при отказе"""
    permission = CanAccessDocument()
    if not permission.has_object_permission(request, view, document):
        raise PermissionDenied(permission.message)


class DocumentVersionSignatureListView(APIView):
    """Представление для просмотра и создания подписей под версией документа"""

    def get_permissions(self):
        """Создание подписи — только Подписант, просмотр — все авторизованные"""
        if self.request.method == "POST":
            return [IsSigner()]
        return [IsEmployee()]

    def get(self, request, document_pk, version_pk):
        """Возвращает список подписей под версией документа"""
        document = get_object_or_404(Document, pk=document_pk)
        _check_document_access(request, self, document)

        version = get_object_or_404(DocumentVersion, pk=version_pk, document=document)
        signatures = version.signatures.select_related("signer").all()
        return Response(SignatureSerializer(signatures, many=True).data)

    def post(self, request, document_pk, version_pk):
        """Создаёт подпись RSA-SHA256 под версией документа"""
        document = get_object_or_404(Document, pk=document_pk)
        _check_document_access(request, self, document)

        version = get_object_or_404(DocumentVersion, pk=version_pk, document=document)

        serializer = SignatureCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        signature = services.sign_document_version(
            document_version=version,
            signer=request.user,
            signature_blob=serializer.validated_data["signature_blob"],
            actor=request.user,
        )

        return Response(SignatureSerializer(signature).data, status=status.HTTP_201_CREATED)


class SignatureVerifyView(APIView):
    """Представление для верификации подписи"""

    permission_classes = [IsEmployee]

    def post(self, request, signature_pk):
        """Верифицирует подпись через публичный ключ подписанта"""
        signature = get_object_or_404(Signature, pk=signature_pk)
        _check_document_access(request, self, signature.document_version.document)

        is_valid = services.verify_document_signature(signature)
        return Response({"is_valid": is_valid})
