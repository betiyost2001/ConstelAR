# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import secrets, logging, os

from ..db import get_db
from ..models import User, EmailToken
from ..security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from ..services.email import send_verify_email
from ..middleware.rate_limit import rate_limited

logger = logging.getLogger("uvicorn.error")
router = APIRouter()
IS_DEV = os.environ.get("APP_ENV") == "dev"


# ========= Schemas =========
class RegisterIn(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=8)


class MeOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str | None = "user"
    status: str | None = "pending"
    email_verified: bool = False


class VerifyIn(BaseModel):
    token: str


class VerifyOut(BaseModel):
    ok: bool
    email: EmailStr
    verified_at: datetime


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class LoginOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    refresh_token: str


class ResendIn(BaseModel):
    email: EmailStr

class ResendOut(BaseModel):
    ok: bool


# ========= Endpoints =========
@router.post("/register", response_model=MeOut, status_code=status.HTTP_200_OK)
@rate_limited("5/minute")
def register(
    payload: RegisterIn,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Crea usuario + token de verificación y envía email (best-effort).
    Sin SELECT previo: dejamos que el índice único de email haga cumplir la unicidad.
    """
    name = payload.name.strip()
    email = payload.email.lower().strip()
    password = payload.password

    if not name or not email or not password:
        raise HTTPException(status_code=422, detail="name, email y password son obligatorios")

    try:
        u = User(
            name=name,
            email=email,
            password_hash=hash_password(password),  # debe devolver str
            status="pending",
            role="user",
        )
        db.add(u)
        db.flush()  # obtiene u.id sin comitear

        token = secrets.token_urlsafe(32)
        db.add(
            EmailToken(
                user_id=u.id,
                token=token,
                purpose="verify",
                expires_at=datetime.utcnow() + timedelta(hours=24),
                used=False,
            )
        )

        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email ya registrado")
    except Exception as e:
        db.rollback()
        logger.exception("error en /auth/register")
        if IS_DEV:
            raise HTTPException(status_code=500, detail=f"DB error: {e}")
        raise HTTPException(status_code=500, detail="Error al registrar")

    # Envío en background (no bloquea la respuesta)
    try:
        background.add_task(send_verify_email, u.email, u.name or "Usuario", token)
    except Exception as e:
        logger.warning(f"no se pudo agendar email de verificación: {e}")

    return MeOut(
        id=u.id,
        name=u.name,
        email=u.email,
        role=getattr(u, "role", "user"),
        status=getattr(u, "status", "pending"),
        email_verified=bool(getattr(u, "email_verified_at", None)),
    )


@router.post("/verify-email", response_model=VerifyOut)
def verify_email(body: VerifyIn, db: Session = Depends(get_db)):
    """
    Marca el email como verificado si el token es válido y no expiró.
    """
    t = (body.token or "").strip()
    if not t:
        raise HTTPException(status_code=422, detail="token requerido")

    et = (
        db.query(EmailToken)
        .filter(
            EmailToken.token == t,
            EmailToken.purpose == "verify",
            EmailToken.used == False,  # noqa: E712
            EmailToken.expires_at > datetime.utcnow(),
        )
        .first()
    )
    if not et:
        raise HTTPException(status_code=400, detail="token inválido o expirado")

    user = db.get(User, et.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="usuario no existe")

    now = datetime.utcnow()
    user.email_verified_at = now
    user.status = "active"
    et.used = True
    db.commit()
    db.refresh(user)

    return VerifyOut(ok=True, email=user.email, verified_at=now)


@router.post("/login", response_model=LoginOut)
@rate_limited("10/minute")
def login(body: LoginIn, db: Session = Depends(get_db)):
    """
    Devuelve par de tokens (access + refresh) si las credenciales son válidas
    y el email está verificado.
    """
    email = body.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="credenciales inválidas")

    if not user.email_verified_at:
        raise HTTPException(status_code=403, detail="verificá tu email antes de ingresar")

    access = create_access_token(sub=user.id)
    refresh = create_refresh_token(sub=user.id)
    return LoginOut(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=LoginOut)
def refresh_token(body: RefreshIn):
    """
    Valida el refresh token y emite un access nuevo (y un refresh nuevo opcionalmente).
    """
    payload = decode_token(body.refresh_token, expected_type="refresh")
    uid = int(payload["sub"])
    access = create_access_token(sub=uid)
    new_refresh = create_refresh_token(sub=uid)  # puedes optar por reutilizar el existente
    return LoginOut(access_token=access, refresh_token=new_refresh)

@router.post("/resend-verification", response_model=ResendOut, status_code=status.HTTP_200_OK)
@rate_limited("3/hour")
def resend_verification(body: ResendIn, background: BackgroundTasks, db: Session = Depends(get_db)):
    email = body.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="usuario no existe")
    if user.email_verified_at:
        return ResendOut(ok=True)  # ya verificado, no hacemos nada

    # nuevo token (invalida los anteriores si querés: marcándolos used=True)
    token = secrets.token_urlsafe(32)
    db.add(EmailToken(
        user_id=user.id,
        token=token,
        purpose="verify",
        expires_at=datetime.utcnow() + timedelta(hours=24),
        used=False,
    ))
    db.commit()

    try:
        background.add_task(send_verify_email, user.email, user.name or "Usuario", token)
    except Exception as e:
        logger.warning(f"no se pudo agendar email de verificación: {e}")

    return ResendOut(ok=True)