from datetime import datetime

from pydantic import BaseModel, Field


class OrganizerRegister(BaseModel):
    email: str
    name: str = ""
    password: str = Field(min_length=6)


class OrganizerLogin(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RaffleCreate(BaseModel):
    title: str
    description: str = ""
    total_numbers: int = Field(default=100, ge=1, le=10000)
    price: float = Field(gt=0)
    prizes: str = ""
    draw_date: datetime | None = None
    cvu: str = ""
    alias: str = ""
    holder: str = ""


class RaffleOut(BaseModel):
    id: str
    title: str
    total_numbers: int
    price: float
    prizes: str
    status: str
    sold_count: int = 0
    reserved_count: int = 0

    class Config:
        from_attributes = True


class TicketOut(BaseModel):
    number: int
    status: str


class OrderCreate(BaseModel):
    raffle_id: str
    numbers: list[int] = Field(min_length=1, max_length=20)
    buyer_name: str = Field(min_length=2)
    buyer_email: str = ""
    buyer_phone: str = ""
    buyer_dni: str = ""
    origin_last4: str = ""


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
