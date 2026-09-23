from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import current_organizer
from ..services import mp_client
from ..services.matcher import run_matcher
from .mp_oauth import get_valid_token

router = APIRouter()


@router.post("/dev/mock-credit")
def mock_credit(data: schemas.MockCreditIn, db: Session = Depends(get_db)):
    """Solo dev/QA con MP mock: simula que entró una transferencia al CVU del organizador."""
    mp_id = f"mock-{int(datetime.utcnow().timestamp()*1000)}"
    db.add(models.Movement(
        mp_payment_id=mp_id, organizer_id=data.organizer_id,
        amount=round(float(data.amount), 2), date_created=datetime.utcnow(), raw_json='{"mock": true}'))
    db.commit()
    matched = run_matcher(db)
    return {"mp_payment_id": mp_id, "matched": matched}


@router.get("/dev/mp-debug")
def mp_debug(db: Session = Depends(get_db), org: models.Organizer = Depends(current_organizer)):
    """TEMPORAL diagnostico: muestra en crudo lo que MP devuelve (sin secretos ni datos del pagador)."""
    out = []
    for conn in db.query(models.MpConnection).filter(models.MpConnection.organizer_id == org.id).all():
        if conn.mp_user_id.startswith("mock-"):
            out.append({"conn": "mock", "skip": True})
            continue
        token = get_valid_token(db, conn)
        if not token:
            out.append({"mp_user_id": conn.mp_user_id, "token": "INVALIDO"})
            continue
        try:
            payments = mp_client.search_payments(token)
        except Exception as exc:
            out.append({"mp_user_id": conn.mp_user_id, "token": "ok", "search_error": str(exc)[:300]})
            continue
        sample = []
        for p in payments[:8]:
            sample.append({k: p.get(k) for k in (
                "id", "status", "status_detail", "transaction_amount", "date_created",
                "date_approved", "operation_type", "payment_type_id", "collector_id",
                "external_reference", "money_release_status")})
        known = {m.mp_payment_id for m in db.query(models.Movement).all()}
        would = sum(1 for p in payments
                    if p.get("status") == "approved" and f"mp-{p.get('id')}" not in known)
        out.append({"mp_user_id": conn.mp_user_id, "token": "ok",
                    "count": len(payments), "ingestibles_nuevos": would, "sample": sample})
    return out
