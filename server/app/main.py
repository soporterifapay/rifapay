import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import Base, SessionLocal, engine
from .routers import mp_oauth, orders, organizers, public, webhook

# Modelos para Alembic/autocreate en dev (en prod usar alembic upgrade head)
from . import models  # noqa: F401

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rifapay")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
    task = asyncio.create_task(_expiry_loop())
    logger.info("expiry loop started (cada %ss)", settings.expiry_check_seconds)
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _expiry_loop():
    """Revisor automático: trae movimientos reales, expira reservas y corre matcher."""
    from .services.matcher import expire_old_orders, run_matcher

    while True:
        try:
            stats = await asyncio.to_thread(_expiry_tick, expire_old_orders, run_matcher)
            logger.info("poll tick: %s", stats)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("expiry loop: %s", exc)
        await asyncio.sleep(settings.expiry_check_seconds)


def _expiry_tick(expire_fn, match_fn) -> dict:
    from . import models
    from .services import mp_client

    db = SessionLocal()
    stats = {"ingested": 0, "expired": 0, "matched": 0, "providers": 0, "errors": 0}
    try:
        if not settings.mp_mock_mode:
            # polling real: trae últimos pagos de cada cuenta conectada (mejor esfuerzo)
            from .routers.mp_oauth import get_valid_token

            for conn in db.query(models.MpConnection).filter(models.MpConnection.status == "connected").all():
                if conn.mp_user_id.startswith("mock-"):
                    continue
                stats["providers"] += 1
                try:
                    token = get_valid_token(db, conn)
                    if not token:
                        stats["errors"] += 1
                        continue
                    org = db.get(models.Organizer, conn.organizer_id)
                    if org is None:
                        continue
                    payments = mp_client.search_payments(token)
                    stats["ingested"] += mp_client.ingest_payments(db, org, payments, collector_id=conn.mp_user_id)
                except Exception as exc:
                    stats["errors"] += 1
                    logger.warning("poll %s: %s", conn.organizer_id, exc)
        stats["expired"] = expire_fn(db)
        stats["matched"] = match_fn(db)
    finally:
        db.close()
    return stats


@app.get("/api/health")
def health():
    return {"ok": True, "mock_mp": settings.mp_mock_mode}


app.include_router(public.router, prefix="/api", tags=["public"])
app.include_router(orders.router, prefix="/api", tags=["orders"])
app.include_router(organizers.router, prefix="/api/organizer", tags=["organizer"])
app.include_router(mp_oauth.router, prefix="/api", tags=["mp"])
app.include_router(webhook.router, prefix="/api", tags=["webhook"])
