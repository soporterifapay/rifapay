from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine_kwargs = {"connect_args": connect_args, "pool_pre_ping": True}
if not settings.database_url.startswith("sqlite"):
    # Pool ajustado: conexiones calidas y reciclate antes de que el pooler las cierre
    # (antes cada request pagaba el setup de ~576ms de una conexion nueva).
    engine_kwargs.update(
        pool_size=5,
        max_overflow=5,
        pool_recycle=300,
        pool_use_lifo=True,
    )

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
