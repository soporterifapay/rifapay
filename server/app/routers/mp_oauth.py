import secrets
import time
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..config import settings
from ..db import get_db
from ..deps import current_organizer
from ..security import decrypt_token, encrypt_token
from ..services import mp_client
from ..services.matcher import run_matcher

router = APIRouter()
_states: dict[str, tuple[str, float]] = {}
STATE_TTL = 600


def _front(path: str) -> str:
    return f"{settings.frontend_url}{path}"


@router.get("/mp/authorize-url")
def authorize_url(org: models.Organizer = Depends(current_organizer)):
    state = secrets.token_urlsafe(16)
    _states[state] = (org.id, time.time())
    # limpia states viejos
    for k, (_, ts) in list(_states.items()):
        if time.time() - ts > STATE_TTL:
            _states.pop(k, None)
    if settings.mp_mock_mode or not settings.mp_client_id:
        return {"url": f"/api/mp/callback?code=MOCK-{state}&state={state}", "mock": True}
    url = (
        "https://auth.mercadopago.com/authorization"
        f"?client_id={settings.mp_client_id}&response_type=code&platform_id=mp"
        f"&state={state}&redirect_uri={settings.mp_redirect_uri}"
    )
    return {"url": url, "mock": False}


@router.get("/mp/callback")
def callback(code: str, state: str, db: Session = Depends(get_db)):
    if code.startswith("MOCK-"):
        return _callback_mock(state, db)
    if settings.mp_mock_mode or not settings.mp_client_id:
        return RedirectResponse(_front("/dashboard?mp=not_configured"))
    item = _states.pop(state, None)
    if item is None:
        return RedirectResponse(_front("/dashboard?mp=error_state"))
    organizer_id = item[0]
    org = db.get(models.Organizer, organizer_id)
    if org is None:
        return RedirectResponse(_front("/dashboard?mp=error_state"))
    try:
        tokens = mp_client.exchange_code(code)
    except Exception:
        return RedirectResponse(_front("/dashboard?mp=error_token"))
    conn = db.query(models.MpConnection).filter(models.MpConnection.organizer_id == org.id).first()
    if not conn:
        conn = models.MpConnection(organizer_id=org.id)
        db.add(conn)
    conn.mp_user_id = str(tokens.get("user_id", ""))
    conn.access_token_enc = encrypt_token(tokens.get("access_token", ""))
    conn.refresh_token_enc = encrypt_token(tokens.get("refresh_token", ""))
    conn.expires_at = datetime.utcnow() + timedelta(seconds=int(tokens.get("expires_in", 15552000)))
    conn.status = "connected"
    try:  # mejor esfuerzo: trae nombre del titular para mostrar
        me = mp_client.get_user(tokens.get("access_token", ""))
        conn.holder = str(me.get("nickname") or me.get("email") or conn.holder)
    except Exception:
        pass
    db.commit()
    return RedirectResponse(_front("/dashboard?mp=connected"))


def _callback_mock(state: str, db: Session):
    item = _states.pop(state, None)
    org = db.get(models.Organizer, item[0]) if item else None
    if org is None:
        org = db.query(models.Organizer).order_by(models.Organizer.created_at.desc()).first()
    if org is None:
        return {"ok": False, "detail": "Creá un organizador primero"}
    conn = db.query(models.MpConnection).filter(models.MpConnection.organizer_id == org.id).first()
    if not conn:
        conn = models.MpConnection(organizer_id=org.id)
        db.add(conn)
    conn.mp_user_id = f"mock-user-{org.id}"
    conn.access_token_enc = encrypt_token("mock-access")
    conn.refresh_token_enc = encrypt_token("mock-refresh")
    conn.expires_at = datetime.utcnow() + timedelta(days=180)
    conn.status = "connected"
    conn.cvu = "0000003100012345678901"
    conn.alias = "RIFA.PAGO.MOCK"
    conn.holder = org.name or org.email
    db.commit()
    return RedirectResponse(_front("/dashboard?mp=connected"))


def get_valid_token(db: Session, conn: models.MpConnection) -> str | None:
    """Devuelve access_token vigente, renovando si hace falta. None si hay que reconectar."""
    if conn.mp_user_id.startswith("mock-"):
        return "mock-access"
    try:
        token = decrypt_token(conn.access_token_enc)
    except Exception:
        token = ""
    if conn.expires_at and conn.expires_at > datetime.utcnow() + timedelta(minutes=5) and token:
        return token
    try:
        data = mp_client.refresh_access(decrypt_token(conn.refresh_token_enc))
    except Exception:
        conn.status = "disconnected"
        db.commit()
        return None
    conn.access_token_enc = encrypt_token(data.get("access_token", ""))
    if data.get("refresh_token"):
        conn.refresh_token_enc = encrypt_token(data["refresh_token"])
    conn.expires_at = datetime.utcnow() + timedelta(seconds=int(data.get("expires_in", 15552000)))
    conn.status = "connected"
    db.commit()
    return data.get("access_token")


@router.post("/mp/refresh")
def refresh(db: Session = Depends(get_db), org: models.Organizer = Depends(current_organizer)):
    conn = db.query(models.MpConnection).filter(models.MpConnection.organizer_id == org.id).first()
    if not conn or conn.mp_user_id.startswith("mock-"):
        raise HTTPException(400, "Sin conexión real para renovar")
    # fuerza renovación
    conn.expires_at = datetime.utcnow()
    db.commit()
    token = get_valid_token(db, conn)
    if not token:
        raise HTTPException(401, "Hay que reconectar Mercado Pago")
    return {"status": "connected"}


@router.get("/mp/status")
def mp_status(db: Session = Depends(get_db), org: models.Organizer = Depends(current_organizer)):
    conn = db.query(models.MpConnection).filter(models.MpConnection.organizer_id == org.id).first()
    if not conn:
        return {"status": "disconnected", "mode": "mock" if settings.mp_mock_mode else "real"}
    return {
        "status": conn.status,
        "cvu": conn.cvu,
        "alias": conn.alias,
        "holder": conn.holder,
        "mode": "mock" if conn.mp_user_id.startswith("mock-") else "real",
    }


@router.post("/mp/disconnect")
def disconnect(db: Session = Depends(get_db), org: models.Organizer = Depends(current_organizer)):
    conn = db.query(models.MpConnection).filter(models.MpConnection.organizer_id == org.id).first()
    if conn:
        conn.status = "disconnected"
        conn.access_token_enc = ""
        conn.refresh_token_enc = ""
        db.commit()
    return {"status": "disconnected"}


@router.post("/mp/ipn")
async def ipn(request: Request, db: Session = Depends(get_db)):
    """Webhook MP: ante aviso de pago, trae el detalle e ingiere el movimiento real."""
    payment_id = ""
    try:
        body = await request.json()
        payment_id = str(((body.get("data") or {}).get("id")) or body.get("id") or "")
    except Exception:
        payment_id = request.query_params.get("data.id") or request.query_params.get("id") or ""
    if payment_id and not settings.mp_mock_mode:
        for conn in db.query(models.MpConnection).filter(models.MpConnection.status == "connected").all():
            if conn.mp_user_id.startswith("mock-"):
                continue
            token = get_valid_token(db, conn)
            if not token:
                continue
            try:
                payment = mp_client.get_payment(token, payment_id)
            except Exception:
                continue
            if "collector_id" in payment and str(payment.get("collector_id")) != conn.mp_user_id:
                continue
            org = db.get(models.Organizer, conn.organizer_id)
            if org:
                mp_client.ingest_payments(db, org, [payment], collector_id=conn.mp_user_id)
            break
    run_matcher(db)
    return {"ok": True}
