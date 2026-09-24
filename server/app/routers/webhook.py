from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import settings
from ..db import get_db
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
