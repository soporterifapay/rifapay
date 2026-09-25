from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..services.matcher import expire_old_orders

router = APIRouter()


@router.get("/raffles", response_model=list[schemas.RaffleOut])
def list_raffles(db: Session = Depends(get_db)):
    expire_old_orders(db)  # el contador nunca muestra reservas vencidas
    out = []
    for r in db.query(models.Raffle).filter(models.Raffle.status == "active").all():
        sold = db.query(models.Ticket).filter(models.Ticket.raffle_id == r.id, models.Ticket.status == "sold").count()
        res = db.query(models.Ticket).filter(models.Ticket.raffle_id == r.id, models.Ticket.status == "reserved").count()
        out.append(schemas.RaffleOut(
            id=r.id, title=r.title, description=r.description, total_numbers=r.total_numbers,
            price=r.price, prizes=r.prizes, status=r.status, sold_count=sold, reserved_count=res,
            draw_date=r.draw_date))
    return out


def _ago(dt) -> str:
    from datetime import datetime
    s = max(0, int((datetime.utcnow() - dt).total_seconds()))
    if s < 3600:
        return f"hace {max(1, s // 60)} min"
    if s < 86400:
        return f"hace {s // 3600} h"
    return f"hace {s // 86400} d"


@router.get("/raffles/{raffle_id}/recent")
def recent_sales(raffle_id: str, limit: int = 10, db: Session = Depends(get_db)):
    """Últimos números vendidos (prueba social). Sin PII: solo números + antigüedad gruesa."""
    from fastapi import HTTPException
    r = db.get(models.Raffle, raffle_id)
    if not r or r.status != "active":
        raise HTTPException(404, "Rifa no existe")
    limit = max(1, min(limit, 20))
    orders = (db.query(models.Order)
              .filter(models.Order.raffle_id == r.id, models.Order.status == "paid")
              .order_by(models.Order.created_at.desc()).limit(limit).all())
    import json
    out = []
    for o in orders:
        try:
            nums = json.loads(o.numbers_json)
        except Exception:
            continue
        out.append({"numbers": nums, "ago": _ago(o.created_at)})
        if len(out) >= limit:
            break
    return out


@router.get("/raffles/{raffle_id}")
def raffle_detail(raffle_id: str, db: Session = Depends(get_db)):
    expire_old_orders(db)
    r = db.get(models.Raffle, raffle_id)
    if not r:
        from fastapi import HTTPException
        raise HTTPException(404, "Rifa no existe")
    tickets = db.query(models.Ticket).filter(models.Ticket.raffle_id == r.id).order_by(models.Ticket.number).all()
    return {
        "id": r.id, "title": r.title, "description": r.description, "price": r.price,
        "prizes": r.prizes, "total_numbers": r.total_numbers,
        "draw_date": r.draw_date.isoformat() if r.draw_date else None,
        "cvu": r.cvu, "alias": r.alias, "holder": r.holder,
        "tickets": [{"number": t.number, "status": t.status} for t in tickets],
    }
