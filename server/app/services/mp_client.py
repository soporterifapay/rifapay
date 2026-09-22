"""Proveedores de movimientos MP.

- MockMpProvider: MVP local, los movimientos se inyectan vía POST /api/dev/mock-credit.
- RealMpProvider: OAuth real. Solo lectura (GET payments/users), nunca crea cobros.
"""
import json
from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx

from ..config import settings

API = "https://api.mercadopago.com"


class MpAuthError(Exception):
    pass


@dataclass
class MovementDTO:
    mp_payment_id: str
    amount: float
    date_created: datetime
    raw: str = "{}"


class MovementProvider:
    def search_recent(self, organizer_id: str) -> list[MovementDTO]:
        raise NotImplementedError


class MockMpProvider(MovementProvider):
    """MVP: los movimientos se inyectan vía POST /api/dev/mock-credit y se leen desde DB."""

    def search_recent(self, organizer_id: str) -> list[MovementDTO]:
        return []


def exchange_code(code: str) -> dict:
    """Cambia el code del callback por access/refresh tokens. Lanza MpAuthError si MP rechaza."""
    resp = httpx.post(
        f"{API}/oauth/token",
        json={
            "client_id": settings.mp_client_id,
            "client_secret": settings.mp_client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.mp_redirect_uri,
        },
        timeout=15,
    )
    if resp.status_code != 200:
        raise MpAuthError(f"token exchange: {resp.status_code} {resp.text[:200]}")
    return resp.json()


def refresh_access(refresh_token: str) -> dict:
    resp = httpx.post(
        f"{API}/oauth/token",
        json={
            "client_id": settings.mp_client_id,
            "client_secret": settings.mp_client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=15,
    )
    if resp.status_code != 200:
        raise MpAuthError(f"refresh: {resp.status_code} {resp.text[:200]}")
    return resp.json()


def api_get(access_token: str, path: str, params: dict | None = None) -> dict:
    resp = httpx.get(
        f"{API}{path}",
        headers={"Authorization": f"Bearer {access_token}"},
        params=params or {},
        timeout=15,
    )
    if resp.status_code == 401:
        raise MpAuthError("unauthorized")
    resp.raise_for_status()
    return resp.json()


def get_user(access_token: str) -> dict:
    return api_get(access_token, "/users/me")


def search_payments(access_token: str, collector_id: str, hours: int = 48) -> list[dict]:
    begin = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = api_get(
        access_token,
        "/v1/payments/search",
        {"collector.id": collector_id, "range": "date_created", "begin_date": begin, "sort": "date_created"},
    )
    return data.get("results", [])


def get_payment(access_token: str, payment_id: str) -> dict:
    return api_get(access_token, f"/v1/payments/{payment_id}")


def parse_mp_date(raw: str) -> datetime:
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00").split(".")[0]).replace(tzinfo=None)
    except Exception:
        return datetime.utcnow()


def to_movement(payment: dict) -> MovementDTO | None:
    if payment.get("status") != "approved":
        return None
    try:
        amount = round(float(payment.get("transaction_amount", 0)), 2)
    except (TypeError, ValueError):
        return None
    return MovementDTO(
        mp_payment_id=f"mp-{payment.get('id')}",
        amount=amount,
        date_created=parse_mp_date(str(payment.get("date_created", ""))),
        raw=json.dumps(payment, default=str)[:4000],
    )


def ingest_payments(db, organizer, payments: list[dict]) -> int:
    """Guarda pagos aprobados no vistos en movements_cache. Devuelve nuevos."""
    from .. import models  # import local para evitar ciclo

    new = 0
    for p in payments:
        mov = to_movement(p)
        if mov is None:
            continue
        if db.get(models.Movement, mov.mp_payment_id) is not None:
            continue
        db.add(models.Movement(
            mp_payment_id=mov.mp_payment_id,
            organizer_id=organizer.id,
            amount=mov.amount,
            date_created=mov.date_created,
            raw_json=mov.raw,
        ))
        new += 1
    if new:
        db.commit()
    return new
