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
    b = {"raffle_id": rid, "buyer_name": "Ana"}
    r1 = client.post("/api/orders", json={**b, "numbers": [1, 2]})
    assert r1.status_code == 200, r1.text
    r2 = client.post("/api/orders", json={**b, "numbers": [2, 3]})
    assert r2.status_code == 409


def test_limite_reservas_por_dni(client, token):
    rid = _raffle(client, token)
    for nums in ([1], [2]):
        r = client.post("/api/orders", json={"raffle_id": rid, "numbers": nums,
                                             "buyer_name": "Bea", "buyer_dni": "DNI1"})
        assert r.status_code == 200, r.text
    r = client.post("/api/orders", json={"raffle_id": rid, "numbers": [3],
                                         "buyer_name": "Bea", "buyer_dni": "DNI1"})
    assert r.status_code == 429


def test_comprobante_duplicado_marca_riesgo(client, token):
    rid = _raffle(client, token)
    o1 = client.post("/api/orders", json={"raffle_id": rid, "numbers": [1], "buyer_name": "Celi"}).json()
    o2 = client.post("/api/orders", json={"raffle_id": rid, "numbers": [2], "buyer_name": "Dora"}).json()
    f1 = {"file": ("c.png", b"mismo-contenido", "image/png")}
    assert client.post(f"/api/orders/{o1['id']}/receipt", files=f1).json()["risk"] == "unknown"
    f2 = {"file": ("c.png", b"mismo-contenido", "image/png")}
    assert client.post(f"/api/orders/{o2['id']}/receipt", files=f2).json()["risk"] == "duplicate"


def test_flujo_mock_credit_paga(client, auth_org):
    org, token = auth_org
    rid = _raffle(client, token)
    o = client.post("/api/orders", json={"raffle_id": rid, "numbers": [1], "buyer_name": "Ema"}).json()
    m = client.post("/api/dev/mock-credit", json={"organizer_id": org.id, "amount": o["amount"]}).json()
    assert m["matched"] == 1
    assert client.get(f"/api/orders/{o['id']}").json()["status"] == "paid"
