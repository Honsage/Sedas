from django.contrib import admin

from .models import Document, DocumentVersion


class DocumentVersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0
    readonly_fields = ("version_number", "file_hash", "author", "created_at")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("title",)
    readonly_fields = ("created_at",)
    inlines = [DocumentVersionInline]


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ("document", "version_number", "author", "created_at")
    readonly_fields = ("file_hash", "created_at")
