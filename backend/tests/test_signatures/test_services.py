import pytest

from apps.audit.models import AuditLog
from apps.signatures import services
from apps.signatures.models import Signature


@pytest.mark.django_db
class TestSignDocumentVersion:
    def test_creates_signature(self, document_version, user_signer):
        sig = services.sign_document_version(document_version, user_signer, "dGVzdA==", actor=user_signer)
        assert Signature.objects.filter(id=sig.id).exists()

    def test_stores_correct_blob(self, document_version, user_signer):
        blob = "dGVzdA=="
        sig = services.sign_document_version(document_version, user_signer, blob, actor=user_signer)
        assert sig.signature_blob == blob

    def test_default_algorithm(self, document_version, user_signer):
        sig = services.sign_document_version(document_version, user_signer, "dGVzdA==", actor=user_signer)
        assert sig.algorithm == "RSA-SHA256"

    def test_writes_audit_log(self, document_version, user_signer):
        sig = services.sign_document_version(document_version, user_signer, "dGVzdA==", actor=user_signer)
        assert AuditLog.objects.filter(
            action_type=AuditLog.ActionType.SIGN_DOCUMENT,
            target_id=sig.pk,
        ).exists()


@pytest.mark.django_db
class TestVerifyDocumentSignature:
    def test_valid_signature_returns_true(self, valid_signature):
        assert services.verify_document_signature(valid_signature) is True

    def test_invalid_blob_returns_false(self, document_version, user_signer, public_key_record):
        sig = Signature.objects.create(
            document_version=document_version,
            signer=user_signer,
            signature_blob="aW52YWxpZA==",  # "invalid" в Base64
        )
        assert services.verify_document_signature(sig) is False

    def test_no_public_key_returns_false(self, document_version, user_signer):
        sig = Signature.objects.create(
            document_version=document_version,
            signer=user_signer,
            signature_blob="dGVzdA==",
        )
        assert services.verify_document_signature(sig) is False
