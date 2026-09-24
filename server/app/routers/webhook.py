from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import settings
from ..db import get_db
from ..deps import current_organizer
from ..services.matcher import run_matcher

router = APIRouter()


@router.post("/dev/mock-credit")
def mock_credit(data: schemas.MockCreditIn, db: Session = Depends(get_db)):
    """Solo dev/QA con MP mock: simula que entró una transferencia al CVU del organizador."""
    if not settings.mp_mock_mode:
        # CRÍTICO: en producción esto permitiría acreditar pagos falsos. Bloqueado.
        raise HTTPException(404, "No existe")
    mp_id = f"mock-{int(datetime.utcnow().timestamp()*1000)}"
    db.add(models.Movement(
        mp_payment_id=mp_id, organizer_id=data.organizer_id,
        amount=round(float(data.amount), 2), date_created=datetime.utcnow(), raw_json='{"mock": true}'))
    db.commit()
    matched = run_matcher(db)
    return {"mp_payment_id": mp_id, "matched": matched}


class ResendIn(BaseModel):
    order_id: str


@router.post("/dev/resend-receipt")
def resend_receipt(data: ResendIn, db: Session = Depends(get_db),
                   org: models.Organizer = Depends(current_organizer)):
    """TEMPORAL: reenvia comprobante de una orden paid (borra intento skipped). Se borra despues."""
    from ..services import notifier

    o = db.get(models.Order, data.order_id)
    if not o or o.status != "paid":
        raise HTTPException(404, "Orden no existe o no está pagada")
    db.query(models.Notification).filter(
        models.Notification.order_id == o.id,
        models.Notification.kind == "receipt").delete()
    db.commit()
    notifier.notify_paid(db, o)
    row = db.query(models.Notification).filter(
        models.Notification.order_id == o.id,
        models.Notification.kind == "receipt",
        models.Notification.channel == "email").order_by(
        models.Notification.created_at.desc()).first()
    return {"email_status": row.status if row else "?", "to": row.recipient if row else "?"}
