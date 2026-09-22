from datetime import datetime, timedelta

from cryptography.fernet import Fernet, InvalidToken
from jose import jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": subject, "exp": expire}, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    return str(payload.get("sub"))


def _fernet() -> Fernet | None:
    if not settings.fernet_key:
        return None
    return Fernet(settings.fernet_key.encode())


def encrypt_token(raw: str) -> str:
    f = _fernet()
    if f is None:
        return raw  # solo dev sin FERNET_KEY; en Render siempre configurar
    return f.encrypt(raw.encode()).decode()


def decrypt_token(enc: str) -> str:
    f = _fernet()
    if f is None:
        return enc
    try:
        return f.decrypt(enc.encode()).decode()
    except InvalidToken:
        return enc
