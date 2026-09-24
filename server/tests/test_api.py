"""API: auth, reserva, concurrencia, comprobantes."""


def test_register_login(client):
    r = client.post("/api/organizer/auth/register",
                    json={"email": "nuevo@ejemplo.com", "name": "N", "password": "clave123"})
    assert r.status_code == 200
    r = client.post("/api/organizer/auth/login",
                    json={"email": "nuevo@ejemplo.com", "password": "clave123"})
    assert r.status_code == 200 and r.json()["access_token"]
    r = client.post("/api/organizer/auth/login",
                    json={"email": "nuevo@ejemplo.com", "password": "mal"})
    assert r.status_code == 401


def test_sin_token_no_entra(client):
    assert client.get("/api/organizer/raffles").status_code == 401


def _raffle(client, token):
    r = client.post("/api/organizer/raffles", headers={"Authorization": f"Bearer {token}"},
                    json={"title": "R", "total_numbers": 5, "price": 1000.0})
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_reserva_doble_mismo_numero_da_409(client, token):
    rid = _raffle(client, token)
    b = {"raffle_id": rid, "buyer_name": "Ana", "buyer_email": "ana@ejemplo.com"}
    r1 = client.post("/api/orders", json={**b, "numbers": [1, 2]})
    assert r1.status_code == 200, r1.text
    r2 = client.post("/api/orders", json={**b, "numbers": [2, 3]})
    assert r2.status_code == 409


def test_limite_reservas_por_dni(client, token):
    rid = _raffle(client, token)
    for nums in ([1], [2]):
        r = client.post("/api/orders", json={"raffle_id": rid, "numbers": nums,
                                             "buyer_name": "Bea", "buyer_email": "bea@ejemplo.com", "buyer_dni": "DNI1"})
        assert r.status_code == 200, r.text
    r = client.post("/api/orders", json={"raffle_id": rid, "numbers": [3],
                                         "buyer_name": "Bea", "buyer_email": "bea@ejemplo.com", "buyer_dni": "DNI1"})
    assert r.status_code == 429


def test_comprobante_duplicado_marca_riesgo(client, token):
    rid = _raffle(client, token)
    o1 = client.post("/api/orders", json={"raffle_id": rid, "numbers": [1], "buyer_name": "Celi", "buyer_email": "celi@ejemplo.com"}).json()
    o2 = client.post("/api/orders", json={"raffle_id": rid, "numbers": [2], "buyer_name": "Dora", "buyer_email": "dora@ejemplo.com"}).json()
    f1 = {"file": ("c.png", b"mismo-contenido", "image/png")}
    assert client.post(f"/api/orders/{o1['id']}/receipt", files=f1).json()["risk"] == "unknown"
    f2 = {"file": ("c.png", b"mismo-contenido", "image/png")}
    assert client.post(f"/api/orders/{o2['id']}/receipt", files=f2).json()["risk"] == "duplicate"


def test_flujo_mock_credit_paga(client, auth_org):
    org, token = auth_org
    rid = _raffle(client, token)
    o = client.post("/api/orders", json={"raffle_id": rid, "numbers": [1], "buyer_name": "Ema", "buyer_email": "ema@ejemplo.com"}).json()
    m = client.post("/api/dev/mock-credit", json={"organizer_id": org.id, "amount": o["amount"]}).json()
    assert m["matched"] == 1
    assert client.get(f"/api/orders/{o['id']}").json()["status"] == "paid"


def test_email_obligatorio_y_valido(client, token):
    rid = _raffle(client, token)
    r = client.post("/api/orders", json={"raffle_id": rid, "numbers": [1], "buyer_name": "Sin Mail"})
    assert r.status_code == 422
    r = client.post("/api/orders", json={"raffle_id": rid, "numbers": [1], "buyer_name": "Mal Mail",
                                         "buyer_email": "no-es-mail"})
    assert r.status_code == 422
    r = client.post("/api/orders", json={"raffle_id": rid, "numbers": [1], "buyer_name": "Inyeccion",
                                         "buyer_email": "a@b.com\nBcc: x@y.com"})
    assert r.status_code == 422
    r = client.post("/api/orders", json={"raffle_id": rid, "numbers": [1], "buyer_name": "Bien",
                                         "buyer_email": "bien@ejemplo.com"})
    assert r.status_code == 200


def test_comprobante_al_pagar_y_sin_duplicar(client, auth_org, db):
    from app import models as _m
    org, token = auth_org
    rid = _raffle(client, token)
    o = client.post("/api/orders", json={"raffle_id": rid, "numbers": [1, 2], "buyer_name": "Recibo",
                                         "buyer_email": "recibo@ejemplo.com"}).json()
    client.post("/api/dev/mock-credit", json={"organizer_id": org.id, "amount": o["amount"]})
    recs = db.query(_m.Notification).filter_by(order_id=o["id"], kind="receipt").all()
    assert recs, "debe crear comprobante al pagar"
    mail = [n for n in recs if n.channel == "email"]
    assert mail and "1, 2" in mail[0].message and str(o["amount"]) in mail[0].message
    n0 = len(recs)
    from app.services.matcher import run_matcher
    run_matcher(db)
    assert db.query(_m.Notification).filter_by(order_id=o["id"], kind="receipt").count() == n0


def test_rate_limit_ordenes(client, token):
    rid = _raffle(client, token)
    codes = set()
    for i in range(25):
        r = client.post("/api/orders", json={"raffle_id": rid, "numbers": [(i % 5) + 1],
                                             "buyer_name": f"RL{i:02d}", "buyer_email": f"rl{i}@ejemplo.com",
                                             "buyer_dni": f"RL{i:03d}"})
        codes.add(r.status_code)
    assert 429 in codes


def test_order_status_trae_datos_comprobante(client, auth_org, db):
    org, token = auth_org
    rid = _raffle(client, token)
    o = client.post("/api/orders", json={"raffle_id": rid, "numbers": [4], "buyer_name": "WA",
                                         "buyer_email": "wa@ejemplo.com"}).json()
    client.post("/api/dev/mock-credit", json={"organizer_id": org.id, "amount": o["amount"]})
    s = client.get(f"/api/orders/{o['id']}").json()
    assert s["status"] == "paid"
    assert s["buyer_name"] == "WA" and s["paid_at"] and "dest" in s and "draw_date" in s
