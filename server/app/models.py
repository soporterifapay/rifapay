import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _uid() -> str:
    return uuid.uuid4().hex[:12]


class Organizer(Base):
    __tablename__ = "organizers"
    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=_uid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MpConnection(Base):
    __tablename__ = "mp_connections"
    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=_uid)
    organizer_id: Mapped[str] = mapped_column(String(12), ForeignKey("organizers.id"), unique=True, index=True)
    mp_user_id: Mapped[str] = mapped_column(String(64), default="")
    access_token_enc: Mapped[str] = mapped_column(Text, default="")
    refresh_token_enc: Mapped[str] = mapped_column(Text, default="")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="disconnected")  # connected|disconnected|error
    cvu: Mapped[str] = mapped_column(String(64), default="")
    alias: Mapped[str] = mapped_column(String(64), default="")
    holder: Mapped[str] = mapped_column(String(255), default="")


class Raffle(Base):
    __tablename__ = "raffles"
    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=_uid)
    organizer_id: Mapped[str] = mapped_column(String(12), ForeignKey("organizers.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    total_numbers: Mapped[int] = mapped_column(Integer, default=100)
    price: Mapped[float] = mapped_column(Float)
    prizes: Mapped[str] = mapped_column(Text, default="")
    draw_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cvu: Mapped[str] = mapped_column(String(64), default="")
    alias: Mapped[str] = mapped_column(String(64), default="")
    holder: Mapped[str] = mapped_column(String(255), default="")
    verification_mode: Mapped[str] = mapped_column(String(32), default="auto_mp")  # auto_mp|manual
    status: Mapped[str] = mapped_column(String(32), default="active")  # active|paused|closed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="raffle", cascade="all, delete-orphan")


class Ticket(Base):
    __tablename__ = "tickets"
    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=_uid)
    raffle_id: Mapped[str] = mapped_column(String(12), ForeignKey("raffles.id"), index=True)
    number: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(16), default="available", index=True)  # available|reserved|sold
    order_id: Mapped[str | None] = mapped_column(String(12), ForeignKey("orders.id"), nullable=True)
    raffle: Mapped["Raffle"] = relationship(back_populates="tickets")
    __table_args__ = (UniqueConstraint("raffle_id", "number", name="uq_raffle_number"),)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=_uid)
    raffle_id: Mapped[str] = mapped_column(String(12), ForeignKey("raffles.id"), index=True)
    organizer_id: Mapped[str] = mapped_column(String(12), ForeignKey("organizers.id"), index=True)
    numbers_json: Mapped[str] = mapped_column(Text, default="[]")
    amount: Mapped[float] = mapped_column(Float)  # monto único con centavos
    buyer_name: Mapped[str] = mapped_column(String(255))
    buyer_email: Mapped[str] = mapped_column(String(255), default="")
    buyer_phone: Mapped[str] = mapped_column(String(64), default="")
    buyer_dni: Mapped[str] = mapped_column(String(32), default="")
    origin_last4: Mapped[str] = mapped_column(String(8), default="")
    status: Mapped[str] = mapped_column(String(24), default="reserved", index=True)
    # reserved|receipt_uploaded|paid|expired|observed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class Movement(Base):
    __tablename__ = "movements_cache"
    mp_payment_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organizer_id: Mapped[str] = mapped_column(String(12), index=True)
    amount: Mapped[float] = mapped_column(Float, index=True)
    date_created: Mapped[datetime] = mapped_column(DateTime, index=True)
    raw_json: Mapped[str] = mapped_column(Text, default="{}")
    used_by_order_id: Mapped[str | None] = mapped_column(String(12), nullable=True, index=True)


class Receipt(Base):
    __tablename__ = "receipts"
    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=_uid)
    order_id: Mapped[str] = mapped_column(String(12), ForeignKey("orders.id"), index=True)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    filename: Mapped[str] = mapped_column(String(255), default="")
    ocr_json: Mapped[str] = mapped_column(Text, default="{}")
    risk_score: Mapped[str] = mapped_column(String(16), default="unknown")


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=_uid)
    order_id: Mapped[str] = mapped_column(String(12), ForeignKey("orders.id"), index=True)
    channel: Mapped[str] = mapped_column(String(16), default="onscreen")  # onscreen|email
    recipient: Mapped[str] = mapped_column(String(255), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)  # pending|sent|skipped
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
