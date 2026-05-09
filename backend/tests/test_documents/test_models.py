import pytest

from apps.documents.models import Document, DocumentStatus


@pytest.mark.django_db
class TestDocumentLifecycle:
    def test_submit_for_review_from_draft(self, document_draft):
        document_draft.submit_for_review()
        assert document_draft.status == DocumentStatus.UNDER_REVIEW

    def test_submit_for_review_persists(self, document_draft):
        document_draft.submit_for_review()
        document_draft.refresh_from_db()
        assert document_draft.status == DocumentStatus.UNDER_REVIEW

    def test_submit_for_review_raises_when_not_draft(self, document_under_review):
        with pytest.raises(ValueError):
            document_under_review.submit_for_review()

    def test_approve_from_under_review(self, document_under_review):
        document_under_review.approve()
        assert document_under_review.status == DocumentStatus.SIGNED

    def test_approve_persists(self, document_under_review):
        document_under_review.approve()
        document_under_review.refresh_from_db()
        assert document_under_review.status == DocumentStatus.SIGNED

    def test_approve_raises_when_not_under_review(self, document_draft):
        with pytest.raises(ValueError):
            document_draft.approve()

    def test_return_for_revision_from_under_review(self, document_under_review):
        document_under_review.return_for_revision()
        assert document_under_review.status == DocumentStatus.DRAFT

    def test_return_for_revision_persists(self, document_under_review):
        document_under_review.return_for_revision()
        document_under_review.refresh_from_db()
        assert document_under_review.status == DocumentStatus.DRAFT

    def test_return_for_revision_raises_when_not_under_review(self, document_draft):
        with pytest.raises(ValueError):
            document_draft.return_for_revision()

    def test_archive_from_signed(self, document_signed):
        document_signed.archive()
        assert document_signed.status == DocumentStatus.ARCHIVED

    def test_archive_persists(self, document_signed):
        document_signed.archive()
        document_signed.refresh_from_db()
        assert document_signed.status == DocumentStatus.ARCHIVED

    def test_archive_raises_when_not_signed(self, document_draft):
        with pytest.raises(ValueError):
            document_draft.archive()

    def test_archive_raises_when_under_review(self, document_under_review):
        with pytest.raises(ValueError):
            document_under_review.archive()
