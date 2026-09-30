from alembic import context
from sqlalchemy import create_engine, pool

from app.config import settings
from app.db import Base
from app import models  # noqa: F401

config = context.config
# NOTA: no usar config.set_main_option("sqlalchemy.url", ...) porque
# ConfigParser valida sintaxis de interpolación y explota con passwords
# que contienen % (ej: %40). La URL se pasa directo al engine.

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=settings.database_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(settings.database_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
