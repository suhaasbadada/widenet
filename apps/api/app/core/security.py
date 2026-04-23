import hashlib
import hmac
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from dotenv import load_dotenv

from app.models.user import UserRole

load_dotenv()

_PASSWORD_HASH_NAME = "pbkdf2_sha256"
_PASSWORD_HASH_ITERATIONS = int(os.environ.get("PASSWORD_HASH_ITERATIONS", "600000"))
_JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
_JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)


class InvalidTokenError(ValueError):
    """Raised when an access token is invalid or expired."""


class SecurityConfigurationError(RuntimeError):
    """Raised when required security settings are missing."""


def ensure_jwt_configured() -> None:
    """Ensure the JWT secret exists before issuing or validating tokens."""
    if not os.environ.get("JWT_SECRET_KEY"):
        raise SecurityConfigurationError("JWT_SECRET_KEY is not configured.")


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a per-password salt."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        _PASSWORD_HASH_ITERATIONS,
    )
    return f"{_PASSWORD_HASH_NAME}${_PASSWORD_HASH_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, encoded_password: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2 hash."""
    try:
        hash_name, iterations, salt, stored_digest = encoded_password.split("$", 3)
    except ValueError:
        return False

    if hash_name != _PASSWORD_HASH_NAME:
        return False

    candidate_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        int(iterations),
    ).hex()
    return hmac.compare_digest(candidate_digest, stored_digest)


def create_access_token(user_id: str, email: str, role: str | UserRole) -> str:
    """Issue a signed JWT access token for the authenticated user."""
    ensure_jwt_configured()
    expires_at = datetime.now(UTC) + timedelta(minutes=_JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    normalized_role = UserRole(str(role)).value if str(role) in {r.value for r in UserRole} else UserRole.USER.value
    payload = {
        "sub": user_id,
        "email": email,
        "role": normalized_role,
        "type": "access",
        "exp": expires_at,
    }
    return jwt.encode(
        payload,
        os.environ["JWT_SECRET_KEY"],
        algorithm=_JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    ensure_jwt_configured()

    try:
        payload = jwt.decode(
            token,
            os.environ["JWT_SECRET_KEY"],
            algorithms=[_JWT_ALGORITHM],
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Invalid or expired access token.") from exc

    if payload.get("type") != "access" or not payload.get("sub"):
        raise InvalidTokenError("Invalid or expired access token.")

    role = str(payload.get("role") or UserRole.USER.value)
    if role not in {item.value for item in UserRole}:
        role = UserRole.USER.value
    payload["role"] = role

    return payload