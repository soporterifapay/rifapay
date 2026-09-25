"""Gobernanza total del admin. Todo acá exige rol admin (nunca organizer)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import require_admin
from ..services import notifier

router = APIRouter()

TRANSITIONS = {
    "pending": {"active", "rejected"},
    "active": {"paused", "closed"},
    "paused": {"active", "closed"},
    "rejected": {"active"},
    "closed": set(),
}


def _counts(db: Session, r: models.Raffle) -> dict:
    sold = db.query(models.Ticket).filter(
        models.Ticket.raffle_id == r.id, models.Ticket.status == "sold").count()
    res = db.query(models.Ticket).filter(
        models.Ticket.raffle_id == r.id, models.Ticket.status == "reserved").count()
    return {"sold": sold, "reserved": res}


@router.get("/raffles")
def all_raffles(status: str | None = Query(default=None),
                db: Session = Depends(get_db), org: models.Organizer = Depends(require_admin)):
    q = db.query(models.Raffle)
    if status:
        q = q.filter(models.Raffle.status == status)
    out = []
    for r in q.order_by(models.Raffle.created_at.desc()).all():
        owner = db.get(models.Organizer, r.organizer_id)
        c = _counts(db, r)
        out.append({"id": r.id, "title": r.title, "status": r.status, "price": r.price,
                    "total_numbers": r.total_numbers, "sold": c["sold"], "reserved": c["reserved"],
                    "owner_email": owner.email if owner else "?",
                    "requested": r.publish_requested_at is not None,
                    "rejection_reason": r.rejection_reason})
    return out


@router.post("/raffles/{raffle_id}/approve")
def approve(raffle_id: str, db: Session = Depends(get_db), org: models.Organizer = Depends(require_admin)):
    r = db.get(models.Raffle, raffle_id)
    if not r:
        raise HTTPException(404, "Rifa no existe")
    if r.status not in ("pending", "rejected"):
        raise HTTPException(409, f"No se puede aprobar desde {r.status}")
    r.status = "active"
    r.rejection_reason = ""
    db.commit()
    return {"id": r.id, "status": r.status}


@router.post("/raffles/{raffle_id}/reject")
def reject(raffle_id: str, data: schemas.RejectIn,
           db: Session = Depends(get_db), org: models.Organizer = Depends(require_admin)):
    r = db.get(models.Raffle, raffle_id)
    if not r:
        raise HTTPException(404, "Rifa no existe")
    if r.status != "pending":
        raise HTTPException(409, f"No se puede rechazar desde {r.status}")
    r.status = "rejected"
    r.rejection_reason = data.reason
    db.commit()
    owner = db.get(models.Organizer, r.organizer_id)
    if owner and notifier.is_valid_email(owner.email):
        notifier._send_email(owner.email, f"Rifa rechazada: {r.title}",
                             f"Hola {owner.name or ''}: tu rifa '{r.title}' fue rechazada.\n"
                             f"Motivo: {data.reason}\nCorregila o contactanos para volver a solicitarla.")
    return {"id": r.id, "status": r.status}


@router.patch("/raffles/{raffle_id}")
def admin_update(raffle_id: str, data: schemas.RaffleAdminUpdate,
                 db: Session = Depends(get_db), org: models.Organizer = Depends(require_admin)):
    r = db.get(models.Raffle, raffle_id)
    if not r:
        raise HTTPException(404, "Rifa no existe")
    if data.total_numbers is not None and data.total_numbers != r.total_numbers:
        raise HTTPException(400, "No se puede cambiar la cantidad de números con tickets generados")
    for field in ("title", "description", "price", "prizes", "draw_date", "cvu", "alias", "holder"):
        v = getattr(data, field)
        if v is not None:
            setattr(r, field, v)
    if data.status is not None:
        if data.status == r.status:
            pass
        elif data.status not in TRANSITIONS.get(r.status, set()):
            raise HTTPException(409, f"Transición inválida {r.status} -> {data.status}")
        else:
            r.status = data.status
            if data.status == "active":
                r.rejection_reason = ""
    db.commit()
    return {"id": r.id, "status": r.status}


@router.delete("/raffles/{raffle_id}")
def admin_delete(raffle_id: str, db: Session = Depends(get_db), org: models.Organizer = Depends(require_admin)):
    r = db.get(models.Raffle, raffle_id)
    if not r:
        raise HTTPException(404, "Rifa no existe")
    if r.status not in ("pending", "rejected"):
        sold = db.query(models.Ticket).filter(
            models.Ticket.raffle_id == r.id, models.Ticket.status == "sold").count()
        if sold > 0:
            raise HTTPException(409, "Con ventas no se elimina: pausar o cerrar")
    db.query(models.Ticket).filter(models.Ticket.raffle_id == r.id).delete()
    db.query(models.Order).filter(models.Order.raffle_id == r.id).delete()
    db.delete(r)
    db.commit()
    return {"deleted": raffle_id}


@router.get("/orders")
def admin_orders(raffle_id: str | None = Query(default=None),
                 status: str | None = Query(default=None),
                 limit: int = Query(default=50, le=200),
                 db: Session = Depends(get_db), org: models.Organizer = Depends(require_admin)):
    import json
    q = db.query(models.Order).order_by(models.Order.created_at.desc())
    if raffle_id:
        q = q.filter(models.Order.raffle_id == raffle_id)
    if status:
        q = q.filter(models.Order.status == status)
    return [{"id": o.id, "raffle_id": o.raffle_id, "numbers": json.loads(o.numbers_json),
             "amount": o.amount, "status": o.status, "buyer": o.buyer_name,
             "email": o.buyer_email} for o in q.limit(limit).all()]
