"""roles + ciclo pending/active/paused/closed/rejected + indices.

Seguro para datos existentes: las rifas actuales quedan active (siguen vendiendo).
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_roles_aprobacion"
down_revision = "0003_notif_kind"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("organizers", sa.Column("role", sa.String(16), server_default="organizer"))
    op.create_index("ix_organizers_role", "organizers", ["role"])

    # existentes -> active (siguen vendiendo); nuevas -> pending por default
    op.execute("UPDATE raffles SET status = 'active' WHERE status IS NULL OR status NOT IN ('active','paused','closed')")
    with op.batch_alter_table("raffles") as batch_op:
        batch_op.alter_column("status", existing_type=sa.String(32),
                              server_default="pending", nullable=False)
    op.create_index("ix_raffles_status", "raffles", ["status"])

    op.add_column("raffles", sa.Column("rejection_reason", sa.Text(), server_default=""))
    op.add_column("raffles", sa.Column("publish_requested_at", sa.DateTime(), nullable=True))
    op.create_index("ix_orders_raffle_status", "orders", ["raffle_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_orders_raffle_status", table_name="orders")
    op.drop_column("raffles", "publish_requested_at")
    op.drop_column("raffles", "rejection_reason")
    op.drop_index("ix_raffles_status", table_name="raffles")
    op.alter_column("raffles", "status", existing_type=sa.String(32),
                    server_default=None, nullable=True)
    op.drop_index("ix_organizers_role", table_name="organizers")
    op.drop_column("organizers", "role")
