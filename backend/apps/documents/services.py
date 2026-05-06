import hashlib

from django.core.files.storage import default_storage

from apps.audit.models import AuditLog

from .models import Document, DocumentVersion


def _compute_sha256(file) -> str:
    """Вычисляет SHA-256 хеш файла и возвращает hex-строку"""
    sha256 = hashlib.sha256()
    for chunk in file.chunks():
        sha256.update(chunk)
    return sha256.hexdigest()


def _save_file(file, document_id: int, version_number: int) -> str:
    """Сохраняет файл в хранилище и возвращает относительный путь"""
    relative_path = f"documents/{document_id}/v{version_number}/{file.name}"
    saved_path = default_storage.save(relative_path, file)
    return saved_path


def create_document(title: str, description: str, file, author) -> Document:
    """Создаёт документ с первой версией, вычисляет хеш файла, записывает в аудит"""
    document = Document.objects.create(title=title, description=description)

    file_hash = _compute_sha256(file)
    file.seek(0)
    file_path = _save_file(file, document.id, version_number=1)

    DocumentVersion.objects.create(
        document=document,
        version_number=1,
        file_path=file_path,
        file_hash=file_hash,
        author=author,
    )

    AuditLog.objects.create(
        user=author,
        action_type=AuditLog.ActionType.CREATE_DOCUMENT,
        target_type=AuditLog.TargetType.DOCUMENT,
        target_id=document.pk,
    )

    return document


def add_version(document: Document, file, author) -> DocumentVersion:
    """Добавляет новую версию к существующему документу, записывает в аудит"""
    next_number = document.versions.count() + 1

    file_hash = _compute_sha256(file)
    file.seek(0)
    file_path = _save_file(file, document.id, version_number=next_number)

    version = DocumentVersion.objects.create(
        document=document,
        version_number=next_number,
        file_path=file_path,
        file_hash=file_hash,
        author=author,
    )

    AuditLog.objects.create(
        user=author,
        action_type=AuditLog.ActionType.ADD_VERSION,
        target_type=AuditLog.TargetType.DOCUMENT_VERSION,
        target_id=version.pk,
    )

    return version


def update_document(document: Document, title: str, description: str, actor) -> Document:
    """Обновляет метаданные черновика документа, записывает в аудит"""
    document.title = title
    document.description = description
    document.save(update_fields=["title", "description"])

    AuditLog.objects.create(
        user=actor,
        action_type=AuditLog.ActionType.UPDATE_DOCUMENT,
        target_type=AuditLog.TargetType.DOCUMENT,
        target_id=document.pk,
    )

    return document


def submit_for_review(document: Document, actor) -> Document:
    """Переводит документ в статус 'На согласовании', записывает в аудит"""
    document.submit_for_review()

    AuditLog.objects.create(
        user=actor,
        action_type=AuditLog.ActionType.SUBMIT_FOR_REVIEW,
        target_type=AuditLog.TargetType.DOCUMENT,
        target_id=document.pk,
    )

    return document


def archive_document(document: Document, actor) -> Document:
    """Архивирует подписанный документ, записывает в аудит"""
    document.archive()

    AuditLog.objects.create(
        user=actor,
        action_type=AuditLog.ActionType.ARCHIVE_DOCUMENT,
        target_type=AuditLog.TargetType.DOCUMENT,
        target_id=document.pk,
    )

    return document
