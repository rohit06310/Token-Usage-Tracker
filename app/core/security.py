"""
Security utilities:
  - FernetEncryption: symmetric encrypt/decrypt for API keys at rest
  - hash_api_key / verify_api_key: HMAC-SHA256 for dashboard auth
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Final, Any

import jwt
from cryptography.fernet import Fernet, InvalidToken
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


# ---------------------------------------------------------------------------
# Fernet encryption (API keys at rest)
# ---------------------------------------------------------------------------

class FernetEncryption:
    """
    Wraps the cryptography.fernet.Fernet cipher for encrypt-at-rest of
    provider API keys stored in the database.

    The encryption key is loaded ONCE from the FERNET_KEY environment
    variable (via Settings) and never touched again at runtime.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._fernet = Fernet(settings.fernet_key.encode())

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Returns a URL-safe base64-encoded ciphertext string suitable for
        storing in a VARCHAR / TEXT column.
        """
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a previously encrypted ciphertext string.

        Raises:
            cryptography.fernet.InvalidToken: if the ciphertext is corrupted,
            tampered with, or was encrypted with a different key.
        """
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken as e:
            raise ValueError(
                "Failed to decrypt value — possible key mismatch or data corruption."
            ) from e


# Module-level singleton — instantiated lazily on first import.
# Tests can override get_settings() to inject a test key.
_encryption_instance: FernetEncryption | None = None


def get_encryption() -> FernetEncryption:
    """Return the module-level FernetEncryption singleton."""
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = FernetEncryption()
    return _encryption_instance


# ---------------------------------------------------------------------------
# API-key hashing (dashboard auth)
# ---------------------------------------------------------------------------

_HASH_ALGORITHM: Final[str] = "sha256"


def hash_api_key(raw_key: str) -> str:
    """
    Produce a hex-encoded SHA-256 hash of the raw dashboard API key.

    We use HMAC with the Fernet key as the HMAC secret, so the hash is
    tied to the installation's secret material and cannot be rainbow-table
    attacked even if the hash leaks.
    """
    settings = get_settings()
    return hmac.new(
        key=settings.fernet_key.encode(),
        msg=raw_key.encode(),
        digestmod=_HASH_ALGORITHM,
    ).hexdigest()


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    """
    Constant-time comparison of a supplied key against its stored hash.

    Uses hmac.compare_digest to prevent timing-oracle attacks.
    """
    expected = hash_api_key(raw_key)
    return hmac.compare_digest(expected, stored_hash)


def generate_api_key(prefix: str = "sk") -> str:
    """
    Generate a cryptographically secure random API key.
    Format: <prefix>_<64 hex chars>
    """
    return f"{prefix}_{secrets.token_hex(32)}"


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ---------------------------------------------------------------------------
# JWT creation
# ---------------------------------------------------------------------------

def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt
