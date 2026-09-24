"""Notificador: validacion, idempotencia, Gmail API vs SMTP, sin red real."""
from app import models
from app.services import notifier


def test_is_valid_email():
    assert notifier.is_valid_email("a@b.com")
    assert not notifier.is_valid_email("mal")
    assert not notifier.is_valid_email("a@b.com\nBcc:x@y.com")
    assert not notifier.is_valid_email("")


def test_skip_sin_config(monkeypatch, db, org, raffle):
    monkeypatch.setattr(notifier.settings, "smtp_from", "")
    import datetime as _dt
    o = models.Order(raffle_id=raffle.id, organizer_id=org.id, numbers_json="[1]",
                     amount=1000.11, buyer_name="Mail", buyer_email="m@ejemplo.com",
                     status="paid", created_at=_dt.datetime.utcnow(),
                     expires_at=_dt.datetime.utcnow() + _dt.timedelta(minutes=30))
    db.add(o)
    db.commit()
    notifier.notify_paid(db, o)
    mail = db.query(models.Notification).filter_by(order_id=o.id, channel="email").one()
    assert mail.status == "skipped"  # sin SMTP se registra, no se envia


def test_gmail_ok_mockeado(monkeypatch, db, org, raffle):
    import datetime as _dt

    class R:
        status_code = 200

        def json(self):
            return {"access_token": "tok", "expires_in": 3600}

        def raise_for_status(self):
            return None

    class G:
        status_code = 200
        text = ""

    monkeypatch.setattr(notifier.settings, "smtp_from", "RifaPay <x@y.com>")
    monkeypatch.setattr(notifier.settings, "google_client_id", "cid")
    monkeypatch.setattr(notifier.settings, "google_client_secret", "csec")
    monkeypatch.setattr(notifier.settings, "google_refresh_token", "rtok")
    import httpx as _hx
    calls = []
    def fake_post(url, **kw):
        calls.append(url)
        return R() if "oauth2" in url else G()
    monkeypatch.setattr(_hx, "post", fake_post)
    o = models.Order(raffle_id=raffle.id, organizer_id=org.id, numbers_json="[3]",
                     amount=1000.33, buyer_name="Gmail", buyer_email="g@ejemplo.com",
                     status="paid", created_at=_dt.datetime.utcnow(),
                     expires_at=_dt.datetime.utcnow() + _dt.timedelta(minutes=30))
    db.add(o)
    db.commit()
    notifier.notify_paid(db, o)
    assert any("oauth2" in u for u in calls) and any("gmail" in u for u in calls)
    mail = db.query(models.Notification).filter_by(order_id=o.id, channel="email").one()
    assert mail.status == "sent" and "3" in mail.message
    # idempotente
    notifier.notify_paid(db, o)
    assert db.query(models.Notification).filter_by(order_id=o.id, kind="receipt").count() == 2

