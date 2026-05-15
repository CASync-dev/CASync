"""change time storage format to iso date time

start_time and end_time were stored as TIME plus a separate DATE column.
This rolls them into a single DATETIME(timezone=True) per side so events
can span multiple days. Existing event rows are wiped — the iCal feed
re-imports them and seeds re-run from scratch.

Revision ID: 0786cbeadab4
Revises: 0b46eac6b742
Create Date: 2026-05-14 23:24:15.298935

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0786cbeadab4'
down_revision = '0b46eac6b742'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite can't coerce TIME → DATETIME on existing rows, and the user opted
    # to wipe rather than backfill. Clear the table first.
    op.execute("DELETE FROM events")
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_column('date')
        batch_op.alter_column(
            'start_time',
            existing_type=sa.Time(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
        )
        batch_op.alter_column(
            'end_time',
            existing_type=sa.Time(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
        )


def downgrade():
    op.execute("DELETE FROM events")
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.alter_column(
            'end_time',
            existing_type=sa.DateTime(timezone=True),
            type_=sa.Time(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            'start_time',
            existing_type=sa.DateTime(timezone=True),
            type_=sa.Time(),
            existing_nullable=False,
        )
        batch_op.add_column(sa.Column('date', sa.DATE(), nullable=False))
