from apps.audit.models import AuditLog
from apps.documents.models import DocumentVersion
from apps.users.models import User
from infrastructure.crypto import verify_signature as crypto_verify

from .models import Signature


def sign_document_version(
    document_version: DocumentVersion,
    signer: User,
    signature_blob: str,
    actor: User,
) -> Signature:
    """Сохраняет подпись под версией документа, записывает в аудит"""
    signature = Signature.objects.create(
        document_version=document_version,
        signer=signer,
        signature_blob=signature_blob,
    )

    AuditLog.objects.create(
        user=actor,
        action_type=AuditLog.ActionType.SIGN_DOCUMENT,
        target_type=AuditLog.TargetType.SIGNATURE,
        target_id=signature.pk,
    )

    return signature


def verify_document_signature(signature: Signature) -> bool:
    """Верифицирует подпись через публичный ключ подписанта"""
    public_key = signature.signer.public_keys.order_by("-created_at").first()
    if public_key is None:
        return False

    return crypto_verify(
        public_key_pem=public_key.public_key,
        file_hash_hex=signature.document_version.file_hash,
        signature_b64=signature.signature_blob,
    )
