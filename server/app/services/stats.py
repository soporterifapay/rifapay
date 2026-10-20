"""Consultas agregadas para evitar N+1 (contadores de tickets en una sola query)."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models


def ticket_counts(db: Session, raffle_ids: list[str] | None = None) -> dict[str, dict[str, int]]:
    """Contadores de tickets (sold/reserved) por rifa en UNA sola consulta.

    Devuelve {raffle_id: {"sold": n, "reserved": n}}.
    """
    q = (
        db.query(models.Ticket.raffle_id, models.Ticket.status, func.count(models.Ticket.id))
        .filter(models.Ticket.status.in_(["sold", "reserved"]))
    )
    if raffle_ids is not None:
        if not raffle_ids:
            return {}
        q = q.filter(models.Ticket.raffle_id.in_(raffle_ids))
    out: dict[str, dict[str, int]] = {}
    for raffle_id, status, n in q.group_by(models.Ticket.raffle_id, models.Ticket.status).all():
        out.setdefault(raffle_id, {})[status] = n
    return out
