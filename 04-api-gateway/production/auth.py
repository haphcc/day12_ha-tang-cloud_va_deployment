"""
JWT Authentication Module

JWT (JSON Web Token) = stateless auth.
Token chứa: user_id, role, expiry → không cần check DB mỗi request.

Flow:
    POST /auth/token  → trả về JWT
    GET  /ask         → gửi JWT trong header Authorization: Bearer <token>
    Server verify signature → extract user info → process request
"""
import os
import time
import json
import base64
import hmac
import hashlib
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-change-in-production-please")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Demo users (trong thực tế lưu trong database)
DEMO_USERS = {
    "student": {"password": "demo123", "role": "user", "daily_limit": 50},
    "teacher": {"password": "teach456", "role": "admin", "daily_limit": 1000},
}

security = HTTPBearer(auto_error=False)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def _jwt_encode(payload: dict, secret: str) -> str:
    header = {"alg": ALGORITHM, "typ": "JWT"}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{_b64url_encode(signature)}"


def _jwt_decode(token: str, secret: str) -> dict:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Invalid token format.") from exc

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    provided_sig = _b64url_decode(signature_b64)

    if not hmac.compare_digest(expected_sig, provided_sig):
        raise HTTPException(status_code=403, detail="Invalid token signature.")

    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    exp = int(payload.get("exp", 0))
    if exp and int(time.time()) > exp:
        raise HTTPException(status_code=401, detail="Token expired. Please login again.")
    return payload


def create_token(username: str, role: str) -> str:
    """Tạo JWT token với expiry."""
    payload = {
        "sub": username,           # subject (user identifier)
        "role": role,
        "iat": int(datetime.now(timezone.utc).timestamp()),  # issued at
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    return _jwt_encode(payload, SECRET_KEY)


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Dependency: verify JWT token từ Authorization header.
    Raise HTTPException nếu token invalid hoặc expired.
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Include: Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _jwt_decode(credentials.credentials, SECRET_KEY)
    return {
        "username": payload["sub"],
        "role": payload["role"],
    }


def authenticate_user(username: str, password: str) -> dict:
    """Kiểm tra username/password, trả về user info nếu hợp lệ."""
    user = DEMO_USERS.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"username": username, "role": user["role"]}
