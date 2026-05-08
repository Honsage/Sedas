import base64

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def verify_signature(public_key_pem: str, file_hash_hex: str, signature_b64: str) -> bool:
    """
    Верифицирует RSA-SHA256 подпись над хешем файла.

    Клиент подписывает: RSA.sign(private_key, bytes.fromhex(file_hash), PKCS1v15, SHA256)
    Сервер проверяет: RSA.verify(public_key, те же байты, та же подпись)

    Возвращает True если подпись корректна, False в остальных случаях
    """
    try:
        public_key = serialization.load_pem_public_key(public_key_pem.encode())
        signature_bytes = base64.b64decode(signature_b64)
        data = bytes.fromhex(file_hash_hex)

        public_key.verify(signature_bytes, data, padding.PKCS1v15(), hashes.SHA256())
        return True
    except (InvalidSignature, Exception):
        return False
