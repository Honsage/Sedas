import hashlib
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.audit.models import AuditLog
from apps.documents import services
from apps.documents.models import Document, DocumentStatus


FILE_CONTENT = b"test file content"
FILE_HASH = hashlib.sha256(FILE_CONTENT).hexdigest()
SAVED_PATH = "documents/1/v1/test.pdf"


def make_file(content=FILE_CONTENT, name="test.pdf"):
    return SimpleUploadedFile(name, content, content_type="application/pdf")


@pytest.mark.django_db
class TestCreateDocument:
    def test_creates_document(self, user_employee):
        with patch("apps.documents.services.default_storage.save", return_value=SAVED_PATH):
            doc = services.create_document("Заголовок", "Описание", make_file(), user_employee)
        assert Document.objects.filter(id=doc.id, title="Заголовок").exists()

    def test_creates_version_1(self, user_employee):
        with patch("apps.documents.services.default_storage.save", return_value=SAVED_PATH):
            doc = services.create_document("Заголовок", "", make_file(), user_employee)
        version = doc.versions.get(version_number=1)
        assert version.author == user_employee

    def test_computes_sha256_hash(self, user_employee):
        with patch("apps.documents.services.default_storage.save", return_value=SAVED_PATH):
            doc = services.create_document("Заголовок", "", make_file(), user_employee)
        version = doc.versions.get(version_number=1)
        assert version.file_hash == FILE_HASH

    def test_status_is_draft(self, user_employee):
        with patch("apps.documents.services.default_storage.save", return_value=SAVED_PATH):
            doc = services.create_document("Заголовок", "", make_file(), user_employee)
        assert doc.status == DocumentStatus.DRAFT

    def test_writes_audit_log(self, user_employee):
        with patch("apps.documents.services.default_storage.save", return_value=SAVED_PATH):
            doc = services.create_document("Заголовок", "", make_file(), user_employee)
        assert AuditLog.objects.filter(
            action_type=AuditLog.ActionType.CREATE_DOCUMENT,
            target_id=doc.pk,
        ).exists()


@pytest.mark.django_db
class TestAddVersion:
    def test_increments_version_number(self, document_draft, user_employee):
        with patch("apps.documents.services.default_storage.save", return_value="documents/1/v2/test.pdf"):
            version = services.add_version(document_draft, make_file(), user_employee)
        assert version.version_number == 2

    def test_computes_hash(self, document_draft, user_employee):
        with patch("apps.documents.services.default_storage.save", return_value="documents/1/v2/test.pdf"):
            version = services.add_version(document_draft, make_file(), user_employee)
        assert version.file_hash == FILE_HASH

    def test_writes_audit_log(self, document_draft, user_employee):
        with patch("apps.documents.services.default_storage.save", return_value="documents/1/v2/test.pdf"):
            version = services.add_version(document_draft, make_file(), user_employee)
        assert AuditLog.objects.filter(
            action_type=AuditLog.ActionType.ADD_VERSION,
            target_id=version.pk,
        ).exists()


@pytest.mark.django_db
class TestUpdateDocument:
    def test_updates_title_and_description(self, document_draft, user_employee):
        doc = services.update_document(document_draft, "Новый заголовок", "Новое описание", user_employee)
        assert doc.title == "Новый заголовок"
        assert doc.description == "Новое описание"

    def test_persists_changes(self, document_draft, user_employee):
        services.update_document(document_draft, "Новый заголовок", "Описание", user_employee)
        document_draft.refresh_from_db()
        assert document_draft.title == "Новый заголовок"

    def test_writes_audit_log(self, document_draft, user_employee):
        services.update_document(document_draft, "Новый заголовок", "", user_employee)
        assert AuditLog.objects.filter(
            action_type=AuditLog.ActionType.UPDATE_DOCUMENT,
            target_id=document_draft.pk,
        ).exists()


@pytest.mark.django_db
class TestSubmitForReview:
    def test_changes_status(self, document_draft, user_employee):
        services.submit_for_review(document_draft, user_employee)
        assert document_draft.status == DocumentStatus.UNDER_REVIEW

    def test_raises_on_wrong_status(self, document_under_review, user_employee):
        with pytest.raises(ValueError):
            services.submit_for_review(document_under_review, user_employee)

    def test_writes_audit_log(self, document_draft, user_employee):
        services.submit_for_review(document_draft, user_employee)
        assert AuditLog.objects.filter(
            action_type=AuditLog.ActionType.SUBMIT_FOR_REVIEW,
            target_id=document_draft.pk,
        ).exists()


@pytest.mark.django_db
class TestArchiveDocument:
    def test_changes_status(self, document_signed, user_employee):
        services.archive_document(document_signed, user_employee)
        assert document_signed.status == DocumentStatus.ARCHIVED

    def test_raises_on_wrong_status(self, document_draft, user_employee):
        with pytest.raises(ValueError):
            services.archive_document(document_draft, user_employee)

    def test_writes_audit_log(self, document_signed, user_employee):
        services.archive_document(document_signed, user_employee)
        assert AuditLog.objects.filter(
            action_type=AuditLog.ActionType.ARCHIVE_DOCUMENT,
            target_id=document_signed.pk,
        ).exists()
