from django.urls import path

from .views import DocumentVersionSignatureListView, SignatureVerifyView

urlpatterns = [
    # Подписи под версией документа
    path(
        "documents/<int:document_pk>/versions/<int:version_pk>/signatures/",
        DocumentVersionSignatureListView.as_view(),
        name="signature-list",
    ),

    # Верификация подписи
    path(
        "signatures/<int:signature_pk>/verify/",
        SignatureVerifyView.as_view(),
        name="signature-verify",
    ),
]
