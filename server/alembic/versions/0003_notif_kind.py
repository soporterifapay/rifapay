"""notification kind (expiry|receipt)"""
from alembic import op
import sqlalchemy as sa

revision = "0003_notif_kind"
down_revision = "0002_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("kind", sa.String(16), server_default="expiry"))
    op.create_index("ix_notifications_kind", "notifications", ["kind"])


def downgrade() -> None:
    op.drop_index("ix_notifications_kind", table_name="notifications")
    op.drop_column("notifications", "kind")
