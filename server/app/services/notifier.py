"""Avisos al comprador. Email best-effort por SMTP si está configurado,
siempre se guarda aviso onscreen para mostrar en la página de la orden."""
import smtplib
from email.message import EmailMessage

from sqlalchemy.orm import Session

from .. import models
from ..config import settings

EXPIRY_SUBJECT = "Tu reserva expiró"
EXPIRY_TEXT = (
    "Hola {name}: tu reserva de los números {numbers} por ${amount} expiró "
    "porque no se acreditó el pago en 30 minutos. Los números volvieron a estar libres. "
    "Podés reservar de nuevo desde la página de la rifa."
)


def expiry_message(buyer_name: str, numbers: list, amount: float) -> str:
    nums = ", ".join(map(str, numbers)) if numbers else "-"
    return EXPIRY_TEXT.format(name=buyer_name or "gracias por participar", numbers=nums, amount=amount)


def notify_expiry(db: Session, order: models.Order, numbers: list) -> None:
    """Crea aviso onscreen + email si hay destinatario. Idempotente por orden."""
    if db.query(models.Notification).filter(models.Notification.order_id == order.id).first():
        return
    msg = expiry_message(order.buyer_name, numbers, order.amount)
    db.add(models.Notification(order_id=order.id, channel="onscreen", recipient="", message=msg, status="sent"))
    if order.buyer_email and "@" in order.buyer_email:
        status = _send_email(order.buyer_email, EXPIRY_SUBJECT, msg)
        db.add(models.Notification(
            order_id=order.id, channel="email", recipient=order.buyer_email, message=msg, status=status))


def _send_email(to: str, subject: str, body: str) -> str:
    if not settings.smtp_host or not settings.smtp_from:
        return "skipped"
    try:
        msg = EmailMessage()
        msg["From"] = settings.smtp_from
        msg["To"] = to
        msg["Subject"] = f"[RifaPay] {subject}"
        msg.set_content(body)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as s:
            if settings.smtp_user:
                s.starttls()
                s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
        return "sent"
    except Exception:
        return "skipped"
