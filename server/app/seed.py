from datetime import datetime, timedelta

from .db import SessionLocal
from . import models
from .security import hash_password

DEMO_EMAIL = "demo@rifapay.local"


def main():
    db = SessionLocal()
    try:
        org = db.query(models.Organizer).filter(models.Organizer.email == DEMO_EMAIL).first()
        if not org:
            org = models.Organizer(email=DEMO_EMAIL, name="Organizador Demo", password_hash=hash_password("demo1234"))
            db.add(org)
            db.commit()
            db.refresh(org)
        raffle = db.query(models.Raffle).filter(models.Raffle.organizer_id == org.id).first()
        if not raffle:
            raffle = models.Raffle(
                organizer_id=org.id, title="Rifa Demo - TV 55 pulgadas",
                description="Rifa de prueba con conciliación automática simulada.",
                total_numbers=100, price=5000.0, prizes="1° TV 55\" - 2° $50.000",
                draw_date=datetime.utcnow() + timedelta(days=30),
                cvu="0000003100012345678901", alias="RIFA.PAGO.MOCK", holder="Organizador Demo",
                status="active",  # seed demo ya aprobada
            )
            db.add(raffle)
            db.flush()
            db.add_all([models.Ticket(raffle_id=raffle.id, number=n) for n in range(1, 101)])
            db.commit()
            print(f"seed raffle_id={raffle.id}")
        else:
            print(f"ya existe raffle_id={raffle.id}")
        print(f"login con {DEMO_EMAIL} / demo1234")
    finally:
        db.close()


if __name__ == "__main__":
    main()
