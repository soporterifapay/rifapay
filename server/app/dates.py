"""Fechas UTC con Z explicita.

Todo el backend guarda datetimes naive que SON UTC (datetime.utcnow).
Sin la Z, el navegador los lee como hora local y suma el offset (bug del timer 209:44).
"""
from datetime import datetime, timezone


def iso_z(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
