from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import settings
from ..db import get_db
from ..deps import current_organizer
from ..services.matcher import run_matcher

router = APIRouter()


@router.post("/dev/mock-credit")
def mock_credit(data: schemas.MockCreditIn, db: Session = Depends(get_db)):
    """Solo dev/QA con MP mock: simula que entró una transferencia al CVU del organizador."""
    if not settings.mp_mock_mode:
        # CRÍTICO: en producción esto permitiría acreditar pagos falsos. Bloqueado.
        raise HTTPException(404, "No existe")
    mp_id = f"mock-{int(datetime.utcnow().timestamp()*1000)}"
    db.add(models.Movement(
        mp_payment_id=mp_id, organizer_id=data.organizer_id,
        amount=round(float(data.amount), 2), date_created=datetime.utcnow(), raw_json='{"mock": true}'))
    db.commit()
    matched = run_matcher(db)
    return {"mp_payment_id": mp_id, "matched": matched}


class SmtpTestIn(BaseModel):
    to: str


@router.post("/dev/smtp-test")
def smtp_test(data: SmtpTestIn, db: Session = Depends(get_db),
              org: models.Organizer = Depends(current_organizer)):
    """TEMPORAL: diagnostica SMTP por etapas sin exponer secretos. Se borra despues."""
    import smtplib

    steps: dict[str, str] = {}
    if not settings.smtp_host or not settings.smtp_from:
        return {"error": "SMTP sin configurar (host/from vacios)"}
    if not settings.smtp_user or not settings.smtp_password:
        return {"error": "SMTP sin credenciales (user/password vacios)"}
    try:
        s = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15)
        code, _ = s.ehlo()
        steps["connect_ehlo"] = f"ok {code}"
    except Exception as exc:
        return {"error": f"connect: {str(exc)[:300]}", "steps": steps}
    try:
        code, _ = s.starttls()
        steps["starttls"] = f"ok {code}"
    except Exception as exc:
        return {"error": f"starttls: {str(exc)[:300]}", "steps": steps}
    try:
        code, _ = s.login(settings.smtp_user, settings.smtp_password)
        steps["login"] = f"ok {code}"
    except Exception as exc:
        return {"error": f"login: {str(exc)[:400]}", "steps": steps}
    try:
        from email.message import EmailMessage
        msg = EmailMessage()
        msg["From"] = settings.smtp_from
        msg["To"] = data.to
        msg["Subject"] = "[RifaPay] prueba SMTP"
        msg.set_content("Prueba de diagnostico, ignorar.")
        s.send_message(msg)
        steps["send"] = "ok"
    except Exception as exc:
        return {"error": f"send: {str(exc)[:400]}", "steps": steps}
    finally:
        try:
            s.quit()
        except Exception:
            pass
    return {"ok": True, "steps": steps}


@router.post("/dev/gmail-test")
def gmail_test(data: SmtpTestIn, db: Session = Depends(get_db),
               org: models.Organizer = Depends(current_organizer)):
    """TEMPORAL: prueba envio por Gmail API. Se borra despues."""
    from ..services import notifier

    if not (settings.google_client_id and settings.google_client_secret and settings.google_refresh_token):
        return {"error": "GOOGLE_* sin configurar"}
    res = notifier._send_gmail(data.to, "prueba Gmail API",
                               "Prueba de diagnostico RifaPay, ignorar.", None)
    return {"result": res}
