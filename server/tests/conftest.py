"""Pytest setup: DB sqlite temporal por corrida, sin tocar la dev ni la nube."""
import os
import tempfile
import uuid

_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_db.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_db.name}"

import pytest
from fastapi.testclient import TestClient

from app import models
from app.db import SessionLocal, engine, Base
from app.main import app

Base.metadata.create_all(bind=engine)


def _mail(prefix="t"):
    return f"{prefix}-{uuid.uuid4().hex[:8]}@ejemplo.com"


@pytest.fixture()
def db():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture()
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def org(db):
    from app.security import hash_password

    o = models.Organizer(email=_mail("org"), name="Test", password_hash=hash_password("clave123"))
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


@pytest.fixture()
def raffle(db, org):
    r = models.Raffle(organizer_id=org.id, title="Rifa Test", total_numbers=10, price=1000.0,
                      cvu="CVU", alias="ALIAS", holder="Test")
    db.add(r)
    db.flush()
    db.add_all([models.Ticket(raffle_id=r.id, number=n) for n in range(1, 11)])
    db.commit()
    db.refresh(r)
    return r


@pytest.fixture()
def token(client):
    c = client.post("/api/organizer/auth/register",
                    json={"email": _mail("org"), "name": "O2", "password": "clave123"})
    assert c.status_code == 200, c.text
    return c.json()["access_token"]


@pytest.fixture()
def auth_org(client, db):
    """Organizador con token + conexión MP mock conectada."""
    email = _mail("mock")
    c = client.post("/api/organizer/auth/register",
                    json={"email": email, "name": "Mock", "password": "clave123"})
    token = c.json()["access_token"]
    org = db.query(models.Organizer).filter(models.Organizer.email == email).first()
    conn = models.MpConnection(organizer_id=org.id, mp_user_id=f"mock-user-{org.id}",
                               access_token_enc="x", refresh_token_enc="y",
                               status="connected", cvu="CVU", alias="ALIAS", holder="Mock")
    db.add(conn)
    db.commit()
    return org, token
