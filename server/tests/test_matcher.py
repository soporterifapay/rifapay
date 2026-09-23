"""Circuito feliz + reglas del matcher."""
from datetime import datetime, timedelta

from app import models
from app.services.matcher import expire_old_orders, generate_unique_amount, run_matcher


def test_monto_unico_no_se_repite(db, raffle):
    a1 = generate_unique_amount(2000.0, db, raffle.id)
    o = models.Order(raffle_id=raffle.id, organizer_id=raffle.organizer_id, numbers_json="[1]",
                     amount=a1, buyer_name="X", status="reserved",
                     created_at=datetime.utcnow(), expires_at=datetime.utcnow() + timedelta(minutes=30))
    db.add(o)
    db.commit()
    a2 = generate_unique_amount(2000.0, db, raffle.id)
    assert a1 != a2


def test_match_exacto_paga(db, raffle, org):
    o = models.Order(raffle_id=raffle.id, organizer_id=org.id, numbers_json="[1,2]",
                     amount=2000.33, buyer_name="Ana", status="reserved",
                     created_at=datetime.utcnow(), expires_at=datetime.utcnow() + timedelta(minutes=30))
    db.add(o)
    db.flush()
    for n in (1, 2):
        t = db.query(models.Ticket).filter_by(raffle_id=raffle.id, number=n).first()
        t.status = "reserved"
        t.order_id = o.id
    db.add(models.Movement(mp_payment_id="mp-1", organizer_id=org.id, amount=2000.33,
                           date_created=datetime.utcnow(), raw_json="{}"))
    db.commit()
    assert run_matcher(db) == 1
    assert db.get(models.Order, o.id).status == "paid"
    assert {t.number for t in db.query(models.Ticket).filter_by(order_id=o.id)} == {1, 2}


def test_movimiento_no_se_reutiliza(db, raffle, org):
    mk = lambda amt, num, pid: models.Order(
        raffle_id=raffle.id, organizer_id=org.id, numbers_json=f"[{num}]", amount=amt,
        buyer_name="B", status="reserved", created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=30))
    o1, o2 = mk(1000.11, 3, 0), mk(1000.11, 4, 0)
    db.add_all([o1, o2])
    db.add(models.Movement(mp_payment_id="mp-once", organizer_id=org.id, amount=1000.11,
                           date_created=datetime.utcnow(), raw_json="{}"))
    db.commit()
    assert run_matcher(db) == 1
    pagos = sorted([db.get(models.Order, o1.id).status, db.get(models.Order, o2.id).status])
    assert pagos == ["paid", "reserved"]  # un crédito = una sola orden


def test_monto_distinto_no_matchea(db, raffle, org):
    o = models.Order(raffle_id=raffle.id, organizer_id=org.id, numbers_json="[5]",
                     amount=1000.50, buyer_name="C", status="reserved",
                     created_at=datetime.utcnow(), expires_at=datetime.utcnow() + timedelta(minutes=30))
    db.add(o)
    db.add(models.Movement(mp_payment_id="mp-otro", organizer_id=org.id, amount=1000.00,
                           date_created=datetime.utcnow(), raw_json="{}"))
    db.commit()
    assert run_matcher(db) == 0
    assert db.get(models.Order, o.id).status == "reserved"


def test_reserva_vencida_libera_numero_pero_sigue_buscando(db, raffle, org):
    o = models.Order(raffle_id=raffle.id, organizer_id=org.id, numbers_json="[6]",
                     amount=1000.60, buyer_name="D", status="reserved",
                     created_at=datetime.utcnow() - timedelta(minutes=40),
                     expires_at=datetime.utcnow() - timedelta(minutes=5))
    db.add(o)
    db.flush()
    t = db.query(models.Ticket).filter_by(raffle_id=raffle.id, number=6).first()
    t.status = "reserved"
    t.order_id = o.id
    db.commit()
    expire_old_orders(db)
    assert db.query(models.Ticket).filter_by(raffle_id=raffle.id, number=6).first().status == "available"
    assert db.get(models.Order, o.id).status == "reserved"  # sigue viva hasta las 24h


def test_ventana_cumplida_expira_y_avisa(db, raffle, org):
    o = models.Order(raffle_id=raffle.id, organizer_id=org.id, numbers_json="[7]",
                     amount=1000.70, buyer_name="E", buyer_email="e@ejemplo.com", status="reserved",
                     created_at=datetime.utcnow() - timedelta(hours=25),
                     expires_at=datetime.utcnow() - timedelta(hours=24))
    db.add(o)
    db.commit()
    oid = o.id
    assert expire_old_orders(db) == 1
    assert db.get(models.Order, oid).status == "expired"
    chans = sorted(n.channel for n in db.query(models.Notification).filter_by(order_id=oid))
    assert chans == ["email", "onscreen"]
    # idempotente: segunda corrida no duplica avisos
    expire_old_orders(db)
    assert db.query(models.Notification).filter_by(order_id=oid).count() == 2
