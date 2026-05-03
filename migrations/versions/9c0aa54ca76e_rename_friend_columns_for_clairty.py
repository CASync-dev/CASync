"""rename friend columns for clairty

Revision ID: 9c0aa54ca76e
Revises: 49014b0e002a
Create Date: 2026-05-03 14:48:49.298465

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '9c0aa54ca76e'
down_revision = '49014b0e002a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('friendships', schema=None) as batch_op:
        batch_op.alter_column('user_id', new_column_name='sender_id')
        batch_op.alter_column('friend_id', new_column_name='recipient_id')


def downgrade():
    with op.batch_alter_table('friendships', schema=None) as batch_op:
        batch_op.alter_column('sender_id', new_column_name='user_id')
        batch_op.alter_column('recipient_id', new_column_name='friend_id')
