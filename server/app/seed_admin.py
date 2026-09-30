"""Seed idempotente del admin pre-creado. Corre en cada arranque; si el email ya
existe no toca nada (nunca pisa roles ni claves existentes)."""
from sqlalchemy.orm import Session

from . import models
from .config import settings
from .schemas import _check_password
from .security import hash_password


def seed_admin(db: Session) -> bool:
    email = (settings.admin_email or "").strip().lower()
    initial = settings.admin_initial_password or ""
    if not email or not initial:
        return False
    try:
        _check_password(initial)
    except Exception:
        return False
    if db.query(models.Organizer).filter(models.Organizer.email == email).first():
        return False
    db.add(models.Organizer(email=email, name="Administrador",
                            password_hash=hash_password(initial), role="admin"))
    db.commit()
    return True
