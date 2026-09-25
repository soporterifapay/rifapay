from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import models
from .config import settings
from .db import get_db
from .security import decode_access_token

bearer = HTTPBearer(auto_error=False)


def role_for_email(email: str) -> str:
    return "admin" if email.strip().lower() in settings.admin_email_list() else "organizer"


def current_organizer(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> models.Organizer:
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Falta token")
    try:
        organizer_id = decode_access_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    org = db.get(models.Organizer, organizer_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Organizador no existe")
    # rol siempre de DB + lista env (nunca del token ni del cliente)
    want = role_for_email(org.email)
    if org.role != want and want == "admin":
        org.role = "admin"
        db.commit()
    return org


def require_admin(org: models.Organizer = Depends(current_organizer)) -> models.Organizer:
    if org.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo admin")
    return org


def own_raffle(db: Session, org: models.Organizer, raffle_id: str) -> models.Raffle:
    """Rifa propia o admin. Cierra el hueco de propiedad."""
    r = db.get(models.Raffle, raffle_id)
    if r is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rifa no existe")
    if org.role != "admin" and r.organizer_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rifa no existe")
    return r
