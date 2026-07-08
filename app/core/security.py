from cryptography.fernet import Fernet
from passlib.context import CryptContext

from app.core.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_fernet = Fernet(settings.encryption_key.encode())


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return _pwd_context.verify(plain_password, password_hash)


def encrypt_secret(plain_text: str) -> str:
    return _fernet.encrypt(plain_text.encode()).decode()


def decrypt_secret(cipher_text: str) -> str:
    return _fernet.decrypt(cipher_text.encode()).decode()
