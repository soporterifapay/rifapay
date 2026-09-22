from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import current_organizer
from ..security import create_access_token, hash_password, verify_password

router = APIRouter()


@router.post("/auth/register", response_model=schemas.TokenOut)
def register(data: schemas.OrganizerRegister, db: Session = Depends(get_db)):
    if db.query(models.Organizer).filter(models.Organizer.email == data.email).first():
        raise HTTPException(400, "Email ya registrado")
    org = models.Organizer(email=data.email, name=data.name, password_hash=hash_password(data.password))
    db.add(org)
    db.commit()
    db.refresh(org)
    return {"access_token": create_access_token(org.id)}


@router.post("/auth/login", response_model=schemas.TokenOut)
def login(data: schemas.OrganizerLogin, db: Session = Depends(get_db)):
    org = db.query(models.Organizer).filter(models.Organizer.email == data.email).first()
    if not org or not verify_password(data.password, org.password_hash):
        raise HTTPException(401, "Credenciales inválidas")
    return {"access_token": create_access_token(org.id)}


@router.post("/raffles", response_model=schemas.RaffleOut)
def create_raffle(
    data: schemas.RaffleCreate, db: Session = Depends(get_db), org: models.Organizer = Depends(current_organizer)
):
    raffle = models.Raffle(
        organizer_id=org.id,
        title=data.title,
        description=data.description,
        total_numbers=data.total_numbers,
        price=data.price,
        prizes=data.prizes,
        draw_date=data.draw_date,
        cvu=data.cvu,
        alias=data.alias,
        holder=data.holder,
    )
    db.add(raffle)
    db.flush()
    db.add_all([models.Ticket(raffle_id=raffle.id, number=n) for n in range(1, data.total_numbers + 1)])
    # autocompleta datos de cobro desde conexión MP si están vacíos
    conn = db.query(models.MpConnection).filter(models.MpConnection.organizer_id == org.id).first()
    if conn and conn.status == "connected":
        if not raffle.cvu:
            raffle.cvu = conn.cvu
        if not raffle.alias:
            raffle.alias = conn.alias
        if not raffle.holder:
            raffle.holder = conn.holder
    db.commit()
    db.refresh(raffle)
    return schemas.RaffleOut(
        id=raffle.id, title=raffle.title, total_numbers=raffle.total_numbers, price=raffle.price,
        prizes=raffle.prizes, status=raffle.status, sold_count=0, reserved_count=0,
    )


@router.get("/raffles", response_model=list[schemas.RaffleOut])
def my_raffles(db: Session = Depends(get_db), org: models.Organizer = Depends(current_organizer)):
    out = []
    for r in db.query(models.Raffle).filter(models.Raffle.organizer_id == org.id).all():
        sold = db.query(models.Ticket).filter(models.Ticket.raffle_id == r.id, models.Ticket.status == "sold").count()
        res = db.query(models.Ticket).filter(models.Ticket.raffle_id == r.id, models.Ticket.status == "reserved").count()
        out.append(schemas.RaffleOut(
            id=r.id, title=r.title, total_numbers=r.total_numbers, price=r.price,
            prizes=r.prizes, status=r.status, sold_count=sold, reserved_count=res))
    return out


@router.get("/raffles/{raffle_id}/orders")
def raffle_orders(raffle_id: str, db: Session = Depends(get_db), org: models.Organizer = Depends(current_organizer)):
    import json
    orders = db.query(models.Order).filter(models.Order.raffle_id == raffle_id).order_by(models.Order.created_at.desc()).all()
    return [
        {"id": o.id, "numbers": json.loads(o.numbers_json), "amount": o.amount, "status": o.status,
         "buyer": o.buyer_name, "created_at": o.created_at.isoformat(), "expires_at": o.expires_at.isoformat()}
        for o in orders
    ]


@router.get("/export/{raffle_id}.csv")
def export_csv(raffle_id: str, db: Session = Depends(get_db), org: models.Organizer = Depends(current_organizer)):
    import csv, io, json
    from fastapi.responses import PlainTextResponse
    orders = db.query(models.Order).filter(models.Order.raffle_id == raffle_id).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["order_id", "numbers", "amount", "status", "buyer", "created_at"])
    for o in orders:
        w.writerow([o.id, json.loads(o.numbers_json), o.amount, o.status, o.buyer_name, o.created_at.isoformat()])
    return PlainTextResponse(buf.getvalue(), media_type="text/csv")
