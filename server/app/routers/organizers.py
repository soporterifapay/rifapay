from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import settings
from ..db import get_db
from ..deps import current_organizer, own_raffle, role_for_email
from ..ratelimit import limit_auth
from ..security import create_access_token, hash_password, verify_password

router = APIRouter()


@router.post("/auth/register", response_model=schemas.TokenOut, dependencies=[Depends(limit_auth)])
def register(data: schemas.OrganizerRegister, request: Request, db: Session = Depends(get_db)):
    if db.query(models.Organizer).filter(models.Organizer.email == data.email).first():
        raise HTTPException(400, "Email ya registrado")
    org = models.Organizer(email=data.email, name=data.name, password_hash=hash_password(data.password),
                           role=role_for_email(data.email))
    db.add(org)
    db.commit()
    db.refresh(org)
    return {"access_token": create_access_token(org.id)}


@router.get("/me")
def me(org: models.Organizer = Depends(current_organizer)):
    return {"id": org.id, "email": org.email, "name": org.name, "role": org.role}


@router.post("/auth/login", response_model=schemas.TokenOut, dependencies=[Depends(limit_auth)])
def login(data: schemas.OrganizerLogin, request: Request, db: Session = Depends(get_db)):
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
        id=raffle.id, title=raffle.title, description=raffle.description,
        total_numbers=raffle.total_numbers, price=raffle.price,
        prizes=raffle.prizes, status=raffle.status, sold_count=0, reserved_count=0,
        draw_date=raffle.draw_date,
    )


@router.get("/raffles", response_model=list[schemas.RaffleOut])
def my_raffles(db: Session = Depends(get_db), org: models.Organizer = Depends(current_organizer)):
    out = []
    for r in db.query(models.Raffle).filter(models.Raffle.organizer_id == org.id).all():
        sold = db.query(models.Ticket).filter(models.Ticket.raffle_id == r.id, models.Ticket.status == "sold").count()
        res = db.query(models.Ticket).filter(models.Ticket.raffle_id == r.id, models.Ticket.status == "reserved").count()
        out.append(schemas.RaffleOut(
            id=r.id, title=r.title, description=r.description, total_numbers=r.total_numbers,
            price=r.price, prizes=r.prizes, status=r.status, sold_count=sold, reserved_count=res,
            requested=r.publish_requested_at is not None, rejection_reason=r.rejection_reason or "",
            draw_date=r.draw_date))
    return out


@router.get("/raffles/{raffle_id}/orders")
def raffle_orders(raffle_id: str, db: Session = Depends(get_db), org: models.Organizer = Depends(current_organizer)):
    import json
    r = own_raffle(db, org, raffle_id)
    orders = db.query(models.Order).filter(models.Order.raffle_id == r.id).order_by(models.Order.created_at.desc()).all()
    return [
        {"id": o.id, "numbers": json.loads(o.numbers_json), "amount": o.amount, "status": o.status,
         "buyer": o.buyer_name, "created_at": o.created_at.isoformat(), "expires_at": o.expires_at.isoformat()}
        for o in orders
    ]


@router.get("/export/{raffle_id}.csv")
def export_csv(raffle_id: str, db: Session = Depends(get_db), org: models.Organizer = Depends(current_organizer)):
    import csv, io, json
    from fastapi.responses import PlainTextResponse
    r = own_raffle(db, org, raffle_id)
    orders = db.query(models.Order).filter(models.Order.raffle_id == r.id).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["order_id", "numbers", "amount", "status", "buyer", "created_at"])
    for o in orders:
        w.writerow([o.id, json.loads(o.numbers_json), o.amount, o.status, o.buyer_name, o.created_at.isoformat()])
    return PlainTextResponse(buf.getvalue(), media_type="text/csv")


@router.patch("/raffles/{raffle_id}/payout")
def update_payout(raffle_id: str, data: schemas.PayoutUpdate,
                  db: Session = Depends(get_db), org: models.Organizer = Depends(current_organizer)):
    """El organizador solo puede corregir datos de cobro mientras la rifa sigue pendiente."""
    r = own_raffle(db, org, raffle_id)
    if org.role != "admin" and r.status != "pending":
        raise HTTPException(403, "Publicada: solo el admin puede modificarla")
    if data.cvu is not None:
        r.cvu = data.cvu
    if data.alias is not None:
        r.alias = data.alias
    if data.holder is not None:
        r.holder = data.holder
    db.commit()
    return {"id": r.id, "cvu": r.cvu, "alias": r.alias, "holder": r.holder}


REQUEST_TEXT = ("Para publicar tu rifa debés abonar el servicio de RifaPay. "
                "Envía Solicitar autorización y te contactamos para activarla.")


@router.post("/raffles/{raffle_id}/request-publication")
def request_publication(raffle_id: str, db: Session = Depends(get_db),
                        org: models.Organizer = Depends(current_organizer)):
    """Solicita al admin la publicación. Solo aviso, idempotente."""
    from datetime import datetime

    from ..services import notifier

    r = own_raffle(db, org, raffle_id)
    if r.status != "pending":
        raise HTTPException(409, "La rifa ya no está pendiente")
    already = r.publish_requested_at is not None
    if not already:
        r.publish_requested_at = datetime.utcnow()
        db.commit()
        for admin_email in settings.admin_email_list():
            notifier._send_email(
                admin_email,
                f"Solicitud de publicación: {r.title}",
                f"El organizador {org.name} ({org.email}) solicita publicar la rifa "
                f"'{r.title}' ({r.total_numbers} números a $ {r.price}). "
                f"Revisar y aprobar en el panel admin.",
            )
    return {"status": r.status, "requested": True, "message": REQUEST_TEXT}


@router.patch("/account/payout")
def update_account_payout(data: schemas.PayoutUpdate,
                          db: Session = Depends(get_db), org: models.Organizer = Depends(current_organizer)):
    """Actualiza los datos de cobro de la conexión (se autocompletan en rifas nuevas)."""
    conn = db.query(models.MpConnection).filter(models.MpConnection.organizer_id == org.id).first()
    if not conn:
        raise HTTPException(404, "Conectá tu cuenta primero")
    if data.cvu is not None:
        conn.cvu = data.cvu
    if data.alias is not None:
        conn.alias = data.alias
    if data.holder is not None:
        conn.holder = data.holder
    db.commit()
    return {"cvu": conn.cvu, "alias": conn.alias, "holder": conn.holder}
