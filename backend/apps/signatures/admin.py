from django.contrib import admin

from .models import Signature


@admin.register(Signature)
class SignatureAdmin(admin.ModelAdmin):
    list_display = ("signer", "document_version", "algorithm", "signed_at")
    list_filter = ("algorithm",)
    readonly_fields = ("signature_blob", "signed_at")
