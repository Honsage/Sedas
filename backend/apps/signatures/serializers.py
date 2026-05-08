from rest_framework import serializers

from apps.users.serializers import UserSerializer

from .models import Signature


class SignatureSerializer(serializers.ModelSerializer):
    """Сериализатор подписи (на чтение)"""

    signer = UserSerializer(read_only=True)

    class Meta:
        model = Signature
        fields = ["id", "signer", "algorithm", "signature_blob", "signed_at"]
        read_only_fields = fields


class SignatureCreateSerializer(serializers.Serializer):
    """Сериализатор на создание подписи под версией документа"""

    signature_blob = serializers.CharField(
        help_text="Base64-encoded RSA-SHA256 подпись хеша файла (SHA-256 hex to bytes)"
    )
