"""Auto-test de correo: latido semanal + alerta inmediata ante fallo."""
from datetime import datetime, timedelta

from app import main
from app.services import notifier


def test_alerta_invalida_se_omite():
    assert notifier.send_email_alert("", "skipped") == "skipped"
    assert notifier.send_email_alert("no-es-mail", "skipped") == "skipped"


def test_latido_sem_recipiente_no_hace_nada(monkeypatch):
    monkeypatch.setattr(main.settings, "selftest_recipient", "")
    state = {"last_ok": None, "last_attempt": None, "alerted": False}
    assert main._maybe_selftest(state) == state


def test_latido_envia_y_agenda_7_dias(monkeypatch):
    monkeypatch.setattr(main.settings, "selftest_recipient", "soporte@ejemplo.com")
    calls = []
    monkeypatch.setattr(notifier, "send_selftest_email", lambda r: calls.append(r) or "sent")
    state = {"last_ok": None, "last_attempt": None, "alerted": False}
    out = main._maybe_selftest(state)
    assert calls == ["soporte@ejemplo.com"]
    assert out["last_ok"] is not None
    # no vuelve a enviar hasta pasado el intervalo
    calls.clear()
    main._maybe_selftest(out)
    assert calls == []


def test_fallo_avisa_una_vez_y_reintenta_despues(monkeypatch):
    monkeypatch.setattr(main.settings, "selftest_recipient", "soporte@ejemplo.com")
    alerts = []
    monkeypatch.setattr(notifier, "send_selftest_email", lambda r: "skipped")
    monkeypatch.setattr(notifier, "send_email_alert", lambda r, s: alerts.append((r, s)) or "sent")
    state = {"last_ok": None, "last_attempt": None, "alerted": False}
    out = main._maybe_selftest(state)
    assert len(alerts) == 1 and out["alerted"] is True
    # no repite la alerta en el mismo cooldown
    out["last_attempt"] = datetime.utcnow() - timedelta(minutes=31)
    out = main._maybe_selftest(out)
    assert len(alerts) == 1
    # tras el cooldown reintenta el envio (sin duplicar alerta)
    out["last_attempt"] = datetime.utcnow() - timedelta(minutes=31)
    out = main._maybe_selftest(out)
    assert len(alerts) == 1


def test_exito_luego_fallo_reabre_alerta(monkeypatch):
    monkeypatch.setattr(main.settings, "selftest_recipient", "soporte@ejemplo.com")
    alerts = []
    monkeypatch.setattr(notifier, "send_email_alert", lambda r, s: alerts.append(r) or "sent")
    results = ["sent", "skipped"]
    monkeypatch.setattr(notifier, "send_selftest_email", lambda r: results.pop(0))
    state = {"last_ok": None, "last_attempt": None, "alerted": False}
    state = main._maybe_selftest(state)
    assert state["alerted"] is False
    # paso una semana: vuelve a tocar el latido y ahora falla -> alerta
    state["last_ok"] = datetime.utcnow() - timedelta(days=8)
    state["last_attempt"] = datetime.utcnow() - timedelta(minutes=31)
    state = main._maybe_selftest(state)
    assert len(alerts) == 1 and state["alerted"] is True
