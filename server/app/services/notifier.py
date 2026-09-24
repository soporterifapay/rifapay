"""Avisos y comprobantes al comprador. Email best-effort por SMTP si está configurado,
siempre se guarda aviso onscreen para mostrar en la página de la orden."""
import html
import re
import smtplib
from email.message import EmailMessage

from sqlalchemy.orm import Session

from .. import models
from ..config import settings

EMAIL_RE = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"


def is_valid_email(v: str) -> bool:
    v = (v or "").strip()
    if "\n" in v or "\r" in v or len(v) > 254 or not v:
        return False
    return re.match(EMAIL_RE, v) is not None

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
    if db.query(models.Notification).filter(
            models.Notification.order_id == order.id,
            models.Notification.kind == "expiry").first():
        return
    msg = expiry_message(order.buyer_name, numbers, order.amount)
    db.add(models.Notification(order_id=order.id, kind="expiry", channel="onscreen",
                               recipient="", message=msg, status="sent"))
    if is_valid_email(order.buyer_email):
        status = _send_email(order.buyer_email, EXPIRY_SUBJECT, msg)
        db.add(models.Notification(order_id=order.id, kind="expiry", channel="email",
                                   recipient=order.buyer_email, message=msg, status=status))


def _send_email(to: str, subject: str, body: str, html_body: str | None = None) -> str:
    if not settings.smtp_host or not settings.smtp_from:
        return "skipped"
    if not is_valid_email(to):
        return "skipped"
    try:
        msg = EmailMessage()
        msg["From"] = settings.smtp_from
        msg["To"] = to.strip()
        msg["Subject"] = f"[RifaPay] {subject}"
        msg.set_content(body)
        if html_body:
            msg.add_alternative(html_body, subtype="html")
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as s:
            if settings.smtp_user:
                s.starttls()
                s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
        return "sent"
    except Exception:
        return "skipped"


def receipt_subject(raffle_title: str, numbers: list) -> str:
    return f"Pago confirmado: N° {', '.join(map(str, numbers))} - {raffle_title}"


def receipt_text(buyer_name: str, raffle_title: str, numbers: list, amount: float,
                 paid_at: str, order_id: str, dest: str, draw: str) -> str:
    lines = [
        "PAGO CONFIRMADO - RifaPay",
        f"Hola {buyer_name}, tus números ya participan del sorteo.",
        "",
        f"Rifa: {raffle_title}",
        f"Tus números: {', '.join(map(str, numbers))}",
        f"Monto acreditado: $ {amount:.2f}",
        f"Fecha de pago: {paid_at}",
        f"ID de orden: {order_id}",
    ]
    if draw:
        lines.append(f"Fecha del sorteo: {draw}")
    if dest:
        lines.append(f"Destino: {dest}")
    lines += ["",
              "Conservá el ID de orden ante cualquier reclamo.",
              "Constancia de compra RifaPay. No reemplaza el comprobante de tu banco."]
    return "\n".join(lines)


def receipt_html(buyer_name: str, raffle_title: str, numbers: list, amount: float,
                 paid_at: str, order_id: str, dest: str, draw: str, order_url: str) -> str:
    e = html.escape
    cells = "".join(
        f'<td style="padding:10px 16px;border:2px solid #059669;border-radius:10px;'
        f'font-size:22px;font-weight:bold;color:#065f46;">{n}</td>' for n in numbers)
    draw_row = (f'<tr><td style="padding:4px 0;color:#475569;">Fecha del sorteo</td>'
                f'<td style="padding:4px 0;font-weight:bold;">{e(draw)}</td></tr>' if draw else "")
    dest_row = (f'<tr><td style="padding:4px 0;color:#475569;">Destino</td>'
                f'<td style="padding:4px 0;font-weight:bold;">{e(dest)}</td></tr>' if dest else "")
    return f"""<div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
<div style="background:#059669;color:#fff;padding:16px 20px;">
<div style="font-size:18px;font-weight:bold;">&#10003; Pago confirmado</div>
<div style="font-size:14px;">{e(raffle_title)}</div></div>
<div style="padding:20px;">
<p style="margin:0 0 12px;">Hola {e(buyer_name)}, tus n&uacute;meros ya participan del sorteo.</p>
<p style="margin:0 0 8px;color:#475569;">Tus n&uacute;meros</p>
<table><tr>{cells}</tr></table>
<table style="margin-top:12px;width:100%;font-size:14px;">
<tr><td style="padding:4px 0;color:#475569;">Monto acreditado</td><td style="padding:4px 0;font-weight:bold;">$ {amount:.2f}</td></tr>
<tr><td style="padding:4px 0;color:#475569;">Fecha de pago</td><td style="padding:4px 0;font-weight:bold;">{e(paid_at)}</td></tr>
<tr><td style="padding:4px 0;color:#475569;">ID de orden</td><td style="padding:4px 0;font-weight:bold;">{e(order_id)}</td></tr>
{draw_row}{dest_row}</table>
<p style="font-size:12px;color:#64748b;">Conserv&aacute; el ID de orden ante cualquier reclamo.<br>
Constancia de compra RifaPay. No reemplaza el comprobante de tu banco.</p>
<p><a href="{e(order_url)}" style="display:inline-block;background:#059669;color:#fff;padding:10px 18px;border-radius:8px;text-decoration:none;">Ver mis n&uacute;meros</a></p>
</div></div>"""


def notify_paid(db: Session, order: models.Order) -> None:
    """Envía comprobante de compra al marcar paid. Best-effort e idempotente.

    Nunca debe romper el flujo de pago: cualquier error interno se traga.
    """
    try:
        if db.query(models.Notification).filter(
                models.Notification.order_id == order.id,
                models.Notification.kind == "receipt").first():
            return
        try:
            import json as _json
            numbers = _json.loads(order.numbers_json)
        except Exception:
            numbers = []
        raffle = db.get(models.Raffle, order.raffle_id)
        title = raffle.title if raffle else "Rifa"
        draw = ""
        if raffle is not None and getattr(raffle, "draw_date", None):
            try:
                draw = raffle.draw_date.strftime("%d/%m/%Y %H:%M")
            except Exception:
                draw = ""
        dest = ""
        if raffle is not None:
            dest = (raffle.alias or raffle.cvu or "").strip()
        paid_at = datetime_now_str()
        text = receipt_text(order.buyer_name, title, numbers, order.amount,
                            paid_at, order.id, dest, draw)
        url = f"{settings.frontend_url}/orden/{order.id}"
        html_body = receipt_html(order.buyer_name, title, numbers, order.amount,
                                 paid_at, order.id, dest, draw, url)
        db.add(models.Notification(order_id=order.id, kind="receipt", channel="onscreen",
                                   recipient="", message=text, status="sent"))
        if is_valid_email(order.buyer_email):
            status = _send_email(order.buyer_email, receipt_subject(title, numbers),
                                 text, html_body)
            db.add(models.Notification(order_id=order.id, kind="receipt", channel="email",
                                       recipient=order.buyer_email, message=text, status=status))
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass


def datetime_now_str() -> str:
    from datetime import datetime
    return datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")
