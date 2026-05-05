from django.conf import settings
from django.db import models


class DocumentStatus(models.TextChoices):
    DRAFT = "draft", "Черновик"
    UNDER_REVIEW = "under_review", "На согласовании"
    SIGNED = "signed", "Подписан"
    ARCHIVED = "archived", "Архив"


class Document(models.Model):
    """Метаданные документа"""

    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=DocumentStatus.choices,
        default=DocumentStatus.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "documents_document"
        verbose_name = "Документ"
        verbose_name_plural = "Документы"

    def __str__(self):
        return f"[{self.status}] {self.title}"

    def submit_for_review(self):
        """Отправляет документ на согласование"""
        if self.status != DocumentStatus.DRAFT:
            raise ValueError("На согласование можно отправить только черновик")
        self.status = DocumentStatus.UNDER_REVIEW
        self.save(update_fields=["status"])

    def approve(self):
        """Подписывает документ"""
        if self.status != DocumentStatus.UNDER_REVIEW:
            raise ValueError("Документ не находится на согласовании")
        self.status = DocumentStatus.SIGNED
        self.save(update_fields=["status"])

    def return_for_revision(self):
        """Возвращает документ на доработку"""
        if self.status != DocumentStatus.UNDER_REVIEW:
            raise ValueError("Документ не находится на согласовании")
        self.status = DocumentStatus.DRAFT
        self.save(update_fields=["status"])

    def archive(self):
        """Архивирует документ"""
        if self.status != DocumentStatus.SIGNED:
            raise ValueError("Архивировать можно только подписанный документ")
        self.status = DocumentStatus.ARCHIVED
        self.save(update_fields=["status"])


class DocumentVersion(models.Model):
    """Версия документа, привязанная к конкретному файлу"""

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField()
    file_path = models.CharField(max_length=1000)
    # SHA-256 hex
    file_hash = models.CharField(max_length=64)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="document_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "documents_version"
        verbose_name = "Версия документа"
        verbose_name_plural = "Версии документов"
        unique_together = [("document", "version_number")]
        ordering = ["version_number"]

    def __str__(self):
        return f"{self.document.title} v{self.version_number}"
