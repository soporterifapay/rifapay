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
            id=r.id, title=r.title, total_numbers=r.total_numbers, price=r.price,
            prizes=r.prizes, status=r.status, sold_count=sold, reserved_count=res))
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
        "cvu": r.cvu, "alias": r.alias, "holder": r.holder,
        "tickets": [{"number": t.number, "status": t.status} for t in tickets],
    }
