import hashlib
import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import settings
from ..db import get_db
from ..services.matcher import generate_unique_amount, run_matcher

router = APIRouter()


@router.post("/orders", response_model=schemas.OrderOut)
def create_order(data: schemas.OrderCreate, db: Session = Depends(get_db)):
    raffle = db.get(models.Raffle, data.raffle_id)
    if not raffle or raffle.status != "active":
        raise HTTPException(404, "Rifa no disponible")
    # límite anti-bloqueo: 2 reservas activas por dni/tel
    if data.buyer_dni or data.buyer_phone:
        q = db.query(models.Order).filter(
            models.Order.raffle_id == raffle.id,
            models.Order.status.in_(["reserved", "receipt_uploaded"]),
        )
        if data.buyer_dni:
            q = q.filter(models.Order.buyer_dni == data.buyer_dni)
        active = q.count()
        if active >= 2:
            raise HTTPException(429, "Tenés demasiadas reservas activas, esperá que venzan")
    numbers = sorted(set(int(n) for n in data.numbers))
    if any(n < 1 or n > raffle.total_numbers for n in numbers):
        raise HTTPException(400, "Número fuera de rango")
    # lock de tickets
    tickets = (
        db.query(models.Ticket)
        .filter(models.Ticket.raffle_id == raffle.id, models.Ticket.number.in_(numbers))
        .with_for_update()
        .all()
    )
    if len(tickets) != len(numbers):
        raise HTTPException(400, "Números inválidos")
    for t in tickets:
        if t.status != "available":
            raise HTTPException(409, f"Número {t.number} ya no está libre")
    base_total = len(numbers) * float(raffle.price)
    amount = generate_unique_amount(base_total, db, raffle.id)
    order = models.Order(
        raffle_id=raffle.id,
        organizer_id=raffle.organizer_id,
        numbers_json=json.dumps(numbers),
        amount=amount,
        buyer_name=data.buyer_name,
        buyer_email=data.buyer_email,
        buyer_phone=data.buyer_phone,
        buyer_dni=data.buyer_dni,
        origin_last4=data.origin_last4,
        status="reserved",
        expires_at=datetime.utcnow() + timedelta(minutes=settings.reservation_minutes),
    )
    db.add(order)
    db.flush()
    for t in tickets:
        t.status = "reserved"
        t.order_id = order.id
    db.commit()
    run_matcher(db)
    return schemas.OrderOut(
        id=order.id, raffle_id=raffle.id, numbers=numbers, amount=amount, status=order.status,
        expires_at=order.expires_at, cvu=raffle.cvu, alias=raffle.alias, holder=raffle.holder,
        concept=f"RIFA{raffle.id}-{'_'.join(map(str, numbers))}",
    )


@router.get("/orders/{order_id}")
def order_status(order_id: str, db: Session = Depends(get_db)):
    import json
    o = db.get(models.Order, order_id)
    if not o:
        raise HTTPException(404, "Orden no existe")
    r = db.get(models.Raffle, o.raffle_id)
    note = (
        db.query(models.Notification)
        .filter(models.Notification.order_id == o.id, models.Notification.channel == "onscreen")
        .order_by(models.Notification.created_at.desc())
        .first()
    )
    return {
        "id": o.id, "numbers": json.loads(o.numbers_json), "amount": o.amount, "status": o.status,
        "expires_at": o.expires_at.isoformat(), "cvu": r.cvu, "alias": r.alias, "holder": r.holder,
        "notice": note.message if note else "",
        "raffle_id": r.id, "raffle_title": r.title,
    }


@router.post("/orders/{order_id}/notified")
def mark_notified(order_id: str, db: Session = Depends(get_db)):
    o = db.get(models.Order, order_id)
    if not o:
        raise HTTPException(404, "Orden no existe")
    if o.status == "reserved":
        o.status = "receipt_uploaded"
        db.commit()
    run_matcher(db)
    db.refresh(o)
    return {"status": o.status}


@router.post("/orders/{order_id}/receipt")
def upload_receipt(order_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Fase 1: solo guarda hash para duplicados (Fase 2 hará OCR). Nunca da pagado."""
    o = db.get(models.Order, order_id)
    if not o:
        raise HTTPException(404, "Orden no existe")
    content = file.file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "Archivo muy grande (máx 10MB)")
    sha = hashlib.sha256(content).hexdigest()
    dup = db.query(models.Receipt).filter(models.Receipt.sha256 == sha).first()
    risk = "duplicate" if dup else "unknown"
    db.add(models.Receipt(order_id=o.id, sha256=sha, filename=file.filename or "", ocr_json="{}", risk_score=risk))
    if o.status == "reserved":
        o.status = "receipt_uploaded"
    db.commit()
    run_matcher(db)
    return {"sha256": sha, "risk": risk, "detail": "Comprobante recibido. El pago se confirma solo cuando se acredita."}
