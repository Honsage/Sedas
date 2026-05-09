import base64
import hashlib

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from infrastructure.crypto import verify_signature


FILE_HASH = hashlib.sha256(b"document content").hexdigest()


def sign(private_key, file_hash_hex: str) -> str:
    data = bytes.fromhex(file_hash_hex)
    sig_bytes = private_key.sign(data, padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(sig_bytes).decode()


@pytest.fixture(scope="module")
def key_pair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_key, public_key_pem


@pytest.fixture(scope="module")
def other_key_pair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_key, public_key_pem


class TestVerifySignature:
    def test_valid_signature_returns_true(self, key_pair):
        private_key, public_key_pem = key_pair
        blob = sign(private_key, FILE_HASH)
        assert verify_signature(public_key_pem, FILE_HASH, blob) is True

    def test_wrong_key_returns_false(self, key_pair, other_key_pair):
        private_key, _ = key_pair
        _, other_public_pem = other_key_pair
        blob = sign(private_key, FILE_HASH)
        assert verify_signature(other_public_pem, FILE_HASH, blob) is False

    def test_tampered_data_returns_false(self, key_pair):
        private_key, public_key_pem = key_pair
        blob = sign(private_key, FILE_HASH)
        tampered_hash = hashlib.sha256(b"other content").hexdigest()
        assert verify_signature(public_key_pem, tampered_hash, blob) is False

    def test_invalid_base64_returns_false(self, key_pair):
        _, public_key_pem = key_pair
        assert verify_signature(public_key_pem, FILE_HASH, "not-valid-base64!!!") is False

    def test_invalid_pem_returns_false(self):
        assert verify_signature("not-a-pem-key", FILE_HASH, "dGVzdA==") is False

    def test_empty_signature_returns_false(self, key_pair):
        _, public_key_pem = key_pair
        assert verify_signature(public_key_pem, FILE_HASH, "") is False
