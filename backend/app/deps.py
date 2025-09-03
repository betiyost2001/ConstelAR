from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session
import jwt
from .config import settings
from .db import get_db
from .models import User


def get_current_user(access_token: str | None = Cookie(default=None), db: Session = Depends(get_db)) -> User:
    if not access_token:
        raise HTTPException(status_code=401, detail="No autenticado")
    try:
        payload = jwt.decode(access_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")
    uid = int(payload.get("sub"))
    tv = int(payload.get("tv", 0))
    user = db.get(User, uid)
    if not user or user.token_version != tv:
        raise HTTPException(status_code=401, detail="Sesión expirada")
    return user