from rest_framework import serializers

from .models import Document, DocumentVersion


class DocumentVersionSerializer(serializers.ModelSerializer):
    """Сериализатор версии документа (на чтение)"""

    author_name = serializers.CharField(source="author.get_full_name", read_only=True)

    class Meta:
        model = DocumentVersion
        fields = [
            "id",
            "version_number",
            "file_path",
            "file_hash",
            "author_name",
            "created_at",
        ]
        read_only_fields = fields


class DocumentSerializer(serializers.ModelSerializer):
    """Сериализатор документа (на чтение)"""

    versions = DocumentVersionSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "description",
            "status",
            "created_at",
            "versions",
        ]
        read_only_fields = fields


class DocumentCreateSerializer(serializers.Serializer):
    """Сериализатор на создание нового документа с первой версией"""

    title = serializers.CharField(max_length=500)
    description = serializers.CharField(required=False, default="", allow_blank=True)
    file = serializers.FileField()


class DocumentUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор на обновление метаданных документа"""

    class Meta:
        model = Document
        fields = ["title", "description"]


class DocumentVersionCreateSerializer(serializers.Serializer):
    """Сериализатор на загрузку новой версии документа"""

    file = serializers.FileField()
