from datetime import datetime

from pydantic import BaseModel, Field, field_serializer, field_validator
from pydantic_core import PydanticCustomError

EMAIL_RE = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"


def _check_email(v: str) -> str:
    import re

    v = (v or "").strip()
    if "\n" in v or "\r" in v or len(v) > 254:
        raise PydanticCustomError("email_invalido", "Email inválido")
    if not re.match(EMAIL_RE, v):
        raise PydanticCustomError("email_invalido", "Email inválido")
    return v


PASSWORD_SPECIAL = set("!@#$%^&*()-_=+")
PASSWORD_GUIDE = "Mín: 8 caracteres, 1 mayúscula, 1 minúscula, 1 número, 1 especial (!@#$%^&*()-_=+)"


def _check_password(v: str) -> str:
    v = v or ""
    if (
        len(v) < 8
        or not any(c.isupper() for c in v)
        or not any(c.islower() for c in v)
        or not any(c.isdigit() for c in v)
        or not any(c in PASSWORD_SPECIAL for c in v)
    ):
        raise PydanticCustomError("password_debil", "Contraseña débil. " + PASSWORD_GUIDE)
    return v


class OrganizerRegister(BaseModel):
    email: str
    name: str = ""
    password: str = Field(min_length=8)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return _check_email(v)

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        return _check_password(v)


class OrganizerLogin(BaseModel):
    email: str
    password: str


class PasswordChange(BaseModel):
    current: str
    new: str = Field(min_length=8)

    @field_validator("new")
    @classmethod
    def _new(cls, v: str) -> str:
        return _check_password(v)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RaffleCreate(BaseModel):
    title: str
    description: str = ""
    total_numbers: int = Field(default=100, ge=1, le=10000)
    price: float = Field(gt=0)
    prizes: str = ""
    draw_date: datetime
    cvu: str = ""
    alias: str = ""
    holder: str = ""


class RaffleOut(BaseModel):
    id: str
    title: str
    description: str = ""
    total_numbers: int
    price: float
    prizes: str
    status: str
    sold_count: int = 0
    reserved_count: int = 0
    requested: bool = False
    rejection_reason: str = ""
    draw_date: datetime | None = None

    @field_serializer("draw_date")
    def _ser_draw(self, v: datetime | None) -> str | None:
        from .dates import iso_z
        return iso_z(v)

    class Config:
        from_attributes = True


class TicketOut(BaseModel):
    number: int
    status: str


class OrderCreate(BaseModel):
    raffle_id: str
    numbers: list[int] = Field(min_length=1, max_length=20)
    buyer_name: str = Field(min_length=2)
    buyer_email: str
    buyer_phone: str = ""
    buyer_dni: str = ""
    origin_last4: str = ""

    @field_validator("buyer_email")
    @classmethod
    def _email(cls, v: str) -> str:
        return _check_email(v)


class OrderOut(BaseModel):
    id: str
    raffle_id: str
    numbers: list[int]
    amount: float
    status: str
    expires_at: datetime
    cvu: str = ""
    alias: str = ""
    holder: str = ""
    concept: str = ""

    class Config:
        from_attributes = True


class MockCreditIn(BaseModel):
    organizer_id: str
    amount: float


class PayoutUpdate(BaseModel):
    cvu: str | None = None
    alias: str | None = None
    holder: str | None = None


class RejectIn(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class RaffleAdminUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    price: float | None = Field(default=None, gt=0)
    total_numbers: int | None = Field(default=None, ge=1, le=10000)
    prizes: str | None = None
    draw_date: datetime | None = None
    cvu: str | None = None
    alias: str | None = None
    holder: str | None = None
    status: str | None = None
