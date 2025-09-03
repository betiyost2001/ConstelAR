import os, time, secrets, hashlib
from datetime import datetime, timedelta, timezone
import jwt
from argon2 import PasswordHasher
from .config import settings


ph = PasswordHasher()


def hash_password(plain: str) -> str:
    return ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return ph.verify(hashed, plain)
    except Exception:
        return False


def make_access_jwt(sub: str, token_version: int) -> str:
    now = int(time.time())
    exp = now + settings.ACCESS_TTL_MIN * 60
    payload = {"sub": sub, "tv": token_version, "type": "access", "iat": now, "exp": exp}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)



def refresh_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def _utcnow():
    return datetime.now(tz=timezone.utc)


def create_refresh_token(sub: int) -> str:
    now = _utcnow()
    payload = {
        "sub": str(sub),
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=int(settings.REFRESH_TTL_DAYS))).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def decode_token(token: str, expected_type: str | None = None) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        if expected_type and payload.get("type") != expected_type:
            raise jwt.InvalidTokenError("tipo de token inválido")
        return payload
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail="token expirado") from e  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=401, detail="token inválido") from e  # type: ignore