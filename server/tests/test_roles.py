"""Matriz roles: organizer inmutable, admin todopoderoso, aprobacion."""
import uuid

from app import models


def _mail(prefix="r"):
    return f"{prefix}-{uuid.uuid4().hex[:8]}@ejemplo.com"


def _reg(client, email=None, name="X"):
    r = client.post("/api/organizer/auth/register",
                    json={"email": email or _mail(), "name": name, "password": "clave12345"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _admin(client, monkeypatch):
    from app.config import settings
    email = _mail("jefe")
    monkeypatch.setattr(settings, "admin_emails", email)
    return _reg(client, email, "Jefe")


def _rifa(client, token, **kw):
    body = {"title": "R", "total_numbers": 5, "price": 100.0, "draw_date": "2026-12-01T20:00:00"}
    body.update(kw)
    r = client.post("/api/organizer/raffles", headers={"Authorization": f"Bearer {token}"}, json=body)
    assert r.status_code == 200, r.text
    return r.json()


def test_admin_por_env(monkeypatch, client):
    ta = _admin(client, monkeypatch)
    me = client.get("/api/organizer/me", headers={"Authorization": f"Bearer {ta}"}).json()
    assert me["role"] == "admin"
    t2 = _reg(client)
    me2 = client.get("/api/organizer/me", headers={"Authorization": f"Bearer {t2}"}).json()
    assert me2["role"] == "organizer"


def test_register_nunca_acepta_rol(client, db):
    email = _mail("vivo")
    _reg(client, email)
    org = db.query(models.Organizer).filter_by(email=email).one()
    assert org.role == "organizer"


def test_fecha_sorteo_obligatoria(client, token):
    H = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/organizer/raffles", headers=H,
                    json={"title": "Sin fecha", "total_numbers": 5, "price": 100.0})
    assert r.status_code == 422


def test_rifa_nace_pending_e_invisible(client, token):
    r = _rifa(client, token)
    assert r["status"] == "pending"
    assert all(x["id"] != r["id"] for x in client.get("/api/raffles").json())
    o = client.post("/api/orders", json={"raffle_id": r["id"], "numbers": [1],
                                         "buyer_name": "Ana", "buyer_email": "a@ejemplo.com"})
    assert o.status_code == 404


def test_organizador_no_edita_ni_pausa(monkeypatch, client, token, db):
    r = _rifa(client, token)
    H = {"Authorization": f"Bearer {token}"}
    # payout corregible solo mientras pending
    assert client.patch(f"/api/organizer/raffles/{r['id']}/payout", headers=H, json={"alias": "X"}).status_code == 200
    assert client.post(f"/api/organizer/raffles/{r['id']}/request-publication", headers=H).status_code == 200
    # segunda solicitud idempotente
    assert client.post(f"/api/organizer/raffles/{r['id']}/request-publication", headers=H).status_code == 200
    # aprobada -> payout bloqueado para organizador
    ta = _admin(client, monkeypatch)
    HA = {"Authorization": f"Bearer {ta}"}
    assert client.post(f"/api/admin/raffles/{r['id']}/approve", headers=HA).status_code == 200
    assert client.patch(f"/api/organizer/raffles/{r['id']}/payout", headers=H, json={"alias": "Y"}).status_code == 403
    # admin-only
    assert client.post("/api/admin/raffles/x/approve", headers=H).status_code == 403
    assert client.get("/api/admin/raffles", headers=H).status_code == 403


def test_ordenes_ajenas_404(client, token):
    t2 = _reg(client)
    r = _rifa(client, token)
    H2 = {"Authorization": f"Bearer {t2}"}
    assert client.get(f"/api/organizer/raffles/{r['id']}/orders", headers=H2).status_code == 404
    assert client.get(f"/api/organizer/export/{r['id']}.csv", headers=H2).status_code == 404


def test_flujo_aprobacion_y_pausa(monkeypatch, client, token, db):
    ta = _admin(client, monkeypatch)
    HA = {"Authorization": f"Bearer {ta}"}
    H = {"Authorization": f"Bearer {token}"}
    r = _rifa(client, token)
    assert client.post(f"/api/admin/raffles/{r['id']}/approve", headers=HA).status_code == 200
    assert any(x["id"] == r["id"] for x in client.get("/api/raffles").json())
    o = client.post("/api/orders", json={"raffle_id": r["id"], "numbers": [1],
                                         "buyer_name": "Ana", "buyer_email": "a@ejemplo.com"})
    assert o.status_code == 200
    # pausa admin bloquea nuevas
    assert client.patch(f"/api/admin/raffles/{r['id']}", headers=HA, json={"status": "paused"}).status_code == 200
    o2 = client.post("/api/orders", json={"raffle_id": r["id"], "numbers": [2],
                                          "buyer_name": "Beto", "buyer_email": "b@ejemplo.com"})
    assert o2.status_code == 404
    # reanuda
    assert client.patch(f"/api/admin/raffles/{r['id']}", headers=HA, json={"status": "active"}).status_code == 200
    # transicion invalida
    assert client.patch(f"/api/admin/raffles/{r['id']}", headers=HA, json={"status": "closed"}).status_code == 200
    assert client.patch(f"/api/admin/raffles/{r['id']}", headers=HA, json={"status": "active"}).status_code == 409


def test_rechazo_con_motivo(monkeypatch, client, token):
    ta = _admin(client, monkeypatch)
    HA = {"Authorization": f"Bearer {ta}"}
    r = _rifa(client, token)
    assert client.post(f"/api/admin/raffles/{r['id']}/reject", headers=HA, json={"reason": "ok"}).status_code == 422
    assert client.post(f"/api/admin/raffles/{r['id']}/reject", headers=HA, json={"reason": "falta premio"}).status_code == 200
    assert client.post(f"/api/admin/raffles/{r['id']}/reject", headers=HA, json={"reason": "otra"}).status_code == 409


def test_admin_edita_y_borra_con_reglas(monkeypatch, client, token):
    ta = _admin(client, monkeypatch)
    HA = {"Authorization": f"Bearer {ta}"}
    r = _rifa(client, token)
    assert client.patch(f"/api/admin/raffles/{r['id']}", headers=HA, json={"price": 200.0}).status_code == 200
    assert client.patch(f"/api/admin/raffles/{r['id']}", headers=HA,
                        json={"total_numbers": 9}).status_code == 400
    assert client.delete(f"/api/admin/raffles/{r['id']}", headers=HA).status_code == 200
