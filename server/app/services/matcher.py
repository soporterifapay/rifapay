import json
import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .. import models
from ..config import settings
from .notifier import notify_expiry


def generate_unique_amount(base_total: float, db: Session, raffle_id: str) -> float:
    """Monto base + centavos únicos no usados en órdenes activas de la rifa."""
    base = round(float(base_total), 2)
    used = {
        round(r[0], 2)
        for r in db.query(models.Order.amount)
        .filter(models.Order.raffle_id == raffle_id, models.Order.status.in_(["reserved", "receipt_uploaded"]))
        .all()
    }
    for _ in range(100):
        cents = random.randint(1, 99)
        candidate = round(int(base) + cents / 100.0, 2)
        if candidate == round(base, 2):
            candidate = round(candidate + 0.01, 2)
        if candidate not in used:
            return candidate
    return round(base + random.randint(1, 99) / 100.0, 2)


def expire_old_orders(db: Session) -> int:
    """Libera números a los 30min (reserva visible) y expira la orden tras la ventana de 24h.

    - Pasado expires_at: tickets vuelven a 'available' para que otro compre,
      pero la orden sigue buscando el crédito tardío (pago que demora COELSA).
    - Pasada la ventana de 24h sin match: orden 'expired' + aviso al comprador.
    """
    now = datetime.utcnow()
    olds = (
        db.query(models.Order)
        .filter(models.Order.status.in_(["reserved", "receipt_uploaded"]), models.Order.expires_at < now)
        .all()
    )
    count = 0
    for o in olds:
        limit = o.created_at + timedelta(hours=settings.match_window_hours) + timedelta(minutes=settings.reservation_minutes)
        tickets = db.query(models.Ticket).filter(models.Ticket.order_id == o.id).all()
        # siempre libera lo visible al vencer la reserva
        for t in tickets:
            if t.status == "reserved":
                t.status = "available"
                t.order_id = None
        if now > limit:
            try:
                numbers = json.loads(o.numbers_json)
            except Exception:
                numbers = []
            o.status = "expired"
            notify_expiry(db, o, numbers)
            count += 1
    if count or olds:
        db.commit()
    return count


def run_matcher(db: Session) -> int:
    """Busca movimientos no usados que calcen con órdenes activas. Devuelve matches."""
    expire_old_orders(db)
    matched = 0
    orders = (
        db.query(models.Order)
        .filter(models.Order.status.in_(["reserved", "receipt_uploaded"]))
        .order_by(models.Order.created_at.asc())
        .all()
    )
    for order in orders:
        window_end = order.created_at + timedelta(hours=settings.match_window_hours)
        mov = (
            db.query(models.Movement)
            .filter(
                models.Movement.organizer_id == order.organizer_id,
                models.Movement.amount == order.amount,
                models.Movement.used_by_order_id.is_(None),
                models.Movement.date_created >= order.created_at,
                models.Movement.date_created <= window_end,
            )
            .order_by(models.Movement.date_created.asc())
            .first()
        )
        if mov is None:
            continue
        mov.used_by_order_id = order.id
        order.status = "paid"
        # re-asigna tickets (pueden haberse liberado visualmente pero la orden sigue viva)
        try:
            numbers = json.loads(order.numbers_json)
        except Exception:
            numbers = []
        for n in numbers:
            t = (
                db.query(models.Ticket)
                .filter(models.Ticket.raffle_id == order.raffle_id, models.Ticket.number == int(n))
                .with_for_update()
                .first()
            )
            if t is None:
                continue
            if t.order_id is not None and t.order_id != order.id:
                continue  # otro comprador lo reservó/pagó después de liberarse
            t.status = "sold"
            t.order_id = order.id
        matched += 1
    if matched:
        db.commit()
    return matched
