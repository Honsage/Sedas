from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.models import Document, DocumentVersion
from apps.documents.permissions import CanAccessDocument
from apps.users.permissions import IsEmployee, IsSigner

from . import services
from .models import Signature
from .serializers import SignatureCreateSerializer, SignatureSerializer

_TAG_SIGS = ["Подписи"]

_RESP_400 = openapi.Response("Ошибка валидации", schema=openapi.Schema(
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

_VERIFY_RESPONSE = openapi.Response(
    "Результат верификации",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={"is_valid": openapi.Schema(type=openapi.TYPE_BOOLEAN)},
    ),
)


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

    @swagger_auto_schema(
        tags=_TAG_SIGS,
        operation_summary="Список подписей версии документа",
        responses={200: SignatureSerializer(many=True), 403: _RESP_403, 404: _RESP_404},
    )
    def get(self, request, document_pk, version_pk):
        """Возвращает список подписей под версией документа"""
        document = get_object_or_404(Document, pk=document_pk)
        _check_document_access(request, self, document)

        version = get_object_or_404(DocumentVersion, pk=version_pk, document=document)
        signatures = version.signatures.select_related("signer").all()
        return Response(SignatureSerializer(signatures, many=True).data)

    @swagger_auto_schema(
        tags=_TAG_SIGS,
        operation_summary="Подписать версию документа",
        operation_description=(
            "Сохраняет RSA-SHA256 подпись под версией документа.\n\n"
            "Клиент подписывает `bytes.fromhex(file_hash)` своим приватным ключом "
            "(PKCS1v15, SHA-256) и передаёт результат в Base64.\n\n"
            "Требуется роль **Подписант** и зарегистрированный публичный ключ"
        ),
        request_body=SignatureCreateSerializer,
        responses={201: SignatureSerializer, 400: _RESP_400, 403: _RESP_403, 404: _RESP_404},
    )
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

    @swagger_auto_schema(
        tags=_TAG_SIGS,
        operation_summary="Верифицировать подпись",
        operation_description=(
            "Проверяет подпись через последний публичный ключ подписанта.\n\n"
            "Возвращает `{\"is_valid\": true}` если подпись корректна, иначе `false`"
        ),
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT),
        responses={200: _VERIFY_RESPONSE, 403: _RESP_403, 404: _RESP_404},
    )
    def post(self, request, signature_pk):
        """Верифицирует подпись через публичный ключ подписанта"""
        signature = get_object_or_404(Signature, pk=signature_pk)
        _check_document_access(request, self, signature.document_version.document)

        is_valid = services.verify_document_signature(signature)
        return Response({"is_valid": is_valid})
