from django.urls import path

from .views import (
    DocumentArchiveView,
    DocumentSubmitForReviewView,
    DocumentUpdateView,
    DocumentVersionViewSet,
    DocumentViewSet,
)

urlpatterns = [
    # Документы
    path(
        "documents/",
        DocumentViewSet.as_view({"get": "list", "post": "create"}),
        name="document-list",
    ),
    path(
        "documents/<int:pk>/",
        DocumentViewSet.as_view({"get": "retrieve"}),
        name="document-detail",
    ),
    path(
        "documents/<int:pk>/update/",
        DocumentUpdateView.as_view(),
        name="document-update",
    ),

    # Жизненный цикл
    path(
        "documents/<int:pk>/submit-for-review/",
        DocumentSubmitForReviewView.as_view(),
        name="document-submit-for-review",
    ),
    path(
        "documents/<int:pk>/archive/",
        DocumentArchiveView.as_view(),
        name="document-archive",
    ),

    # Версии документа
    path(
        "documents/<int:document_pk>/versions/",
        DocumentVersionViewSet.as_view({"get": "list", "post": "create"}),
        name="document-version-list",
    ),
]
