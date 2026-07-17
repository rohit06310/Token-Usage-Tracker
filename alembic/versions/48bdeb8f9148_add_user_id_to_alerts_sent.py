"""add user_id to alerts_sent

Revision ID: 48bdeb8f9148
Revises: 5b199b57852b
Create Date: 2026-07-13 09:48:23.928928+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48bdeb8f9148'
down_revision: Union[str, None] = '5b199b57852b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('TRUNCATE TABLE ai_alerts_sent CASCADE')
    op.add_column('ai_alerts_sent', sa.Column('user_id', sa.Uuid(), nullable=False))
    op.create_foreign_key('fk_alerts_sent_user_id', 'ai_alerts_sent', 'ai_users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_ai_alerts_sent_user_id', 'ai_alerts_sent', ['user_id'])


def downgrade() -> None:
    op.drop_constraint('fk_alerts_sent_user_id', 'ai_alerts_sent', type_='foreignkey')
    op.drop_index('ix_ai_alerts_sent_user_id', 'ai_alerts_sent')
    op.drop_column('ai_alerts_sent', 'user_id')
