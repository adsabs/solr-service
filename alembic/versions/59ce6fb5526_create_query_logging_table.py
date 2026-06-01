"""Create query logging table

Revision ID: 59ce6fb5526
Revises: 51f3b3b5cd5d
Create Date: 2026-05-22 15:22:17.468189

"""

# revision identifiers, used by Alembic.
revision = '59ce6fb5526'
down_revision = '51f3b3b5cd5d'

from alembic import op
import sqlalchemy as sa

import datetime

from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer, Index


def upgrade():
    op.create_table('query_log',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('query', sa.Text, nullable=False),
        sa.Column('allocated_bytes', sa.Integer, nullable=False),
        sa.Column('request_duration', sa.Interval, nullable=False)
    )

def downgrade():
    op.drop_table('query_log')
