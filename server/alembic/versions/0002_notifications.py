"""notifications table"""
from alembic import op
import sqlalchemy as sa

revision = "0002_notifications"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(12), primary_key=True),
        sa.Column("order_id", sa.String(12), index=True),
        sa.Column("channel", sa.String(16), server_default="onscreen"),
        sa.Column("recipient", sa.String(255), server_default=""),
        sa.Column("message", sa.Text(), server_default=""),
        sa.Column("status", sa.String(16), server_default="pending", index=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
    )


def downgrade() -> None:
    op.drop_table("notifications")
