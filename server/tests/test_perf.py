"""Performance: sin N+1 en listados, sin escrituras en GET publicos, matcher acotado."""
from datetime import datetime, timedelta

from app import models
from app.routers import public
from app.services import stats
from app.services.matcher import run_matcher


def _mk_raffle(db, org, rid, numbers=10, status="active"):
    r = models.Raffle(organizer_id=org.id, title=f"R {rid}", total_numbers=numbers,
                       price=1000.0, status=status)
    db.add(r)
    db.flush()
    db.add_all([models.Ticket(raffle_id=r.id, number=n) for n in range(1, numbers + 1)])
    db.commit()
    db.refresh(r)
    return r


def test_contadores_en_una_sola_query(db, org):
    r1 = _mk_raffle(db, org, "a")
    r2 = _mk_raffle(db, org, "b")
    t = db.query(models.Ticket).filter_by(raffle_id=r1.id, number=1).first()
    t.status = "sold"
    t2 = db.query(models.Ticket).filter_by(raffle_id=r1.id, number=2).first()
    t2.status = "reserved"
    db.commit()
    counts = stats.ticket_counts(db)
    assert counts[r1.id]["sold"] == 1
    assert counts[r1.id]["reserved"] == 1
    assert r2.id not in counts  # sin tickets usados
    # filtrado por subconjunto
    sub = stats.ticket_counts(db, [r2.id])
    assert sub == {}


def test_lista_publica_no_escribe_ni_expira(db, org):
    """El GET público no debe expirar reservas (eso lo hace el worker cada 60s)."""
    import inspect

    _mk_raffle(db, org, "c")
    assert "expire_old_orders" not in inspect.getsource(public.list_raffles)
    assert "expire_old_orders" not in inspect.getsource(public.raffle_detail)


def test_lista_publica_devuelve_contadores(db, org):
    r = _mk_raffle(db, org, "d")
    t = db.query(models.Ticket).filter_by(raffle_id=r.id, number=1).first()
    t.status = "sold"
    db.commit()
    out = public.list_raffles(db)
    mine = [x for x in out if x.id == r.id]
    assert mine and mine[0].sold_count == 1 and mine[0].reserved_count == 0


def test_matcher_procesa_lote_acotado(db, org, raffle):
    """Con muchas ordenes, el matcher no supera el lote configurado."""
    for i in range(5):
        o = models.Order(raffle_id=raffle.id, organizer_id=org.id, numbers_json=f"[{i + 1}]",
                         amount=1000.0 + i, buyer_name="L", status="reserved",
                         created_at=datetime.utcnow(), expires_at=datetime.utcnow() + timedelta(minutes=30))
        db.add(o)
    db.commit()
    from app.services import matcher

    old = matcher.MATCHER_BATCH
    matcher.MATCHER_BATCH = 2
    try:
        run_matcher(db)  # no debe explodes con lote chico
    finally:
        matcher.MATCHER_BATCH = old
