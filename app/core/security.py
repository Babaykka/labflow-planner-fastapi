from datetime import UTC, datetime, timedelta
import base64
import hashlib
import hmac
import json
from secrets import token_bytes
from typing import Any

from app.core.config import get_settings

HASH_ITERATIONS = 210_000


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def hash_password(password: str) -> str:
    salt = token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, HASH_ITERATIONS)
    return f"pbkdf2_sha256${HASH_ITERATIONS}${_base64url_encode(salt)}${_base64url_encode(digest)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt, digest = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt_bytes = _base64url_decode(salt)
        expected = _base64url_decode(digest)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt_bytes,
            int(iterations),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _sign(message: bytes, secret_key: str) -> str:
    digest = hmac.new(secret_key.encode("utf-8"), message, hashlib.sha256).digest()
    return _base64url_encode(digest)


def encode_jwt(payload: dict[str, Any], secret_key: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_part = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_part}.{payload_part}".encode("ascii")
    return f"{header_part}.{payload_part}.{_sign(signing_input, secret_key)}"


def decode_jwt(token: str, secret_key: str) -> dict[str, Any]:
    try:
        header_part, payload_part, signature = token.split(".", 2)
        signing_input = f"{header_part}.{payload_part}".encode("ascii")
        expected_signature = _sign(signing_input, secret_key)
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid token signature")
        header = json.loads(_base64url_decode(header_part))
        if header.get("alg") != "HS256":
            raise ValueError("Unsupported token algorithm")
        payload = json.loads(_base64url_decode(payload_part))
        expires_at = payload.get("exp")
        if not isinstance(expires_at, int):
            raise ValueError("Token expiration is missing")
        if datetime.now(UTC).timestamp() > expires_at:
            raise ValueError("Token expired")
        return payload
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("Invalid access token") from exc


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    lifetime = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()),
    }
    return encode_jwt(payload, settings.secret_key)


def decode_access_token(token: str) -> dict[str, Any]:
    return decode_jwt(token, get_settings().secret_key)
