from django.conf import settings
from django.db import models


class Signature(models.Model):
    """Криптографическая подпись (RSA-SHA256) под конкретной версией документа"""

    document_version = models.ForeignKey(
        "documents.DocumentVersion",
        on_delete=models.CASCADE,
        related_name="signatures",
    )
    signer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="signatures",
    )
    # Base64-encoded signature bytes
    signature_blob = models.TextField()
    algorithm = models.CharField(max_length=50, default="RSA-SHA256")
    signed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "signatures_signature"
        verbose_name = "Подпись"
        verbose_name_plural = "Подписи"

    def __str__(self):
        return f"Подпись #{self.pk}: {self.signer} на {self.document_version}"
