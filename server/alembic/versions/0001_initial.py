"""initial tables"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizers",
        sa.Column("id", sa.String(12), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, index=True),
        sa.Column("name", sa.String(255), server_default=""),
        sa.Column("password_hash", sa.String(255)),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "mp_connections",
        sa.Column("id", sa.String(12), primary_key=True),
        sa.Column("organizer_id", sa.String(12), unique=True, index=True),
        sa.Column("mp_user_id", sa.String(64), server_default=""),
        sa.Column("access_token_enc", sa.Text(), server_default=""),
        sa.Column("refresh_token_enc", sa.Text(), server_default=""),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(32), server_default="disconnected"),
        sa.Column("cvu", sa.String(64), server_default=""),
        sa.Column("alias", sa.String(64), server_default=""),
        sa.Column("holder", sa.String(255), server_default=""),
        sa.ForeignKeyConstraint(["organizer_id"], ["organizers.id"]),
    )
    op.create_table(
        "raffles",
        sa.Column("id", sa.String(12), primary_key=True),
        sa.Column("organizer_id", sa.String(12), index=True),
        sa.Column("title", sa.String(255)),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("total_numbers", sa.Integer(), server_default="100"),
        sa.Column("price", sa.Float()),
        sa.Column("prizes", sa.Text(), server_default=""),
        sa.Column("draw_date", sa.DateTime(), nullable=True),
        sa.Column("cvu", sa.String(64), server_default=""),
        sa.Column("alias", sa.String(64), server_default=""),
        sa.Column("holder", sa.String(255), server_default=""),
        sa.Column("verification_mode", sa.String(32), server_default="auto_mp"),
        sa.Column("status", sa.String(32), server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["organizer_id"], ["organizers.id"]),
    )
    op.create_table(
        "orders",
        sa.Column("id", sa.String(12), primary_key=True),
        sa.Column("raffle_id", sa.String(12), index=True),
        sa.Column("organizer_id", sa.String(12), index=True),
        sa.Column("numbers_json", sa.Text(), server_default="[]"),
        sa.Column("amount", sa.Float(), index=True),
        sa.Column("buyer_name", sa.String(255)),
        sa.Column("buyer_email", sa.String(255), server_default=""),
        sa.Column("buyer_phone", sa.String(64), server_default=""),
        sa.Column("buyer_dni", sa.String(32), server_default=""),
        sa.Column("origin_last4", sa.String(8), server_default=""),
        sa.Column("status", sa.String(24), server_default="reserved", index=True),
        sa.Column("created_at", sa.DateTime(), index=True),
        sa.Column("expires_at", sa.DateTime()),
        sa.ForeignKeyConstraint(["raffle_id"], ["raffles.id"]),
        sa.ForeignKeyConstraint(["organizer_id"], ["organizers.id"]),
    )
    op.create_table(
        "tickets",
        sa.Column("id", sa.String(12), primary_key=True),
        sa.Column("raffle_id", sa.String(12), index=True),
        sa.Column("number", sa.Integer(), index=True),
        sa.Column("status", sa.String(16), server_default="available", index=True),
        sa.Column("order_id", sa.String(12), nullable=True),
        sa.ForeignKeyConstraint(["raffle_id"], ["raffles.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.UniqueConstraint("raffle_id", "number", name="uq_raffle_number"),
    )
    op.create_table(
        "movements_cache",
        sa.Column("mp_payment_id", sa.String(64), primary_key=True),
        sa.Column("organizer_id", sa.String(12), index=True),
        sa.Column("amount", sa.Float(), index=True),
        sa.Column("date_created", sa.DateTime(), index=True),
        sa.Column("raw_json", sa.Text(), server_default="{}"),
        sa.Column("used_by_order_id", sa.String(12), nullable=True, index=True),
    )
    op.create_table(
        "receipts",
        sa.Column("id", sa.String(12), primary_key=True),
        sa.Column("order_id", sa.String(12), index=True),
        sa.Column("sha256", sa.String(64), index=True),
        sa.Column("filename", sa.String(255), server_default=""),
        sa.Column("ocr_json", sa.Text(), server_default="{}"),
        sa.Column("risk_score", sa.String(16), server_default="unknown"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
    )


def downgrade() -> None:
    for t in ["receipts", "movements_cache", "tickets", "orders", "raffles", "mp_connections", "organizers"]:
        op.drop_table(t)
