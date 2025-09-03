# app/routes/notifications.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import NotificationPreference
from ..deps import get_current_user
from ..middleware.rate_limit import rate_limited

router = APIRouter()

# ===== Schemas =====
class PrefIn(BaseModel):
    channel: str   # email | whatsapp | push
    type: str      # alerta | novedad | recordatorio
    enabled: bool
    frequency: str | None = "immediate"

# ===== Endpoints =====
@router.get("/prefs")
@rate_limited("30/minute")
def get_prefs(db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = (
        db.query(NotificationPreference)
        .filter(NotificationPreference.user_id == user.id)
        .all()
    )
    return [
        {
            "channel": r.channel,
            "type": r.type,
            "enabled": r.enabled,
            "frequency": r.frequency,
        }
        for r in rows
    ]

@router.put("/prefs")
@rate_limited("10/minute")
def set_prefs(items: list[PrefIn], db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Borramos las preferencias previas y grabamos las nuevas
    db.query(NotificationPreference).filter(
        NotificationPreference.user_id == user.id
    ).delete()

    for it in items:
        db.add(
            NotificationPreference(
                user_id=user.id,
                channel=it.channel,
                type=it.type,
                enabled=it.enabled,
                frequency=it.frequency or "immediate",
            )
        )

    db.commit()
    return {"message": "Preferencias guardadas"}
