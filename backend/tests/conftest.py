import base64
import hashlib

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.documents.models import Document, DocumentStatus, DocumentVersion
from apps.signatures.models import Signature
from apps.users.models import PublicKey, Role, User, UserRole
from apps.workflows.models import DocumentWorkflow, StepAssignment, Workflow, WorkflowStep


# Roles

@pytest.fixture
def role_admin(db):
    return Role.objects.create(name=Role.ADMINISTRATOR, description="Администратор")


@pytest.fixture
def role_employee(db):
    return Role.objects.create(name=Role.EMPLOYEE, description="Сотрудник")


@pytest.fixture
def role_signer(db):
    return Role.objects.create(name=Role.SIGNER, description="Подписант")


# Users

def make_user(email, role=None, **kwargs):
    """Вспомогательная функция создания пользователя с опциональной ролью"""
    defaults = {"surname": "Тестовый", "name": "Пользователь", "patronymic": "Тест"}
    defaults.update(kwargs)
    user = User.objects.create_user(email=email, password="password123", **defaults)
    if role:
        UserRole.objects.create(user=user, role=role)
    return user


@pytest.fixture
def user_admin(db, role_admin):
    return make_user("admin@test.com", role=role_admin)


@pytest.fixture
def user_employee(db, role_employee):
    return make_user("employee@test.com", role=role_employee)


@pytest.fixture
def user_signer(db, role_signer):
    return make_user("signer@test.com", role=role_signer)


@pytest.fixture
def user_plain(db):
    """Пользователь без ролей"""
    return make_user("plain@test.com")


# Documents

@pytest.fixture
def document_draft(db, user_employee):
    doc = Document.objects.create(title="Тестовый документ", description="Описание")
    DocumentVersion.objects.create(
        document=doc,
        version_number=1,
        file_path="documents/1/v1/test.pdf",
        file_hash=hashlib.sha256(b"test content").hexdigest(),
        author=user_employee,
    )
    return doc


@pytest.fixture
def document_under_review(db, document_draft):
    document_draft.status = DocumentStatus.UNDER_REVIEW
    document_draft.save(update_fields=["status"])
    return document_draft


@pytest.fixture
def document_signed(db, document_draft):
    document_draft.status = DocumentStatus.SIGNED
    document_draft.save(update_fields=["status"])
    return document_draft


@pytest.fixture
def document_version(db, document_draft):
    return document_draft.versions.first()


@pytest.fixture
def uploaded_file():
    """Фиктивный загружаемый файл"""
    return SimpleUploadedFile("test.pdf", b"test file content", content_type="application/pdf")


# Workflows

@pytest.fixture
def workflow(db, role_employee):
    wf = Workflow.objects.create(name="Стандартный маршрут", description="")
    WorkflowStep.objects.create(workflow=wf, step_order=1, role=role_employee)
    return wf


@pytest.fixture
def workflow_two_steps(db, role_employee, role_signer):
    wf = Workflow.objects.create(name="Двухшаговый маршрут", description="")
    WorkflowStep.objects.create(workflow=wf, step_order=1, role=role_employee)
    WorkflowStep.objects.create(workflow=wf, step_order=2, role=role_signer)
    return wf


@pytest.fixture
def document_workflow(db, document_under_review, workflow):
    return DocumentWorkflow.objects.create(
        document=document_under_review,
        workflow=workflow,
    )


@pytest.fixture
def step_assignment(db, document_workflow, user_employee):
    step = document_workflow.workflow.steps.first()
    return StepAssignment.objects.create(
        document_workflow=document_workflow,
        workflow_step=step,
        assigned_user=user_employee,
    )


# Crypto helpers

@pytest.fixture(scope="session")
def rsa_key_pair():
    """Генерирует RSA-2048 пару ключей один раз на сессию"""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_key, public_key_pem


def make_signature_blob(private_key, file_hash_hex: str) -> str:
    """Подписывает хеш файла и возвращает Base64-строку"""
    data = bytes.fromhex(file_hash_hex)
    sig_bytes = private_key.sign(data, padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(sig_bytes).decode()


@pytest.fixture
def public_key_record(db, user_signer, rsa_key_pair):
    """Сохранённый PublicKey для user_signer"""
    _, public_key_pem = rsa_key_pair
    return PublicKey.objects.create(user=user_signer, public_key=public_key_pem)


@pytest.fixture
def valid_signature(db, document_version, user_signer, rsa_key_pair, public_key_record):
    """Корректная Signature под document_version, подписанная rsa_key_pair"""
    private_key, _ = rsa_key_pair
    blob = make_signature_blob(private_key, document_version.file_hash)
    return Signature.objects.create(
        document_version=document_version,
        signer=user_signer,
        signature_blob=blob,
    )
