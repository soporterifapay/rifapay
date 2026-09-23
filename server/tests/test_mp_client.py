"""Ingesta MP sin red: parseo, filtro collector y duplicados."""
from datetime import datetime

from app import models
from app.services import mp_client


def _pay(pid="1", amount=20.33, status="approved", collector="1921694"):
    return {"id": pid, "status": status, "transaction_amount": amount,
            "date_created": "2026-09-22T15:33:00.000-03:00", "collector_id": collector}


def test_to_movement_ok():
    m = mp_client.to_movement(_pay())
    assert m and m.mp_payment_id == "mp-1" and m.amount == 20.33
    assert isinstance(m.date_created, datetime)


def test_to_movement_descarta_no_aprobado():
    assert mp_client.to_movement(_pay(status="rejected")) is None


def test_ingest_filtra_otro_collector(db, org):
    assert mp_client.ingest_payments(db, org, [_pay(pid="9", collector="otro")],
                                     collector_id="1921694") == 0
    assert db.get(models.Movement, "mp-9") is None


def test_ingest_acepta_propio_y_no_duplica(db, org):
    assert mp_client.ingest_payments(db, org, [_pay(pid="7")], collector_id="1921694") == 1
    assert mp_client.ingest_payments(db, org, [_pay(pid="7")], collector_id="1921694") == 0
    mov = db.get(models.Movement, "mp-7")
    assert mov and mov.organizer_id == org.id and mov.amount == 20.33


def test_ingest_sin_collector_no_descarta(db, org):
    p = _pay(pid="8")
    del p["collector_id"]
    assert mp_client.ingest_payments(db, org, [p], collector_id="1921694") == 1
